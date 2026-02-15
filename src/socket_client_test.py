import asyncio
import socketio

sio = socketio.AsyncClient()

ROOM_ID = "4"  # keep your existing real room id

@sio.event
async def connect():
    print("Connected to server")
    await sio.emit("join_room", {"room_id": ROOM_ID})
    await sio.emit("chat_message", {"message": "Hello from Python client"})

@sio.on("system_message")
async def on_system_message(data):
    print("Received system_message:", data)

@sio.on("chat_message")
async def on_chat_message(data):
    print("Received chat_message:", data)

async def main():
    await sio.connect("http://localhost:8000")
    await asyncio.sleep(5)
    await sio.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

