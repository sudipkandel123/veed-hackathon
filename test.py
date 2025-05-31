# -*- coding: utf-8 -*-
import fal_client
import os
import time
from typing import Optional, Dict, Any


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
                    "duration": duration,
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


def main():
    """Example usage of the FalImageToVideo class"""
    import os

    # Check if the image file exists
    image_path = "big-ben.jpg"
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found in the current directory.")
        print("Please place the image file in the same directory as this script.")
        return

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

    # Example 1: Convert using Veo 2 model
    try:
        print("=== Converting with Veo 2 Model ===")
        result_veo2 = converter.convert_image_to_video(
            image_path=image_path,
            model="fal-ai/veo2/image-to-video",
            prompt="A person walking through a beautiful garden with flowers swaying in the breeze",
            duration=5,
        )
        print(f"Veo 2 Result: {result_veo2}")

        if "video" in result_veo2:
            video_url = result_veo2["video"]["url"]
            print(f"Generated video URL: {video_url}")

    except Exception as e:
        print(f"Error with Veo 2: {e}")

    # Example 2: Convert using Wan-2.1 model
    try:
        print("\n=== Converting with Wan-2.1 Model ===")
        result_wan = converter.convert_image_to_video(
            image_path=image_path,
            model="fal-ai/wan-i2v",
            prompt="Create a cinematic video with dramatic lighting",
            resolution="720p",
        )
        print(f"Wan-2.1 Result: {result_wan}")

    except Exception as e:
        print(f"Error with Wan-2.1: {e}")

    # Example 3: Using data URL method for faster processing
    try:
        print("\n=== Converting with Data URL Method ===")
        result_data_url = converter.convert_with_data_url(
            image_path=image_path,
            model="fal-ai/minimax-video",
            prompt="Generate smooth motion video",
        )
        print(f"Data URL Result: {result_data_url}")

    except Exception as e:
        print(f"Error with data URL method: {e}")


if __name__ == "__main__":
    main()
