from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket, WebSocketDisconnect
import speech_recognition as sr
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import os
import tempfile
import subprocess
from typing import List

app = FastAPI()

# Static files 제공 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

# BERT 모델 로드
model_name = "unitary/toxic-bert"
model = BertForSequenceClassification.from_pretrained(model_name)
tokenizer = BertTokenizer.from_pretrained(model_name)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

def filter_text(text):
    forbidden_words = ["씨발", "시발", "개새끼", "씨발새끼", "fuck", "새끼", "새기", "병신", "shit", "Fuck", "Kiss my ass", "ass",  "Get away", "Fuck off", "shut up", "you suck", "씨발", "느금마", "느금", "좆", "좆까", "지랄", "염병", "좃까", "족까", "졷까", "시발", "쪽바리", "어미", "에미", "Fucking", "fucking", "Fuck ing", "fuck ing", "ing", "바보"]
    for word in forbidden_words:
        text = text.replace(word, "")
    return text

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        tmp_wav_path = tmp_wav.name

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # ffmpeg를 사용하여 오디오 파일을 PCM WAV 형식으로 변환
        subprocess.run(["ffmpeg", "-i", tmp_path, tmp_wav_path], check=True)

        with sr.AudioFile(tmp_wav_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language="ko-KR")
        filtered_text = filter_text(text)

        # 모든 클라이언트에 필터링된 텍스트를 브로드캐스트
        await manager.broadcast(filtered_text)
    except Exception as e:
        print(f"Error processing file: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        os.remove(tmp_path)
        os.remove(tmp_wav_path)

    return JSONResponse(content={"filtered_text": filtered_text})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def get():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)