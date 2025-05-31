# Import necessary libraries
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import fal_client
from typing import Dict, Any, Optional, List, Set
import os
import requests

# import io
# from elevenlabs import ElevenLabs
# from elevenlabs.client import ElevenLabs as ElevenLabsClient
import uuid
from datetime import datetime, timedelta
import certifi
import ssl

# Configure SSL context
# ssl_context = ssl.create_default_context(cafile=certifi.where())

# Initialize FastAPI application
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# export FAL_KEY=57726426-5347-43c5-a45a-b57a2474fc51:a4a5bb69ce0b9ff0e091d32a95e5d532

# Set up API keys and configuration
os.environ["FAL_KEY"] = (
    "57726426-5347-43c5-a45a-b57a2474fc51:a4a5bb69ce0b9ff0e091d32a95e5d532"
)
# ELEVENLABS_API_KEY = "sk_6048733473bdee5dc87d5f695a515374ecb7fbe4bf5bdfe7"
# ELEVENLABS_VOICE_ID = "czENV7XMod8QIdiYtyC4"
# ELEVENLABS_AGENT_ID = "agent_01jwk4yynnemwsf3vr3kj9da45"

# # Initialize ElevenLabs clients with SSL context
# elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY, ssl_context=ssl_context)
# elevenlabs_client = ElevenLabsClient(api_key=ELEVENLABS_API_KEY, ssl_context=ssl_context)


# Data models
class VideoRequest(BaseModel):
    prompt: str
    motion_bucket_id: int = 127
    cond_aug: float = 0.02
    steps: int = 20
    deep_cache: str = "none"
    fps: int = 10
    negative_prompt: str = "unrealistic, saturated, high contrast, big nose, painting, drawing, sketch, cartoon, anime, manga, render, CG, 3d, watermark, signature, label"
    video_size: str = "landscape_16_9"


class TextRequest(BaseModel):
    text: str


class ConversationRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None


class TransferRequest(BaseModel):
    target_id: str
    reason: str


class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    category: str
    description: Optional[str] = None
    preview_url: Optional[str] = None


class Session:
    def __init__(self, session_id: str, voice_id: Optional[str] = None):
        self.session_id = session_id
        self.voice_id = voice_id or ELEVENLABS_VOICE_ID
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.language = "en"
        self.conversation_history: List[Dict[str, Any]] = []

    def update_activity(self):
        self.last_activity = datetime.now()

    def add_to_history(self, message: str, is_user: bool):
        self.conversation_history.append(
            {
                "message": message,
                "is_user": is_user,
                "timestamp": datetime.now().isoformat(),
            }
        )


# Session storage
active_sessions: Dict[str, Session] = {}

# def get_or_create_session(session_id: Optional[str] = None, voice_id: Optional[str] = None) -> Session:
#     if session_id and session_id in active_sessions:
#         session = active_sessions[session_id]
#         session.update_activity()
#         return session

#     new_session_id = session_id or str(uuid.uuid4())
#     session = Session(new_session_id, voice_id)
#     active_sessions[new_session_id] = session
#     return session

# def cleanup_expired_sessions():
#     current_time = datetime.now()
#     expired_sessions = [
#         session_id for session_id, session in active_sessions.items()
#         if current_time - session.last_activity > timedelta(hours=1)
#     ]
#     for session_id in expired_sessions:
#         del active_sessions[session_id]

# class ConversationResponse(BaseModel):
#     text_response: str
#     session_id: str
#     language: str
#     audio_url: Optional[str] = None

# # Function to get all available voices
# def get_available_voices():
#     try:
#         response = elevenlabs_client.voices.get_all()
#         return [
#             VoiceInfo(
#                 voice_id=voice.voice_id,
#                 name=voice.name,
#                 category=voice.category,
#                 description=voice.description,
#                 preview_url=voice.preview_url
#             )
#             for voice in response.voices
#         ]
#     except Exception as e:
#         print(f"Error fetching voices: {str(e)}")
#         raise

