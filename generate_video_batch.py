# Import necessary libraries
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import fal_client
from typing import Dict, Any, List
import os
import requests
import uuid
from datetime import datetime
import aiohttp
import time
import ssl
import certifi

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

# Set up API keys and configuration
os.environ["FAL_KEY"] = (
    "57726426-5347-43c5-a45a-b57a2474fc51:a4a5bb69ce0b9ff0e091d32a95e5d532"
)

# Create videos directory if it doesn't exist
os.makedirs("videos", exist_ok=True)


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


class BatchVideoRequest(BaseModel):
    prompts: List[str]
    motion_bucket_id: int = 127
    cond_aug: float = 0.02
    steps: int = 20
    deep_cache: str = "none"
    fps: int = 10
    negative_prompt: str = "unrealistic, saturated, high contrast, big nose, painting, drawing, sketch, cartoon, anime, manga, render, CG, 3d, watermark, signature, label"
    video_size: str = "landscape_16_9"
    max_concurrent: int = 5  # Control concurrency to avoid overwhelming the API


# Function to download video from URL asynchronously
async def download_video_async(video_url: str, output_path: str) -> str:
    """
    Download video from URL to specified output path asynchronously

    Args:
        video_url: URL of the video to download
        output_path: Path to save the video

    Returns:
        Path to the downloaded video
    """
    print(f"📥 Starting async download: {output_path}")

    # Create SSL context with proper certificate verification
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Create connector with SSL context
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(video_url) as response:
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        print(f"✅ Download completed: {output_path}")
        return output_path

    except (aiohttp.ClientSSLError, ssl.SSLError) as ssl_error:
        print(f"⚠️ SSL error encountered, trying with fallback method: {ssl_error}")
        # Fallback to synchronous download with requests (which handles SSL better)
        return download_video(video_url, output_path)

    except Exception as e:
        print(f"❌ Async download failed: {e}")
        print("🔄 Trying fallback synchronous download...")
        # Fallback to synchronous download
        return download_video(video_url, output_path)


# Function to download video from URL (synchronous fallback)
def download_video(video_url: str, output_path: str) -> str:
    """
    Download video from URL to specified output path

    Args:
        video_url: URL of the video to download
        output_path: Path to save the video

    Returns:
        Path to the downloaded video
    """
    print(f"📥 Starting synchronous download: {output_path}")

    # Configure session with proper SSL and timeout settings
    session = requests.Session()
    session.verify = certifi.where()  # Use certifi certificate bundle

    try:
        response = session.get(video_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Synchronous download completed: {output_path}")
        return output_path

    except requests.exceptions.SSLError as ssl_error:
        print(f"⚠️ SSL error in synchronous download: {ssl_error}")
        print("🔧 Attempting download without SSL verification (not recommended)...")

        # Last resort: disable SSL verification
        session.verify = False
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = session.get(video_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Download completed (no SSL verification): {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Synchronous download failed: {e}")
        raise

    finally:
        session.close()


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


# Function to process a single video request
async def process_single_video(
    prompt: str, request_params: Dict[str, Any], request_id: int
) -> Dict[str, Any]:
    """
    Process a single video generation request

    Args:
        prompt: The prompt for video generation
        request_params: Parameters for video generation
        request_id: Unique identifier for this request

    Returns:
        Dictionary containing the result and metadata
    """
    start_time = time.time()

    try:
        print(
            f"🎬 Starting video generation {request_id} for prompt: '{prompt[:50]}...'"
        )

        # Generate video using fal.ai API
        result = await generate_video(prompt=prompt, **request_params)

        # Check if video generation was successful and download the video
        if result and "video" in result and "url" in result["video"]:
            video_url = result["video"]["url"]

            # Use original filename from response or generate unique one
            original_filename = result["video"].get("file_name", "generated_video.mp4")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]

            # Create filename with timestamp prefix to avoid conflicts
            name_parts = original_filename.split(".")
            if len(name_parts) > 1:
                filename = f"{timestamp}_{unique_id}_req{request_id}_{'.'.join(name_parts[:-1])}.{name_parts[-1]}"
            else:
                filename = (
                    f"{timestamp}_{unique_id}_req{request_id}_{original_filename}.mp4"
                )

            output_path = os.path.join("videos", filename)

            # Download the video asynchronously
            try:
                local_path = await download_video_async(video_url, output_path)
                result["local_path"] = local_path
                result["filename"] = filename

                # Add download success info
                file_size = result["video"].get("file_size", 0)
                processing_time = time.time() - start_time

                print(f"✅ Request {request_id} completed in {processing_time:.2f}s")
                print(f"   📁 Local path: {local_path}")
                print(f"   📏 File size: {file_size} bytes")
                print(f"   🎬 Original name: {original_filename}")

                result["download_success"] = True
                result["request_id"] = request_id
                result["processing_time_seconds"] = processing_time
                result["download_info"] = {
                    "original_filename": original_filename,
                    "local_filename": filename,
                    "file_size_bytes": file_size,
                }

            except Exception as e:
                print(f"❌ Error downloading video for request {request_id}: {e}")
                result["download_error"] = str(e)
                result["download_success"] = False
                result["request_id"] = request_id
        else:
            print(f"⚠️ No video URL found in response for request {request_id}")
            result["request_id"] = request_id
            result["download_success"] = False

        return {
            "success": True,
            "request_id": request_id,
            "prompt": prompt,
            "result": result,
        }

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"❌ Error processing request {request_id}: {e}")
        return {
            "success": False,
            "request_id": request_id,
            "prompt": prompt,
            "error": str(e),
            "processing_time_seconds": processing_time,
        }


# Video generation endpoint (single request)
@app.post("/generate-video")
async def create_video(request: VideoRequest):
    try:
        # Generate video using fal.ai API
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

        # Check if video generation was successful and download the video
        if result and "video" in result and "url" in result["video"]:
            video_url = result["video"]["url"]

            # Use original filename from response or generate unique one
            original_filename = result["video"].get("file_name", "generated_video.mp4")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]

            # Create filename with timestamp prefix to avoid conflicts
            name_parts = original_filename.split(".")
            if len(name_parts) > 1:
                filename = f"{timestamp}_{unique_id}_{'.'.join(name_parts[:-1])}.{name_parts[-1]}"
            else:
                filename = f"{timestamp}_{unique_id}_{original_filename}.mp4"

            output_path = os.path.join("videos", filename)

            # Download the video asynchronously
            try:
                local_path = await download_video_async(video_url, output_path)
                result["local_path"] = local_path
                result["filename"] = filename

                # Add download success info
                file_size = result["video"].get("file_size", 0)
                print(f"✅ Video successfully downloaded!")
                print(f"   📁 Local path: {local_path}")
                print(f"   📏 File size: {file_size} bytes")
                print(f"   🎬 Original name: {original_filename}")

                result["download_success"] = True
                result["download_info"] = {
                    "original_filename": original_filename,
                    "local_filename": filename,
                    "file_size_bytes": file_size,
                }

            except Exception as e:
                print(f"❌ Error downloading video: {e}")
                result["download_error"] = str(e)
                result["download_success"] = False
        else:
            print("⚠️ No video URL found in response")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Batch video generation endpoint (multiple requests)
