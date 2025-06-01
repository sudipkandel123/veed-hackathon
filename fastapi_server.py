#!/usr/bin/env python3
"""
FastAPI Server for AI Video Generation Pipeline

This FastAPI application exposes all the numbered Python files (001, 002, 006, 0012, etc.)
as API endpoints, allowing you to trigger their functions via HTTP requests.

Each endpoint corresponds to a specific module in the video generation pipeline:
- Image to Video conversion
- Transcript processing and image downloading
- Text-to-speech and video processing
- Interactive AI conversations
- TikTok and YouTube upload

Usage:
    uvicorn fastapi_server:app --reload --host 0.0.0.0 --port 8000

API Documentation:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import traceback

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import our numbered modules
try:
    # Import 001 - User Video Generation
    import importlib.util

    spec_001_user = importlib.util.spec_from_file_location(
        "video_gen_user", "001_USER_generate_video_from_pictures.py"
    )
    video_gen_user = importlib.util.module_from_spec(spec_001_user)
    spec_001_user.loader.exec_module(video_gen_user)

    # Import 001 - AI Video Generation
    spec_001_ai = importlib.util.spec_from_file_location(
        "video_gen_ai", "001_AI_generate_video_from_pictures.py"
    )
    video_gen_ai = importlib.util.module_from_spec(spec_001_ai)
    spec_001_ai.loader.exec_module(video_gen_ai)

    # Import 002 - Transcript Image Downloader
    spec_002 = importlib.util.spec_from_file_location(
        "transcript_downloader", "02_download_image_from_transcript.py"
    )
    transcript_downloader = importlib.util.module_from_spec(spec_002)
    spec_002.loader.exec_module(transcript_downloader)

    # Import 006 - ElevenLabs Text-to-Voice
    spec_006 = importlib.util.spec_from_file_location(
        "elevenlabs_processor", "006_elevenlabs_text_to_voice.py"
    )
    elevenlabs_processor = importlib.util.module_from_spec(spec_006)
    spec_006.loader.exec_module(elevenlabs_processor)

    # Import 0012 - ElevenLabs Video Demo
    spec_0012 = importlib.util.spec_from_file_location(
        "elevenlabs_demo", "0012_elevenlabs_video_demo.py"
    )
    elevenlabs_demo = importlib.util.module_from_spec(spec_0012)
    spec_0012.loader.exec_module(elevenlabs_demo)

    # Import upload scripts
    spec_tiktok = importlib.util.spec_from_file_location(
        "tiktok_uploader", "z005_post_to_tiktok.py"
    )
    tiktok_uploader = importlib.util.module_from_spec(spec_tiktok)
    spec_tiktok.loader.exec_module(tiktok_uploader)

    spec_youtube = importlib.util.spec_from_file_location(
        "youtube_uploader", "z006_post_to_youtube.py"
    )
    youtube_uploader = importlib.util.module_from_spec(spec_youtube)
    spec_youtube.loader.exec_module(youtube_uploader)

except Exception as e:
    print(f"Error importing modules: {e}")
    print("Some endpoints may not be available.")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Video Generation Pipeline API",
    description="""
    ## 🎬 AI Video Generation Pipeline API
    
    This API provides endpoints for the complete AI video generation pipeline:
    
    ### 📹 **Video Generation**
    - `/generate-video-user` - Convert user images to videos
    - `/generate-video-ai` - Convert AI images to videos 
    
    ### 📝 **Content Processing**  
    - `/process-transcripts` - Download images from transcripts
    - `/create-storyline` - Create storylines from existing videos
    
    ### 🎙️ **Audio & Video Processing**
    - `/text-to-speech-pipeline` - Complete text-to-speech + video pipeline
    - `/elevenlabs-conversation` - Interactive AI conversation session
    
    ### 📤 **Social Media Upload**
    - `/upload-to-tiktok` - Post videos to TikTok
    - `/upload-to-youtube` - Post videos to YouTube
    
    ### 📊 **Status & Utilities**
    - `/status` - Check system status
    - `/list-files` - List generated files
    - `/download-file` - Download generated files
    
    All endpoints support background processing and provide detailed status updates.
    """,
    version="1.0.0",
    contact={
        "name": "AI Video Pipeline",
        "email": "support@aivideo.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class VideoGenerationRequest(BaseModel):
    """Request model for video generation"""

    image_dir: str = Field(
        default="./user_images", description="Directory containing images"
    )
    pattern: str = Field(default="*.jpg", description="File pattern to match")
    model: str = Field(
        default="fal-ai/veo2/image-to-video", description="AI model to use"
    )
    prompt: str = Field(
        default="Generate a natural motion video", description="Generation prompt"
    )
    max_concurrent: int = Field(default=3, description="Maximum concurrent processing")


class TranscriptProcessingRequest(BaseModel):
    """Request model for transcript processing"""

    transcripts_dir: str = Field(
        default="session_transcripts", description="Directory with transcript files"
    )


class StorylineRequest(BaseModel):
    """Request model for storyline creation"""

    videos_dir: str = Field(default="videos", description="Directory with video files")
    seconds_per_video: int = Field(default=5, description="Seconds per video segment")
    enhance_with_additional_images: bool = Field(
        default=True, description="Enhance with additional images"
    )


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech pipeline"""

    storyline_path: str = Field(
        default="stories/storyline.txt", description="Path to storyline file"
    )
    voice_id: Optional[str] = Field(None, description="Custom ElevenLabs voice ID")


