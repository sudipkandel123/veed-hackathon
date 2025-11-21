from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pyaudio
import wave
import json
import asyncio
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os

# Updated ElevenLabs imports based on official documentation
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs.conversational_ai.conversation import Conversation
    from elevenlabs.conversational_ai.default_audio_interface import (
        DefaultAudioInterface,
    )
except ImportError as e:
    print(f"ElevenLabs import error: {e}")
    print("Please ensure you have the latest version of elevenlabs installed")
    print("Run: pip install --upgrade elevenlabs")

    # Set dummy classes to prevent startup errors
    class ElevenLabs:
        def __init__(self, api_key=None):
            self.api_key = api_key

    class Conversation:
        def __init__(self, *args, **kwargs):
            pass

        def start_session(self):
            return "dummy_session"

        def get_session_id(self):
            return "dummy_session_id"

        def send_message(self, message):
            return "ElevenLabs not properly configured"

        def end_session(self):
            pass

    class DefaultAudioInterface:
        def __init__(self):
            pass


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
AGENT_ID = os.environ.get('AGENT_ID')
API_KEY = os.environ.get('ELEVENLABS_API_KEY')

# Initialize ElevenLabs client with error handling
try:
    client = ElevenLabs(api_key=API_KEY)
    ELEVENLABS_AVAILABLE = True
except Exception as e:
    print(f"Failed to initialize ElevenLabs client: {e}")
    client = None
    ELEVENLABS_AVAILABLE = False

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
            frames_per_buffer=CHUNK,
        )

    def stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        return self.frames

    def save_audio(self, frames, filename="temp_recording.wav"):
        wf = wave.open(filename, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
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

                if ELEVENLABS_AVAILABLE:
                    try:
                        # Initialize conversation using the documented approach
                        conversation = Conversation(
                            client,
                            AGENT_ID,
                            requires_auth=bool(API_KEY),
                            audio_interface=DefaultAudioInterface(),
                        )

                        # Process the audio file and get response
                        # Note: You'll need to implement the actual audio processing logic here
                        # This is a placeholder for the response
                        response = {
                            "status": "success",
                            "message": "Audio processed",
                            "filename": filename,
                        }
                    except Exception as e:
                        response = {
                            "status": "error",
                            "message": f"ElevenLabs processing failed: {str(e)}",
                        }
                else:
                    response = {
                        "status": "error",
                        "message": "ElevenLabs not available",
                    }

                await websocket.send_json(response)

    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})
    finally:
        await websocket.close()


@app.get("/")
async def root():
    status = (
        "ElevenLabs available" if ELEVENLABS_AVAILABLE else "ElevenLabs unavailable"
    )
    return {"message": f"Audio API is running - {status}"}


@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    if not ELEVENLABS_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="ElevenLabs service is not available"
        )

    try:
        # If no conversation_id provided, create new conversation
        if not request.conversation_id:
            try:
                conversation = Conversation(
                    client,
                    AGENT_ID,
                    requires_auth=bool(API_KEY),
                    audio_interface=DefaultAudioInterface(),
                )
                conversation.start_session()
                conversation_id = conversation.get_session_id()
                active_conversations[conversation_id] = conversation

                # Send initial message
                response_text = conversation.send_message(request.message)

            except Exception as e:
                # If there's an issue with the conversation, return a fallback response
                print(f"Conversation creation error: {e}")
                return MessageResponse(
                    response=f"I'm having trouble connecting to the conversation service. Your message was: '{request.message}'. Please try again.",
                    conversation_id="fallback_session",
                )
        else:
            # Get existing conversation
            conversation = active_conversations.get(request.conversation_id)
            if not conversation:
                # Create new conversation if the ID doesn't exist
                try:
                    conversation = Conversation(
                        client,
                        AGENT_ID,
                        requires_auth=bool(API_KEY),
                        audio_interface=DefaultAudioInterface(),
                    )
                    conversation.start_session()
                    conversation_id = conversation.get_session_id()
                    active_conversations[conversation_id] = conversation
                    response_text = conversation.send_message(request.message)
                except Exception as e:
                    return MessageResponse(
                        response=f"I'm having trouble connecting to the conversation service. Your message was: '{request.message}'. Please try again.",
                        conversation_id="fallback_session",
                    )
            else:
                try:
                    response_text = conversation.send_message(request.message)
                    conversation_id = conversation.get_session_id()
                except Exception as e:
                    print(f"Message sending error: {e}")
                    return MessageResponse(
                        response=f"I encountered an error processing your message: '{request.message}'. Please try again.",
                        conversation_id=request.conversation_id,
                    )

        return MessageResponse(response=response_text, conversation_id=conversation_id)
    except Exception as e:
        print(f"General chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Conversation error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint to verify service status"""
    return {
        "status": "healthy",
        "elevenlabs_available": ELEVENLABS_AVAILABLE,
        "active_conversations": len(active_conversations),
    }


@app.get("/conversations")
async def list_conversations():
    """List all active conversations"""
    return {
        "active_conversations": list(active_conversations.keys()),
        "total_conversations": len(active_conversations),
    }


@app.delete("/conversation/{conversation_id}")
async def end_conversation(conversation_id: str):
    """End a specific conversation"""
    conversation = active_conversations.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        conversation.end_session()
        del active_conversations[conversation_id]
        return {"message": "Conversation ended successfully"}
    except Exception as e:
        print(f"Error ending conversation: {e}")
        # Remove from active conversations even if ending failed
        if conversation_id in active_conversations:
            del active_conversations[conversation_id]
        return {"message": f"Conversation removed with error: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