@app.post("/generate-videos-batch")
async def create_videos_batch(request: BatchVideoRequest):
    """
    Generate multiple videos from a list of prompts in parallel

    Args:
        request: BatchVideoRequest containing list of prompts and parameters

    Returns:
        Dictionary containing results for all requests with summary statistics
    """
    try:
        start_time = time.time()
        prompts = request.prompts

        if not prompts:
            raise HTTPException(status_code=400, detail="No prompts provided")

        if len(prompts) > 50:  # Reasonable limit
            raise HTTPException(
                status_code=400, detail="Too many prompts. Maximum 50 allowed."
            )

        print(f"🚀 Starting batch processing of {len(prompts)} video requests")
        print(f"⚙️ Max concurrent requests: {request.max_concurrent}")

        # Prepare parameters for video generation
        request_params = {
            "motion_bucket_id": request.motion_bucket_id,
            "cond_aug": request.cond_aug,
            "steps": request.steps,
            "deep_cache": request.deep_cache,
            "fps": request.fps,
            "negative_prompt": request.negative_prompt,
            "video_size": request.video_size,
        }

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(request.max_concurrent)

        async def process_with_semaphore(prompt: str, request_id: int):
            async with semaphore:
                return await process_single_video(prompt, request_params, request_id)

        # Create tasks for all prompts
        tasks = [process_with_semaphore(prompt, i) for i, prompt in enumerate(prompts)]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        successful_count = 0
        failed_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "success": False,
                        "request_id": i,
                        "prompt": prompts[i],
                        "error": str(result),
                    }
                )
                failed_count += 1
            else:
                processed_results.append(result)
                if result.get("success", False):
                    successful_count += 1
                else:
                    failed_count += 1

        total_time = time.time() - start_time

        # Create summary
        summary = {
            "total_requests": len(prompts),
            "successful": successful_count,
            "failed": failed_count,
            "total_processing_time_seconds": total_time,
            "average_time_per_request": total_time / len(prompts) if prompts else 0,
            "max_concurrent_used": request.max_concurrent,
        }

        print(f"🏁 Batch processing completed!")
        print(f"   ✅ Successful: {successful_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   ⏱️ Total time: {total_time:.2f}s")
        print(f"   📊 Average per request: {summary['average_time_per_request']:.2f}s")

        return {"summary": summary, "results": processed_results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
