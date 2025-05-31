from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
import wave
import json
import asyncio
from pydantic import BaseModel
from typing import Optional
import uvicorn
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

app = FastAPI(title="ElevenLabs Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# ElevenLabs configuration
AGENT_ID = "agent_01jwk4yynnemwsf3vr3kj9da45"
API_KEY = "sk_6048733473bdee5dc87d5f695a515374ecb7fbe4bf5bdfe7"

# Initialize ElevenLabs client
client = ElevenLabs(api_key=API_KEY)

# Store active conversations
active_conversations = {}

class MessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class MessageResponse(BaseModel):
    response: str
    conversation_id: str

class AudioHandler:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False

    def start_recording(self):
        self.frames = []
        self.is_recording = True
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        return self.frames

    def save_audio(self, frames, filename="temp_recording.wav"):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return filename

audio_handler = AudioHandler()

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)
            
            if command["action"] == "start_recording":
                audio_handler.start_recording()
                await websocket.send_json({"status": "recording_started"})
                
            elif command["action"] == "stop_recording":
                frames = audio_handler.stop_recording()
                filename = audio_handler.save_audio(frames)
                
                # Initialize ElevenLabs client and conversation
                client = ElevenLabs(api_key=API_KEY)
                conversation = Conversation(
                    client,
                    AGENT_ID,
                    requires_auth=bool(API_KEY),
                    audio_interface=DefaultAudioInterface(),
                )
                
                # Process the audio file and get response
                # Note: You'll need to implement the actual audio processing logic here
                # This is a placeholder for the response
                response = {"status": "success", "message": "Audio processed", "filename": filename}
                await websocket.send_json(response)
                
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})
    finally:
        await websocket.close()

@app.get("/")
async def root():
    return {"message": "Audio API is running"}

@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    try:
        # If no conversation_id provided, create new conversation
        if not request.conversation_id:
            conversation = Conversation(
                client,
                AGENT_ID,
                requires_auth=bool(API_KEY),
                audio_interface=DefaultAudioInterface(),
            )
            conversation.start_session()
            conversation_id = conversation.get_session_id()
            active_conversations[conversation_id] = conversation
        else:
            # Get existing conversation
            conversation = active_conversations.get(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

        # Get response from agent
        response = conversation.send_message(request.message)
        
        return MessageResponse(
            response=response,
            conversation_id=conversation.get_session_id()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversation/{conversation_id}")
async def end_conversation(conversation_id: str):
    conversation = active_conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation.end_session()
    del active_conversations[conversation_id]
    return {"message": "Conversation ended successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 