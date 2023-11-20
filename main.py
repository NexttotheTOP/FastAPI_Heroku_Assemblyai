from fastapi import FastAPI
import pyaudio
from fastapi.websockets import WebSocket
import websockets
import asyncio
import json

app = FastAPI()

# PyAudio Configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
FRAMES_PER_BUFFER = 3200
p = pyaudio.PyAudio()

# Function to connect to AssemblyAI and handle audio streaming
async def connect_to_assemblyai(websocket: WebSocket, audio_stream):
    assemblyai_url = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"
    auth_key = "04053935c43f4a479c70fd62b353a528"  # Replace with your AssemblyAI API key

    async with websockets.connect(assemblyai_url, extra_headers={"Authorization": auth_key}) as assemblyai_ws:
        await websocket.accept()
        try:
            while True:
                # Read data from the PyAudio stream
                data = audio_stream.read(FRAMES_PER_BUFFER)
                # Send this data to AssemblyAI
                await assemblyai_ws.send(data)
                # Wait for transcription result from AssemblyAI
                result_str = await assemblyai_ws.recv()
                result = json.loads(result_str)
                # Send the transcription result back to the client (Retool app)
                await websocket.send_json(result)
        except Exception as e:
            print("Error:", e)
        finally:
            await websocket.close()

# FastAPI WebSocket endpoint
@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=FRAMES_PER_BUFFER)
    await connect_to_assemblyai(websocket, stream)