# # Create the agent configuration
# conversation_config = {
#     "name": "Customer Support Agent",
#     "description": "A helpful customer support agent that can assist with various inquiries",
#     "voice_id": ELEVENLABS_VOICE_ID,
#     "model": "gpt-4",
#     "temperature": 0.7,
#     "max_tokens": 150,
#     "tools": [
#         {
#             "type": "system",
#             "name": "end_call",
#             "description": "End the call when the user says goodbye, thank you, or indicates they have no more questions.",
#             "params": {
#                 "conditions": [
#                     "user says goodbye",
#                     "user says thank you",
#                     "user indicates they have no more questions",
#                     "user wants to end the conversation"
#                 ]
#             }
#         },
#         {
#             "type": "system",
#             "name": "language_detection",
#             "description": "Detect and switch language based on user input or request.",
#             "params": {
#                 "supported_languages": ["en", "es"],
#                 "default_language": "en"
#             }
#         },
#         {
#             "type": "system",
#             "name": "transfer_to_agent",
#             "description": "Transfer the user to a specialized agent based on their request.",
#             "params": {
#                 "transfers": [
#                     {
#                         "agent_id": "billing_support",
#                         "condition": "When the user asks for billing support or payment related questions.",
#                         "description": "Billing Support Agent"
#                     },
#                     {
#                         "agent_id": "technical_support",
#                         "condition": "When the user requests advanced technical help or product troubleshooting.",
#                         "description": "Technical Support Agent"
#                     }
#                 ],
#                 "fallback_message": "I'll transfer you to a specialized agent who can better assist you with your request."
#             }
#         },
#         {
#             "type": "system",
#             "name": "transfer_to_human",
#             "description": "Transfer the user to a human operator based on their request.",
#             "params": {
#                 "transfers": [
#                     {
#                         "phone_number": "+447502387536",
#                         "condition": "When the user asks for billing support or payment disputes.",
#                         "description": "Billing Support Team"
#                     },
#                     {
#                         "phone_number": "+447502387536",
#                         "condition": "When the user requests to file a formal complaint or needs urgent assistance.",
#                         "description": "Customer Relations Team"
#                     }
#                 ],
#                 "fallback_message": "I'll connect you with a human operator who can assist you further."
#             }
#         },
#         {
#             "type": "system",
#             "name": "skip_turn",
#             "description": "Skip the current turn in the conversation when appropriate.",
#             "params": {
#                 "conditions": [
#                     "user is typing",
#                     "system processing delay",
#                     "temporary interruption"
#                 ]
#             }
#         }
#     ],
#     "first_message": "Hi, how can I help you today?",
#     "system_prompt": "You are a helpful customer support agent. Your goal is to assist users with their inquiries in a friendly and professional manner. You can handle general questions, provide information about products and services, and transfer users to specialized agents or human operators when necessary. Always maintain a professional tone and ensure user satisfaction.",
#     "language_presets": {
#         "en": {
#             "overrides": {
#                 "agent": {
#                     "first_message": "Hi, how can I help you today?",
#                     "system_prompt": "You are a helpful customer support agent. Your goal is to assist users with their inquiries in a friendly and professional manner. You can handle general questions, provide information about products and services, and transfer users to specialized agents or human operators when necessary."
#                 },
#                 "tts": {
#                     "voice_id": ELEVENLABS_VOICE_ID,
#                     "stability": 0.5,
#                     "similarity_boost": 0.85
#                 }
#             }
#         },
#         "es": {
#             "overrides": {
#                 "agent": {
#                     "first_message": "Hola, ¿cómo puedo ayudarte hoy?",
#                     "system_prompt": "Eres un agente de soporte al cliente servicial. Tu objetivo es ayudar a los usuarios con sus consultas de manera amigable y profesional. Puedes manejar preguntas generales, proporcionar información sobre productos y servicios, y transferir usuarios a agentes especializados u operadores humanos cuando sea necesario."
#                 },
#                 "tts": {
#                     "voice_id": ELEVENLABS_VOICE_ID,
#                     "stability": 0.5,
#                     "similarity_boost": 0.85
#                 }
#             }
#         }
#     },
#     "tts_settings": {
#         "voice_id": ELEVENLABS_VOICE_ID,
#         "stability": 0.5,
#         "similarity_boost": 0.85,
#         "style": 0.5,
#         "use_speaker_boost": True
#     },
#     "fallback_responses": [
#         "I apologize, but I'm having trouble understanding. Could you please rephrase that?",
#         "I'm not quite sure I follow. Could you provide more details?",
#         "I'm having difficulty processing your request. Could you try asking in a different way?"
#     ]
# }