class UploadRequest(BaseModel):
    """Request model for social media uploads"""

    video_path: Optional[str] = Field(
        None, description="Specific video path (auto-detect if None)"
    )
    title: Optional[str] = Field(None, description="Custom video title")
    description: Optional[str] = Field(None, description="Custom video description")
    privacy: str = Field(
        default="public", description="Privacy setting (public/private/unlisted)"
    )


class APIResponse(BaseModel):
    """Standard API response model"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Global task storage for background tasks
background_tasks_status = {}


def get_task_id() -> str:
    """Generate unique task ID"""
    return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint with API information"""
    return APIResponse(
        success=True,
        message="AI Video Generation Pipeline API is running",
        data={
            "version": "1.0.0",
            "endpoints": {
                "video_generation": ["/generate-video-user", "/generate-video-ai"],
                "content_processing": ["/process-transcripts", "/create-storyline"],
                "audio_video": ["/text-to-speech-pipeline", "/elevenlabs-conversation"],
                "social_upload": ["/upload-to-tiktok", "/upload-to-youtube"],
                "utilities": ["/status", "/list-files", "/download-file"],
            },
            "documentation": {"swagger": "/docs", "redoc": "/redoc"},
        },
    )


@app.get("/status", response_model=APIResponse)
async def get_status():
    """Get system status and running tasks"""
    try:
        # Check directory structure
        directories = {
            "user_images": os.path.exists("user_images"),
            "images": os.path.exists("images"),
            "videos": os.path.exists("videos"),
            "audio": os.path.exists("audio"),
            "output": os.path.exists("output"),
            "stories": os.path.exists("stories"),
            "session_transcripts": os.path.exists("session_transcripts"),
            "logs": os.path.exists("logs"),
        }

        # Check API keys
        api_keys = {
            "FAL_KEY": bool(os.environ.get("FAL_KEY")),
            "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
            "ELEVENLABS_API_KEY": bool(os.environ.get("ELEVENLABS_API_KEY")),
            "TIKTOK_ACCESS_TOKEN": bool(os.environ.get("TIKTOK_ACCESS_TOKEN")),
        }

        # Check running tasks
        active_tasks = {
            k: v
            for k, v in background_tasks_status.items()
            if v.get("status") == "running"
        }

        return APIResponse(
            success=True,
            message="System status retrieved",
            data={
                "directories": directories,
                "api_keys_configured": api_keys,
                "active_tasks": len(active_tasks),
                "task_details": active_tasks,
            },
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-video-user", response_model=APIResponse)
async def generate_video_user_endpoint(
    request: VideoGenerationRequest, background_tasks: BackgroundTasks
):
    """
    **Generate Videos from User Images**

    Converts user-uploaded images in the user_images directory to videos using AI models.
    This endpoint uses the `001_USER_generate_video_from_pictures.py` module.

    **Process:**
    1. Scans user_images directory for images matching the pattern
    2. Uploads images to FAL AI service
    3. Generates videos using specified model
    4. Downloads generated videos to videos/ directory

    **Requirements:**
    - FAL_KEY environment variable must be set
    - Images must be in user_images/ directory

    **Models Available:**
    - `fal-ai/veo2/image-to-video` (recommended)
    - `fal-ai/wan-i2v`
    - `fal-ai/minimax-video`
    - `fal-ai/luma-dream-machine`
    """
    task_id = get_task_id()

    try:
        # Validate API key
        if not os.environ.get("FAL_KEY"):
            raise HTTPException(
                status_code=400, detail="FAL_KEY environment variable not set"
            )

        # Start background task
        background_tasks_status[task_id] = {
            "status": "running",
            "message": "Starting user video generation",
            "start_time": datetime.now(),
            "request": request.dict(),
        }

        async def process_user_videos():
            try:
                # Initialize converter
                converter = video_gen_user.FalImageToVideo()

                # Process images
                results = await video_gen_user.process_user_images_parallel(
                    converter=converter,
                    image_dir=request.image_dir,
                    pattern=request.pattern,
                    model=request.model,
                    prompt=request.prompt,
                    max_concurrent=request.max_concurrent,
                )

                background_tasks_status[task_id].update(
                    {
                        "status": "completed",
                        "message": f"Generated {len(results)} videos",
                        "results": results,
                        "end_time": datetime.now(),
                    }
                )

            except Exception as e:
                background_tasks_status[task_id].update(
                    {
                        "status": "failed",
                        "message": f"Error: {str(e)}",
                        "error": str(e),
                        "end_time": datetime.now(),
                    }
                )
                logger.error(f"User video generation failed: {e}")

        background_tasks.add_task(process_user_videos)

        return APIResponse(
            success=True,
            message="User video generation started",
            data={
                "task_id": task_id,
                "status": "running",
                "check_status_url": f"/task-status/{task_id}",
            },
        )

    except Exception as e:
        logger.error(f"Error in generate_video_user_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-video-ai", response_model=APIResponse)
async def generate_video_ai_endpoint(
    request: VideoGenerationRequest, background_tasks: BackgroundTasks
):
    """
    **Generate Videos from AI Images**

    Converts AI-generated images in the images directory to videos using AI models.
    This endpoint uses the `001_AI_generate_video_from_pictures.py` module.

    **Process:**
    1. Scans images directory for images matching the pattern
    2. Uploads images to FAL AI service
    3. Generates videos using specified model
    4. Downloads generated videos to videos/ directory

    **Requirements:**
    - FAL_KEY environment variable must be set
    - Images must be in images/ directory
    """
    task_id = get_task_id()

    try:
        if not os.environ.get("FAL_KEY"):
            raise HTTPException(
                status_code=400, detail="FAL_KEY environment variable not set"
            )

        background_tasks_status[task_id] = {
            "status": "running",
            "message": "Starting AI video generation",
            "start_time": datetime.now(),
            "request": request.dict(),
        }

        async def process_ai_videos():
            try:
                converter = video_gen_ai.FalImageToVideo()

                results = await video_gen_ai.process_images_parallel(
                    converter=converter,
                    image_dir=request.image_dir.replace("user_images", "images"),
                    pattern=request.pattern,
                    model=request.model,
                    prompt=request.prompt,
                    max_concurrent=request.max_concurrent,
                )

                background_tasks_status[task_id].update(
                    {
                        "status": "completed",
                        "message": f"Generated {len(results)} videos",
                        "results": results,
                        "end_time": datetime.now(),
                    }
                )

            except Exception as e:
                background_tasks_status[task_id].update(
                    {
                        "status": "failed",
                        "message": f"Error: {str(e)}",
                        "error": str(e),
                        "end_time": datetime.now(),
                    }
                )
                logger.error(f"AI video generation failed: {e}")

        background_tasks.add_task(process_ai_videos)

        return APIResponse(
            success=True,
            message="AI video generation started",
            data={
                "task_id": task_id,
                "status": "running",
                "check_status_url": f"/task-status/{task_id}",
            },
        )

    except Exception as e:
        logger.error(f"Error in generate_video_ai_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-transcripts", response_model=APIResponse)
async def process_transcripts_endpoint(
    request: TranscriptProcessingRequest, background_tasks: BackgroundTasks
):
    """
    **Process Transcripts and Download Images**

    Processes transcript files and downloads relevant images based on content analysis.
    This endpoint uses the `02_download_image_from_transcript.py` module.

    **Process:**
    1. Reads transcript files from session_transcripts directory
    2. Uses ChatGPT to extract image concepts from transcripts
    3. Searches Google Images for relevant images
    4. Downloads and saves images to images/ directory

    **Requirements:**
    - OPENAI_API_KEY environment variable must be set
    - Transcript files must be in session_transcripts/ directory
    """
    task_id = get_task_id()

    try:
        if not os.environ.get("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=400, detail="OPENAI_API_KEY environment variable not set"
            )

        background_tasks_status[task_id] = {
            "status": "running",
            "message": "Starting transcript processing",
            "start_time": datetime.now(),
            "request": request.dict(),
        }

        async def process_transcripts():
            try:
                downloader = transcript_downloader.TranscriptImageDownloader()

                results = await downloader.process_all_transcripts(
                    transcripts_dir=request.transcripts_dir
                )

                # Save processing log
                log_path = downloader.save_processing_log(results)

                background_tasks_status[task_id].update(
                    {
                        "status": "completed",
                        "message": f"Processed {len(results)} transcripts",
                        "results": results,
                        "log_path": log_path,
                        "end_time": datetime.now(),
                    }
                )

            except Exception as e:
                background_tasks_status[task_id].update(
                    {
                        "status": "failed",
                        "message": f"Error: {str(e)}",
                        "error": str(e),
                        "end_time": datetime.now(),
                    }
                )
                logger.error(f"Transcript processing failed: {e}")

        background_tasks.add_task(process_transcripts)

        return APIResponse(
            success=True,
            message="Transcript processing started",
            data={
                "task_id": task_id,
                "status": "running",
                "check_status_url": f"/task-status/{task_id}",
            },
        )

    except Exception as e:
        logger.error(f"Error in process_transcripts_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-storyline", response_model=APIResponse)
async def create_storyline_endpoint(
    request: StorylineRequest, background_tasks: BackgroundTasks
):
    """
    **Create Storyline from Existing Videos**

    Analyzes existing videos and creates a cohesive storyline with voiceover script.
    This endpoint uses the storyline creation function from `02_download_image_from_transcript.py`.

    **Process:**
    1. Analyzes video files in the videos directory
    2. Extracts concepts and themes from existing images
    3. Uses ChatGPT to create a cohesive storyline
    4. Optionally downloads additional images to enhance the story
    5. Saves storyline to stories/storyline.txt

    **Requirements:**
    - OPENAI_API_KEY environment variable must be set
    - Video files must be in videos/ directory
    """
    task_id = get_task_id()

    try:
        if not os.environ.get("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=400, detail="OPENAI_API_KEY environment variable not set"
            )

        background_tasks_status[task_id] = {
            "status": "running",
            "message": "Starting storyline creation",
            "start_time": datetime.now(),
            "request": request.dict(),
        }

        async def create_storyline():
            try:
                downloader = transcript_downloader.TranscriptImageDownloader()

                result = await downloader.create_story_from_videos(
                    videos_dir=request.videos_dir,
                    seconds_per_video=request.seconds_per_video,
                    enhance_with_additional_images=request.enhance_with_additional_images,
                )

                background_tasks_status[task_id].update(
                    {
                        "status": "completed",
                        "message": "Storyline created successfully",
                        "result": result,
                        "end_time": datetime.now(),
                    }
                )

            except Exception as e:
                background_tasks_status[task_id].update(
                    {
                        "status": "failed",
                        "message": f"Error: {str(e)}",
                        "error": str(e),
                        "end_time": datetime.now(),
                    }
                )
                logger.error(f"Storyline creation failed: {e}")

        background_tasks.add_task(create_storyline)

        return APIResponse(
            success=True,
            message="Storyline creation started",
            data={
                "task_id": task_id,
                "status": "running",
                "check_status_url": f"/task-status/{task_id}",
            },
        )

    except Exception as e:
        logger.error(f"Error in create_storyline_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/text-to-speech-pipeline", response_model=APIResponse)
async def text_to_speech_pipeline_endpoint(
    request: TextToSpeechRequest, background_tasks: BackgroundTasks
):
    """
    **Complete Text-to-Speech and Video Pipeline**

    Runs the complete pipeline: reads storyline, converts to speech, merges videos, and combines.
    This endpoint uses the `006_elevenlabs_text_to_voice.py` module.

    **Process:**
    1. Reads storyline from stories/storyline.txt
    2. Converts text to speech using ElevenLabs API
    3. Merges all videos from videos/ directory
    4. Combines audio and video into final output
    5. Saves final video to output/ directory

    **Requirements:**
    - ELEVENLABS_API_KEY environment variable must be set
    - Storyline file must exist (created by /create-storyline)
    - Video files must exist in videos/ directory
    - FFmpeg must be installed
    """
    task_id = get_task_id()

    try:
        if not os.environ.get("ELEVENLABS_API_KEY"):
            raise HTTPException(
                status_code=400,
                detail="ELEVENLABS_API_KEY environment variable not set",
            )

        background_tasks_status[task_id] = {
            "status": "running",
            "message": "Starting text-to-speech pipeline",
            "start_time": datetime.now(),
            "request": request.dict(),
        }

        async def run_tts_pipeline():
            try:
                processor = elevenlabs_processor.ElevenLabsVideoProcessor()

                # Run complete pipeline
                final_output = processor.process_full_pipeline(
                    storyline_path=request.storyline_path, voice_id=request.voice_id
                )

                # Get file info
                file_size = os.path.getsize(final_output) / (1024 * 1024)  # MB

                background_tasks_status[task_id].update(
                    {
                        "status": "completed",
                        "message": "Text-to-speech pipeline completed",
                        "final_output": final_output,
                        "file_size_mb": round(file_size, 1),
                        "end_time": datetime.now(),
                    }
                )

            except Exception as e:
                background_tasks_status[task_id].update(
                    {
                        "status": "failed",
                        "message": f"Error: {str(e)}",
                        "error": str(e),
                        "end_time": datetime.now(),
                    }
                )
                logger.error(f"Text-to-speech pipeline failed: {e}")

        background_tasks.add_task(run_tts_pipeline)

        return APIResponse(
            success=True,
            message="Text-to-speech pipeline started",
            data={
                "task_id": task_id,
                "status": "running",
                "check_status_url": f"/task-status/{task_id}",
            },
        )

    except Exception as e:
        logger.error(f"Error in text_to_speech_pipeline_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-to-tiktok", response_model=APIResponse)
async def upload_to_tiktok_endpoint(
    request: UploadRequest, background_tasks: BackgroundTasks
):
    """
    **Upload Video to TikTok**

    Uploads the latest final_video to TikTok using TikTok Business API.
    This endpoint uses the `z005_post_to_tiktok.py` module.

    **Process:**
    1. Finds latest video starting with 'final_video' in output/ directory
    2. Uploads to TikTok using Business API
    3. Sets metadata (title, description, tags)
    4. Publishes video with specified privacy settings

    **Requirements:**
    - TikTok API credentials in .env file:
      - TIKTOK_CLIENT_KEY
      - TIKTOK_CLIENT_SECRET
      - TIKTOK_ACCESS_TOKEN
    - Final video must exist in output/ directory
    """
    task_id = get_task_id()

    try:
        background_tasks_status[task_id] = {
            "status": "running",
            "message": "Starting TikTok upload",
            "start_time": datetime.now(),
            "request": request.dict(),
        }

        async def upload_to_tiktok():
            try:
                uploader = tiktok_uploader.TikTokUploader()

                result = uploader.upload_and_post(video_path=request.video_path)

                background_tasks_status[task_id].update(
                    {
                        "status": "completed" if result["success"] else "failed",
                        "message": result.get("message", "Upload completed"),
                        "result": result,
                        "end_time": datetime.now(),
                    }
                )

            except Exception as e:
                background_tasks_status[task_id].update(
                    {
                        "status": "failed",
                        "message": f"Error: {str(e)}",
                        "error": str(e),
                        "end_time": datetime.now(),
                    }
                )
                logger.error(f"TikTok upload failed: {e}")

        background_tasks.add_task(upload_to_tiktok)

        return APIResponse(
            success=True,
            message="TikTok upload started",
            data={
                "task_id": task_id,
                "status": "running",
                "check_status_url": f"/task-status/{task_id}",
            },
        )

    except Exception as e:
        logger.error(f"Error in upload_to_tiktok_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-to-youtube", response_model=APIResponse)
async def upload_to_youtube_endpoint(
    request: UploadRequest, background_tasks: BackgroundTasks
):
    """
    **Upload Video to YouTube**

    Uploads the latest final_video to YouTube using YouTube Data API v3.
    This endpoint uses the `z006_post_to_youtube.py` module.

    **Process:**
    1. Finds latest video starting with 'final_video' in output/ directory
    2. Authenticates with YouTube via OAuth 2.0
    3. Uploads video with resumable upload
    4. Sets metadata and publishes with specified privacy

    **Requirements:**
    - Google Cloud Project with YouTube Data API v3 enabled
    - OAuth 2.0 credentials (client_secrets.json)
    - YouTube channel
    - Final video must exist in output/ directory
    """
    task_id = get_task_id()

    try:
        background_tasks_status[task_id] = {
            "status": "running",
            "message": "Starting YouTube upload",
            "start_time": datetime.now(),
            "request": request.dict(),
        }

        async def upload_to_youtube():
            try:
                uploader = youtube_uploader.YouTubeUploader()

                result = uploader.upload_and_post(
                    video_path=request.video_path,
                    title=request.title,
                    description=request.description,
                    privacy=request.privacy,
                )

                background_tasks_status[task_id].update(
                    {
                        "status": "completed" if result["success"] else "failed",
                        "message": result.get("message", "Upload completed"),
                        "result": result,
                        "end_time": datetime.now(),
                    }
                )

            except Exception as e:
                background_tasks_status[task_id].update(
                    {
                        "status": "failed",
                        "message": f"Error: {str(e)}",
                        "error": str(e),
                        "end_time": datetime.now(),
                    }
                )
                logger.error(f"YouTube upload failed: {e}")

        background_tasks.add_task(upload_to_youtube)

        return APIResponse(
            success=True,
            message="YouTube upload started",
            data={
                "task_id": task_id,
                "status": "running",
                "check_status_url": f"/task-status/{task_id}",
            },
        )

    except Exception as e:
        logger.error(f"Error in upload_to_youtube_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/task-status/{task_id}", response_model=APIResponse)
async def get_task_status(task_id: str):
    """Get status of a background task"""
    if task_id not in background_tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")

    task_info = background_tasks_status[task_id]
    return APIResponse(
        success=True, message=f"Task {task_id} status retrieved", data=task_info
    )


@app.get("/list-files", response_model=APIResponse)
async def list_files():
    """List generated files in all output directories"""
    try:
        files = {}
        directories = ["output", "videos", "audio", "images", "stories", "logs"]

        for directory in directories:
            if os.path.exists(directory):
                files[directory] = []
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path):
                        stat = os.stat(file_path)
                        files[directory].append(
                            {
                                "filename": file,
                                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                                "modified": datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                            }
                        )

        return APIResponse(
            success=True, message="Files listed successfully", data={"files": files}
        )

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-file/{directory}/{filename}")
async def download_file(directory: str, filename: str):
    """Download a specific file"""
    try:
        file_path = os.path.join(directory, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=file_path, filename=filename, media_type="application/octet-stream"
        )

    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting AI Video Generation Pipeline API...")
    print("📖 Documentation available at: http://localhost:8000/docs")
    print("🔗 Alternative docs at: http://localhost:8000/redoc")

    uvicorn.run(
        "fastapi_server:app", host="0.0.0.0", port=8002, reload=True, log_level="info"
    )
