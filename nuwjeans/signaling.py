import socketio

# 비동기 Socket.IO 서버 설정
sio = socketio.AsyncServer(async_mode='asgi')
sio_app = socketio.ASGIApp(sio)

# 이벤트 핸들러 설정
@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)

@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)

@sio.event
async def offer(sid, data):
    print('Offer received from:', sid)
    await sio.emit('offer', data, skip_sid=sid)

@sio.event
async def answer(sid, data):
    print('Answer received from:', sid)
    await sio.emit('answer', data, skip_sid=sid)

@sio.event
async def candidate(sid, data):
    print('Candidate received from:', sid)
    await sio.emit('candidate', data, skip_sid=sid)

@sio.event
async def hangup(sid):
    print('Hangup received from:', sid)
    await sio.emit('hangup', room=sid)
