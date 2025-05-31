# -*- coding: utf-8 -*-
import fal_client
import os
import time
import asyncio
import aiohttp
import glob
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, List, Tuple


class FalImageToVideo:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Fal Image-to-Video converter

        Args:
            api_key: Optional API key. If not provided, will use FAL_KEY environment variable
        """
        if api_key:
            os.environ["FAL_KEY"] = api_key
        elif not os.environ.get("FAL_KEY"):
            raise ValueError(
                "API key must be provided either as parameter or FAL_KEY environment variable"
            )

        # Create videos directory if it doesn't exist
        os.makedirs("videos", exist_ok=True)

    def convert_image_to_video(
        self,
        image_path: str,
        model: str = "fal-ai/veo2/image-to-video",
        prompt: str = "",
        duration: int = 5,
        resolution: str = "720p",
    ) -> Dict[str, Any]:
        """
        Convert an image to video using fal.ai API

        Args:
            image_path: Path to the input image file
            model: Model to use for conversion
            prompt: Optional text prompt to guide video generation
            duration: Video duration in seconds (for supported models)
            resolution: Video resolution (480p or 720p for applicable models)

        Returns:
            Dictionary containing the generated video URL and metadata
        """

        # Upload the image file to fal.ai CDN
        print(f"Uploading image: {image_path}")
        image_url = fal_client.upload_file(image_path)
        print(f"Image uploaded successfully: {image_url}")

        # Prepare arguments based on the selected model
        arguments = self._prepare_arguments(
            model, image_url, prompt, duration, resolution
        )

        print(f"Starting video generation with model: {model}")
        print(f"Arguments: {arguments}")

        # Generate video using fal.ai API
        result = fal_client.subscribe(
            model,
            arguments=arguments,
            with_logs=True,
            on_queue_update=self._on_queue_update,
        )

        # Check if we got a result or if it's still in progress
        if hasattr(result, "status"):
            print(f"Request status: {result.status}")
            return {"status": result.status, "message": "Job is still processing"}

        return result

    def _prepare_arguments(
        self, model: str, image_url: str, prompt: str, duration: int, resolution: str
    ) -> Dict[str, Any]:
        """Prepare arguments based on the selected model"""

        base_args = {"image_url": image_url}

        if model == "fal-ai/veo2/image-to-video":
            base_args.update(
                {
                    "prompt": prompt
                    if prompt
                    else "Generate a video with natural motion",
                    "duration": f"{duration}s",  # Format as string with 's' suffix
                }
            )
        elif model == "fal-ai/wan-i2v":
            base_args.update(
                {
                    "prompt": prompt if prompt else "Create a video with smooth motion",
                    "resolution": resolution,
                }
            )
        elif model in [
            "fal-ai/minimax-video",
            "fal-ai/luma-dream-machine",
            "fal-ai/kling-video/v1/standard",
        ]:
            if prompt:
                base_args["prompt"] = prompt

        return base_args

    def _on_queue_update(self, update):
        """Callback function to handle queue updates"""
        # Check the class/type name instead of status attribute
        update_type = type(update).__name__

        if update_type == "InProgress":
            print(
                f"Generation in progress: {getattr(update, 'logs', 'No logs available')}"
            )
        elif update_type == "Completed":
            print("Video generation completed!")
        elif update_type == "Failed":
            print(f"Generation failed: {getattr(update, 'logs', 'No error details')}")
        elif update_type == "Queued":
            print(f"Job queued, waiting to start...")
        else:
            print(f"Update received: {update_type}")

    def convert_with_data_url(
        self,
        image_path: str,
        model: str = "fal-ai/veo2/image-to-video",
        prompt: str = "",
    ) -> Dict[str, Any]:
        """
        Convert image to video using data URL (for faster processing)

        Args:
            image_path: Path to the input image file
            model: Model to use for conversion
            prompt: Optional text prompt to guide video generation

        Returns:
            Dictionary containing the generated video URL and metadata
        """

        # Encode image as data URL
        print(f"Encoding image as data URL: {image_path}")
        image_data_url = fal_client.encode_file(image_path)

        arguments = {
            "image_url": image_data_url,
        }

        if prompt:
            arguments["prompt"] = prompt

        print(f"Starting video generation with model: {model}")

        result = fal_client.subscribe(
            model,
            arguments=arguments,
            with_logs=True,
            on_queue_update=self._on_queue_update,
        )

        # Check if we got a result or if it's still in progress
        if hasattr(result, "status"):
            print(f"Request status: {result.status}")
            return {"status": result.status, "message": "Job is still processing"}

        return result

    def download_video(self, video_url: str, output_path: str) -> str:
        """
        Download video from URL to specified output path

        Args:
            video_url: URL of the video to download
            output_path: Path to save the video

        Returns:
            Path to the downloaded video
        """
        print(f"Downloading video from {video_url} to {output_path}")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Video downloaded to {output_path}")
        return output_path


async def process_image(
    converter: FalImageToVideo, image_path: str, model: str, prompt: str
) -> Tuple[str, str, Dict]:
    """Process a single image and return the result along with image path"""
    # Use ThreadPoolExecutor to run the blocking convert function in a separate thread
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool,
            lambda: converter.convert_image_to_video(
                image_path=image_path, model=model, prompt=prompt
            ),
        )

    return image_path, model, result


async def process_images_parallel(
    converter: FalImageToVideo,
    image_dir: str = "./images",
    pattern: str = "*.jpg",
    model: str = "fal-ai/veo2/image-to-video",
    prompt: str = "Generate a natural motion video",
    max_concurrent: int = 3,
) -> List[Dict]:
    """
    Process multiple images in parallel

    Args:
        converter: FalImageToVideo instance
        image_dir: Directory containing images
        pattern: Glob pattern to match image files
        model: Model to use for conversion
        prompt: Prompt for generation
        max_concurrent: Maximum number of concurrent tasks

    Returns:
        List of results with video URLs and metadata
    """
    # Check if image directory exists
    if not os.path.exists(image_dir):
        print(f"Error: Image directory '{image_dir}' doesn't exist. Creating it now.")
        os.makedirs(image_dir, exist_ok=True)
        return []

    # Get all images matching the pattern
    image_paths = glob.glob(os.path.join(image_dir, pattern))

    if not image_paths:
        print(f"No images found matching pattern {pattern} in directory {image_dir}")
        return []

    # Sort images by modification time (newest first)
    image_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    print(f"Found {len(image_paths)} images to process")

    # Create tasks for each image but limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []

    async def process_with_semaphore(img_path):
        async with semaphore:
            return await process_image(converter, img_path, model, prompt)

    # Start all tasks
    for img_path in image_paths:
        task = asyncio.create_task(process_with_semaphore(img_path))
        tasks.append(task)

    # Wait for all tasks to complete
    results = []
    for task in asyncio.as_completed(tasks):
        try:
            image_path, model_used, result = await task
            # If successful and contains video URL, download it
            if (
                result
                and not hasattr(result, "status")
                and "video" in result
                and "url" in result["video"]
            ):
                video_url = result["video"]["url"]
                base_filename = os.path.basename(image_path)
                name_without_ext = os.path.splitext(base_filename)[0]
                timestamp = datetime.fromtimestamp(os.path.getmtime(image_path))
                output_filename = (
                    f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{name_without_ext}.mp4"
                )
                output_path = os.path.join("videos", output_filename)

                # Download in a separate thread to not block
                try:
                    with ThreadPoolExecutor() as pool:
                        await asyncio.get_event_loop().run_in_executor(
                            pool,
                            lambda: converter.download_video(video_url, output_path),
                        )

                    result["local_path"] = output_path
                    print(
                        f"Successfully downloaded video for {image_path} to {output_path}"
                    )
                except Exception as e:
                    print(f"Error downloading video for {image_path}: {e}")
            elif isinstance(result, dict) and "error" in result:
                print(f"API Error for {image_path}: {result['error']}")

            results.append(
                {"image_path": image_path, "model": model_used, "result": result}
            )
            print(f"Completed processing {image_path}")
        except Exception as e:
            error_details = str(e)
            print(f"Error processing image: {error_details}")
            results.append({"error": error_details})

    return results


async def main_async():
    """Asynchronous main function to process images in parallel"""
    import os

    # Get API key from environment variable
    api_key = os.environ.get("FAL_KEY")
    if not api_key:
        print("Error: FAL_KEY environment variable not set.")
        print("Please set your FAL API key using:")
        print("    export FAL_KEY=your_api_key_here")
        print("Or modify this script to provide the API key directly.")
        return

    # Initialize the converter with the API key
    try:
        converter = FalImageToVideo(api_key=api_key)
    except ValueError as e:
        print(f"Error: {e}")
        return

    # Process all JPG/JPEG images in the current directory
    patterns = ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]
    all_results = []

    for pattern in patterns:
        results = await process_images_parallel(
            converter=converter,
            image_dir="./images",
            pattern=pattern,
            model="fal-ai/veo2/image-to-video",
            prompt="Generate a smooth, natural motion video",
            max_concurrent=3,  # Process 3 images at a time
        )
        all_results.extend(results)

    # Print a summary of results
    print("\n=== Processing Summary ===")
    print(f"Total images processed: {len(all_results)}")

    success_count = sum(
        1 for r in all_results if "result" in r and "local_path" in r["result"]
    )
    print(f"Successfully generated videos: {success_count}")

    if success_count > 0:
        print("\nGenerated videos (newest first):")
        videos = [
            r["result"]["local_path"]
            for r in all_results
            if "result" in r and "local_path" in r["result"]
        ]
        for video in videos:
            print(f"  - {video}")


def main():
    """Entry point for the script, runs the async main function"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
