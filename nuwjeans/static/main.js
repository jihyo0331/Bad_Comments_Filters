const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const transcriptDiv = document.getElementById('transcript');
let mediaRecorder;
let audioChunks = [];
let socket;

const forbiddenWords = ["씨발", "시발", "개새끼", "씨발새끼", "fuck", "새끼", "새기", "병신", "shit", "Fuck", "Kiss my ass", "ass",  "Get away", "Fuck off", "shut up", "you suck", "씨발", "느금마", "느금", "좆", "좆까", "지랄", "염병", "좃까", "족까", "졷까", "시발", "쪽바리", "어미", "에미", "Fucking", "fucking", "Fuck ing", "fuck ing","ing", "바보"]; // 필터링할 단어 목록

function filterText(text) {
    forbiddenWords.forEach(word => {
        text = text.replace(new RegExp(word, "gi"), ""); // 단어 필터링
    });
    return text;
}

function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ko-KR';
    window.speechSynthesis.speak(utterance);
}

startButton.onclick = () => {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            startButton.disabled = true;
            stopButton.disabled = false;

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('file', audioBlob, 'audio.wav');

                fetch('/upload-audio', {
                    method: 'POST',
                    body: formData
                });

                audioChunks = [];
                startButton.disabled = false;
                stopButton.disabled = true;
            };
        });
};

stopButton.onclick = () => {
    mediaRecorder.stop();
};

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//${window.location.host}/ws`;
    socket = new WebSocket(socketUrl);

    socket.onmessage = function(event) {
        const filteredText = event.data;
        transcriptDiv.textContent = filteredText;
        speakText(filteredText);
    };

    socket.onclose = function(event) {
        console.log('WebSocket is closed. Reconnect will be attempted in 1 second.', event.reason);
        setTimeout(function() {
            connectWebSocket();
        }, 1000);
    };

    socket.onerror = function(err) {
        console.error('WebSocket encountered error: ', err.message, 'Closing socket');
        socket.close();
    };
}

connectWebSocket();
