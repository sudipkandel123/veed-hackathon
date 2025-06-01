# 🚀 AI Video Generation Pipeline API Guide

This guide explains how to use the FastAPI server that exposes all the numbered Python files as RESTful API endpoints.

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📊 API Overview](#-api-overview)
- [🔧 Setup &amp; Installation](#-setup--installation)
- [🎯 API Endpoints](#-api-endpoints)
- [📝 Usage Examples](#-usage-examples)
- [🔄 Workflow](#-workflow)
- [🛠️ Troubleshooting](#️-troubleshooting)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required for different endpoints
export FAL_KEY="your_fal_api_key"
export OPENAI_API_KEY="your_openai_key"
export ELEVENLABS_API_KEY="your_elevenlabs_key"

# Optional for social media uploads
export TIKTOK_CLIENT_KEY="your_tiktok_client_key"
export TIKTOK_CLIENT_SECRET="your_tiktok_secret"
export TIKTOK_ACCESS_TOKEN="your_tiktok_token"
```

### 3. Start the Server

```bash
# Option 1: Direct run
python fastapi_server.py

# Option 2: Using uvicorn
uvicorn fastapi_server:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📊 API Overview

The FastAPI server imports and exposes these numbered files as endpoints:

| Module         | File                                         | Endpoint                     | Description                      |
| -------------- | -------------------------------------------- | ---------------------------- | -------------------------------- |
| **001**  | `001_USER_generate_video_from_pictures.py` | `/generate-video-user`     | Convert user images to videos    |
| **001**  | `001_AI_generate_video_from_pictures.py`   | `/generate-video-ai`       | Convert AI images to videos      |
| **002**  | `02_download_image_from_transcript.py`     | `/process-transcripts`     | Download images from transcripts |
| **002**  | `02_download_image_from_transcript.py`     | `/create-storyline`        | Create storylines from videos    |
| **006**  | `006_elevenlabs_text_to_voice.py`          | `/text-to-speech-pipeline` | Complete TTS + video pipeline    |
| **z005** | `z005_post_to_tiktok.py`                   | `/upload-to-tiktok`        | Upload videos to TikTok          |
| **z006** | `z006_post_to_youtube.py`                  | `/upload-to-youtube`       | Upload videos to YouTube         |

## 🔧 Setup & Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** (for video processing)
3. **API Keys** for various services

### Directory Structure

Ensure your project has these directories:

```
your-project/
├── fastapi_server.py           # Main API server
├── 001_USER_generate_video_from_pictures.py
├── 001_AI_generate_video_from_pictures.py
├── 02_download_image_from_transcript.py
├── 006_elevenlabs_text_to_voice.py
├── z005_post_to_tiktok.py
├── z006_post_to_youtube.py
├── requirements.txt
├── .env                        # API keys (create this)
├── user_images/               # User uploaded images
├── images/                    # AI generated images
├── videos/                    # Generated videos
├── audio/                     # Audio files
├── output/                    # Final videos
├── stories/                   # Storyline files
├── session_transcripts/       # Transcript files
└── logs/                      # Log files
```

### Environment Variables

Create a `.env` file:

```env
# Required for video generation
FAL_KEY=your_fal_api_key_here

# Required for transcript processing and storyline creation
OPENAI_API_KEY=your_openai_key_here

# Required for text-to-speech
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Optional: TikTok upload
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_token

# Optional: YouTube upload (use OAuth flow instead)
GOOGLE_CLIENT_SECRETS_PATH=client_secrets.json
```

## 🎯 API Endpoints

### 🏠 System Endpoints

#### `GET /` - Root Information

```json
{
  "success": true,
  "message": "AI Video Generation Pipeline API is running",
  "data": {
    "version": "1.0.0",
    "endpoints": { ... },
    "documentation": {
      "swagger": "/docs",
      "redoc": "/redoc"
    }
  }
}
```

#### `GET /status` - System Status

Returns system status, directory existence, API key configuration, and active tasks.

#### `GET /health` - Health Check

Simple health check endpoint.

### 📹 Video Generation Endpoints

#### `POST /generate-video-user` - User Video Generation

**Description**: Converts user-uploaded images to videos using FAL AI.

**Request Body**:

```json
{
  "image_dir": "./user_images",
  "pattern": "*.jpg",
  "model": "fal-ai/veo2/image-to-video",
  "prompt": "Generate a natural motion video",
  "max_concurrent": 3
}
```

**Response**:

```json
{
  "success": true,
  "message": "User video generation started",
  "data": {
    "task_id": "task_20241201_143022_123456",
    "status": "running",
    "check_status_url": "/task-status/task_20241201_143022_123456"
  }
}
```

#### `POST /generate-video-ai` - AI Video Generation

**Description**: Converts AI-generated images to videos.

**Request Body**: Same as user video generation

**Process**:

1. Scans `images/` directory for images
2. Uploads to FAL AI service
3. Generates videos using specified model
4. Downloads videos to `videos/` directory

### 📝 Content Processing Endpoints

#### `POST /process-transcripts` - Process Transcripts

**Description**: Downloads images based on transcript content analysis.

**Request Body**:

```json
{
  "transcripts_dir": "session_transcripts"
}
```

**Process**:

1. Reads transcript files from `session_transcripts/`
2. Uses ChatGPT to extract image concepts
3. Searches Google Images
4. Downloads images to `images/` directory

#### `POST /create-storyline` - Create Storyline

**Description**: Creates storylines from existing videos.

**Request Body**:

```json
{
  "videos_dir": "videos",
  "seconds_per_video": 5,
  "enhance_with_additional_images": true
}
```

**Process**:

1. Analyzes video files in `videos/` directory
2. Extracts concepts from existing images
3. Uses ChatGPT to create cohesive storyline
4. Optionally downloads additional images
5. Saves storyline to `stories/storyline.txt`

### 🎙️ Audio & Video Processing Endpoints

#### `POST /text-to-speech-pipeline` - Complete TTS Pipeline

**Description**: Runs complete text-to-speech and video processing pipeline.

**Request Body**:

```json
{
  "storyline_path": "stories/storyline.txt",
  "voice_id": "JBFqnCBsd6RMkjVDRZzb"
}
```

**Process**:

1. Reads storyline from `stories/storyline.txt`
2. Converts text to speech using ElevenLabs
3. Merges all videos from `videos/` directory
4. Combines audio and video
5. Saves final video to `output/` directory

### 📤 Social Media Upload Endpoints

#### `POST /upload-to-tiktok` - TikTok Upload

**Description**: Uploads videos to TikTok using Business API.

**Request Body**:

```json
{
  "video_path": null,
  "title": null,
  "description": null,
  "privacy": "public"
}
```

#### `POST /upload-to-youtube` - YouTube Upload

**Description**: Uploads videos to YouTube using Data API v3.

**Request Body**:

```json
{
  "video_path": null,
  "title": "My AI Generated Video",
  "description": "Custom description...",
  "privacy": "public"
}
```

### 📊 Utility Endpoints

#### `GET /task-status/{task_id}` - Task Status

Check the status of background tasks.

#### `GET /list-files` - List Files

List all generated files in output directories.

#### `GET /download-file/{directory}/{filename}` - Download Files

Download specific generated files.

## 📝 Usage Examples

### Example 1: Complete Video Generation Workflow

```bash
# 1. Check system status
curl -X GET "http://localhost:8000/status"

# 2. Generate videos from user images
curl -X POST "http://localhost:8000/generate-video-user" \
  -H "Content-Type: application/json" \
  -d '{
    "image_dir": "./user_images",
    "pattern": "*.jpg",
    "model": "fal-ai/veo2/image-to-video",
    "prompt": "Create a smooth video with natural motion"
  }'

# 3. Check task status
curl -X GET "http://localhost:8000/task-status/task_20241201_143022_123456"

# 4. Create storyline from generated videos
curl -X POST "http://localhost:8000/create-storyline" \
  -H "Content-Type: application/json" \
  -d '{
    "videos_dir": "videos",
    "seconds_per_video": 5,
    "enhance_with_additional_images": true
  }'

# 5. Run text-to-speech pipeline
curl -X POST "http://localhost:8000/text-to-speech-pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "storyline_path": "stories/storyline.txt"
  }'

# 6. Upload to YouTube
curl -X POST "http://localhost:8000/upload-to-youtube" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My AI Generated Video",
    "description": "Created with AI pipeline",
    "privacy": "public"
  }'
```

### Example 2: Using Python Requests

```python
import requests
import time

base_url = "http://localhost:8000"

# 1. Start video generation
response = requests.post(f"{base_url}/generate-video-user", json={
    "image_dir": "./user_images",
    "pattern": "*.jpg",
    "model": "fal-ai/veo2/image-to-video",
    "prompt": "Generate a cinematic video with smooth motion"
})

task_id = response.json()["data"]["task_id"]
print(f"Started task: {task_id}")

# 2. Monitor progress
while True:
    status_response = requests.get(f"{base_url}/task-status/{task_id}")
    status = status_response.json()["data"]["status"]
  
    print(f"Status: {status}")
  
    if status in ["completed", "failed"]:
        print("Task finished!")
        print(status_response.json())
        break
  
    time.sleep(10)  # Check every 10 seconds

# 3. List generated files
files_response = requests.get(f"{base_url}/list-files")
print("Generated files:", files_response.json())
```

### Example 3: JavaScript/Fetch API

```javascript
const baseUrl = 'http://localhost:8000';

// Start video generation
async function generateVideos() {
  const response = await fetch(`${baseUrl}/generate-video-user`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_dir: './user_images',
      pattern: '*.jpg',
      model: 'fal-ai/veo2/image-to-video',
      prompt: 'Create a dynamic video with natural motion'
    })
  });
  
  const result = await response.json();
  console.log('Task started:', result.data.task_id);
  
  return result.data.task_id;
}

// Monitor task progress
async function monitorTask(taskId) {
  while (true) {
    const response = await fetch(`${baseUrl}/task-status/${taskId}`);
    const result = await response.json();
  
    console.log('Status:', result.data.status);
  
    if (['completed', 'failed'].includes(result.data.status)) {
      console.log('Final result:', result.data);
      break;
    }
  
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
  }
}

// Run workflow
async function runWorkflow() {
  try {
    const taskId = await generateVideos();
    await monitorTask(taskId);
  } catch (error) {
    console.error('Error:', error);
  }
}

runWorkflow();
```

## 🔄 Workflow

### Typical Complete Workflow:

1. **Check Status**: Verify system status and API keys
2. **Upload Images**: Place images in `user_images/` directory
3. **Generate Videos**: Call `/generate-video-user` endpoint
4. **Monitor Progress**: Check task status until completion
5. **Create Storyline**: Call `/create-storyline` to generate narrative
6. **Process Audio**: Call `/text-to-speech-pipeline` for final video
7. **Upload**: Use `/upload-to-youtube` or `/upload-to-tiktok`
8. **Download**: Get final files via `/download-file` endpoint

### Background Task Management:

- All long-running operations use background tasks
- Each task gets a unique ID for status tracking
- Tasks can be monitored in real-time
- Failed tasks include detailed error information

## 🛠️ Troubleshooting

### Common Issues:

#### 1. **Module Import Errors**

```
Error importing modules: No module named '...'
```

**Solution**: Ensure all numbered Python files exist in the project root.

#### 2. **API Key Missing**

```
{"detail": "FAL_KEY environment variable not set"}
```

**Solution**: Set required environment variables or create `.env` file.

#### 3. **Directory Not Found**

```
{"detail": "No images found matching pattern"}
```

**Solution**: Create required directories and add images:

```bash
mkdir -p user_images images videos audio output stories session_transcripts logs
```

#### 4. **Task Not Found**

```
{"detail": "Task not found"}
```

**Solution**: Task IDs expire. Start a new task and use the current task ID.

#### 5. **FFmpeg Not Found**

```
{"detail": "FFmpeg not found"}
```

**Solution**: Install FFmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Debug Mode:

Enable detailed logging by setting:

```bash
export FASTAPI_DEBUG=true
```

### Logs:

Check logs in:

- Console output from uvicorn
- `logs/` directory for module-specific logs

### Performance Tuning:

For better performance:

- Increase `max_concurrent` for video generation (careful with API limits)
- Use SSD storage for faster file operations
- Monitor system resources during processing

### API Rate Limits:

Be aware of rate limits:

- **FAL AI**: Check your plan limits
- **OpenAI**: GPT API has rate limits
- **ElevenLabs**: TTS API has character limits
- **TikTok/YouTube**: Upload quotas apply

## 🔒 Security Considerations

### Production Deployment:

1. **CORS Configuration**: Update CORS settings for production
2. **API Key Security**: Use proper secret management
3. **Rate Limiting**: Implement rate limiting for endpoints
4. **Authentication**: Add authentication for sensitive endpoints
5. **File Upload Security**: Validate uploaded files
6. **HTTPS**: Use HTTPS in production

### Example Production Settings:

```python
# In fastapi_server.py for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 📈 Monitoring

### Health Checks:

```bash
# Simple health check
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status
```

### Active Tasks:

```bash
# Check running tasks
curl http://localhost:8000/status | jq '.data.active_tasks'
```

### File System:

```bash
# List all generated files
curl http://localhost:8000/list-files | jq '.data.files'
```

This FastAPI server provides a complete REST API interface for the AI video generation pipeline, making it easy to integrate with web applications, mobile apps, or other services.