# # Create the agent with error handling
# try:
#     agent = elevenlabs.conversational_ai.agents.create(
#         name="Customer Support Agent",
#         conversation_config=conversation_config
#     )
# except Exception as e:
#     print(f"Error creating agent: {str(e)}")
#     raise


# Function to handle video generation
async def generate_video(prompt: str, **kwargs) -> Dict[str, Any]:
    try:
        handler = await fal_client.submit_async(
            "fal-ai/fast-svd/text-to-video", arguments={"prompt": prompt, **kwargs}
        )

        async for event in handler.iter_events(with_logs=True):
            print(f"Progress: {event}")

        result = await handler.get()
        return result
    except Exception as e:
        print(f"Error generating video: {str(e)}")
        raise


# Function to transcribe audio
# def transcribe_audio(audio_bytes):
#     # TODO: Integrate your ASR model here (e.g., Whisper)
#     return "This is a placeholder transcription."

# # Function to process text with agent logic
# def agent_logic(text):
#     # TODO: Integrate your LLM or custom logic here
#     return f"Agent heard: {text}"

# # Function to convert text to speech
# def elevenlabs_tts(text, voice_id=None):
#     voice_id = voice_id or ELEVENLABS_VOICE_ID
#     url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
#     headers = {
#         "xi-api-key": ELEVENLABS_API_KEY,
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "text": text,
#         "voice_settings": {
#             "stability": 0.5,
#             "similarity_boost": 0.85
#         }
#     }
#     response = requests.post(url, headers=headers, json=payload)
#     return response.content


# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Video and Voice Generation API"}


# Get available voices endpoint
@app.get("/voices/", response_model=List[VoiceInfo])
async def get_voices():
    try:
        voices = get_available_voices()
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Video generation endpoint
@app.post("/generate-video")
async def create_video(request: VideoRequest):
    try:
        result = await generate_video(
            prompt=request.prompt,
            motion_bucket_id=request.motion_bucket_id,
            cond_aug=request.cond_aug,
            steps=request.steps,
            deep_cache=request.deep_cache,
            fps=request.fps,
            negative_prompt=request.negative_prompt,
            video_size=request.video_size,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# # Voice-to-voice endpoint
# @app.post("/voice-to-voice/")
# async def voice_to_voice(file: UploadFile = File(...), voice_id: Optional[str] = None):
#     try:
#         audio_content = await file.read()
#         transcribed_text = transcribe_audio(audio_content)
#         agent_response = agent_logic(transcribed_text)
#         tts_audio = elevenlabs_tts(agent_response, voice_id)
#         return StreamingResponse(io.BytesIO(tts_audio), media_type="audio/mpeg")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # Conversational agent endpoint
# @app.post("/conversation/")
# async def handle_conversation(request: ConversationRequest):
#     try:
#         # Process the message through the conversation agent
#         response = agent.send_message(request.message)

#         # Convert the response to speech using specified voice or default
#         tts_audio = elevenlabs_tts(response.text, request.voice_id)

#         # Return both the text response and audio
#         return {
#             "text_response": response.text,
#             "audio": StreamingResponse(io.BytesIO(tts_audio), media_type="audio/mpeg")
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # End call endpoint
# @app.post("/end-call/")
# async def end_call(session_id: str):
#     try:
#         agent.end_session(session_id)
#         return {"message": "Call ended successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # Transfer to agent endpoint
# @app.post("/transfer-to-agent/")
# async def transfer_to_agent(request: TransferRequest):
#     try:
#         agent.transfer_to_agent(
#             target_agent_id=request.target_id,
#             reason=request.reason
#         )
#         return {"message": f"Transferred to agent {request.target_id}"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # Transfer to human endpoint
# @app.post("/transfer-to-human/")
# async def transfer_to_human(phone_number: str):
#     try:
#         agent.transfer_to_human(phone_number)
#         return {"message": f"Transferred to human operator at {phone_number}"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# Skip turn endpoint
@app.post("/skip-turn/")
async def skip_turn(session_id: str):
    try:
        agent.skip_turn(session_id)
        return {"message": "Turn skipped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
