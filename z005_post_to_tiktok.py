#!/usr/bin/env python3
"""
TikTok Video Uploader Script

This script automatically finds videos in the output folder that start with 'final_video'
and posts them to TikTok using TikTok's Business API.

Requirements:
- TikTok Business account
- TikTok API credentials (Client Key, Client Secret)
- Access token for posting videos

Setup:
1. Create a .env file with your TikTok API credentials:
   TIKTOK_CLIENT_KEY=your_client_key
   TIKTOK_CLIENT_SECRET=your_client_secret
   TIKTOK_ACCESS_TOKEN=your_access_token

2. Install required packages:
   pip install requests python-dotenv

Usage:
python z005_post_to_tiktok.py
"""

import os
import glob
import json
import time
import requests
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/tiktok_upload.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class TikTokUploader:
    def __init__(self):
        """Initialize TikTok uploader with API credentials."""
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")

        if not all([self.client_key, self.client_secret, self.access_token]):
            raise ValueError(
                "Missing TikTok API credentials. Please check your .env file."
            )

        self.base_url = "https://open.tiktokapis.com"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

    def find_latest_final_video(self, output_dir="output"):
        """
        Find the latest video file in output directory that starts with 'final_video'.

        Args:
            output_dir (str): Directory to search for videos

        Returns:
            str: Path to the latest final video file, or None if not found
        """
        try:
            # Pattern to match files starting with 'final_video'
            pattern = os.path.join(output_dir, "final_video*.mp4")
            video_files = glob.glob(pattern)

            if not video_files:
                logger.warning(
                    f"No video files starting with 'final_video' found in {output_dir}"
                )
                return None

            # Sort by modification time to get the latest
            latest_video = max(video_files, key=os.path.getmtime)
            logger.info(f"Found latest video: {latest_video}")
            return latest_video

        except Exception as e:
            logger.error(f"Error finding video files: {str(e)}")
            return None

    def get_video_info(self, video_path):
        """
        Extract basic information about the video file.

        Args:
            video_path (str): Path to the video file

        Returns:
            dict: Video information including size, duration estimate
        """
        try:
            stat = os.stat(video_path)
            size_mb = stat.st_size / (1024 * 1024)

            return {
                "path": video_path,
                "filename": os.path.basename(video_path),
                "size_mb": round(size_mb, 2),
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
            }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return None

    def upload_video_init(self, video_info):
        """
        Initialize video upload session with TikTok.

        Args:
            video_info (dict): Video information

        Returns:
            dict: Upload session information or None if failed
        """
        try:
            url = f"{self.base_url}/v2/post/publish/video/init/"

            payload = {
                "post_info": {
                    "title": f"AI Generated Video - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "description": "#AI #Generated #Content #Creative",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": int(video_info["size_mb"] * 1024 * 1024),
                    "chunk_size": 10000000,  # 10MB chunks
                    "total_chunk_count": 1,
                },
            }

            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                logger.info("Video upload initialized successfully")
                return result.get("data", {})
            else:
                logger.error(
                    f"Failed to initialize upload: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error initializing upload: {str(e)}")
            return None

    def upload_video_file(self, upload_url, video_path):
        """
        Upload the actual video file to TikTok's servers.

        Args:
            upload_url (str): Upload URL from initialization
            video_path (str): Path to the video file

        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            with open(video_path, "rb") as video_file:
                files = {"video": video_file}

                # Use a separate session for file upload (without JSON content-type)
                upload_response = requests.put(
                    upload_url,
                    files=files,
                    timeout=300,  # 5 minute timeout for large files
                )

                if upload_response.status_code in [200, 201]:
                    logger.info("Video file uploaded successfully")
                    return True
                else:
                    logger.error(
                        f"Failed to upload file: {upload_response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error uploading video file: {str(e)}")
            return False

    def publish_video(self, publish_id):
        """
        Publish the uploaded video to TikTok.

        Args:
            publish_id (str): Publish ID from upload initialization

        Returns:
            dict: Publish result or None if failed
        """
        try:
            url = f"{self.base_url}/v2/post/publish/status/fetch/"

            payload = {"publish_id": publish_id}

            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                logger.info("Video published successfully")
                return result.get("data", {})
            else:
                logger.error(
                    f"Failed to publish video: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error publishing video: {str(e)}")
            return None

    def upload_and_post(self, video_path=None):
        """
        Complete workflow to upload and post a video to TikTok.

        Args:
            video_path (str, optional): Specific video path. If None, finds latest final_video

        Returns:
            dict: Upload result with success status and details
        """
        try:
            # Find video if not specified
            if video_path is None:
                video_path = self.find_latest_final_video()
                if not video_path:
                    return {
                        "success": False,
                        "error": "No final_video found in output directory",
                    }

            # Check if video file exists
            if not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": f"Video file not found: {video_path}",
                }

            # Get video information
            video_info = self.get_video_info(video_path)
            if not video_info:
                return {"success": False, "error": "Failed to get video information"}

            logger.info(
                f"Starting upload for: {video_info['filename']} ({video_info['size_mb']} MB)"
            )

            # Step 1: Initialize upload
            upload_session = self.upload_video_init(video_info)
            if not upload_session:
                return {
                    "success": False,
                    "error": "Failed to initialize upload session",
                }

            upload_url = upload_session.get("upload_url")
            publish_id = upload_session.get("publish_id")

            if not upload_url or not publish_id:
                return {
                    "success": False,
                    "error": "Missing upload URL or publish ID from initialization",
                }

            # Step 2: Upload video file
            if not self.upload_video_file(upload_url, video_path):
                return {"success": False, "error": "Failed to upload video file"}

            # Step 3: Wait a moment for processing
            logger.info("Waiting for video processing...")
            time.sleep(10)

            # Step 4: Publish video
            publish_result = self.publish_video(publish_id)
            if not publish_result:
                return {"success": False, "error": "Failed to publish video"}

            return {
                "success": True,
                "video_path": video_path,
                "video_info": video_info,
                "publish_id": publish_id,
                "publish_result": publish_result,
                "message": f"Successfully posted {video_info['filename']} to TikTok!",
            }

        except Exception as e:
            logger.error(f"Error in upload_and_post: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}


def main():
    """Main function to run the TikTok uploader."""
    try:
        logger.info("Starting TikTok video upload process...")

        # Create uploader instance
        uploader = TikTokUploader()

        # Upload and post video
        result = uploader.upload_and_post()

        if result["success"]:
            logger.info(f"✅ {result['message']}")
            print(f"\n🎉 Success! {result['message']}")
            print(f"📹 Video: {result['video_info']['filename']}")
            print(f"📊 Size: {result['video_info']['size_mb']} MB")
            print(f"🆔 Publish ID: {result['publish_id']}")
        else:
            logger.error(f"❌ Failed to post video: {result['error']}")
            print(f"\n❌ Error: {result['error']}")

            # Provide helpful suggestions
            if "credentials" in result["error"].lower():
                print("\n💡 Make sure you have a .env file with:")
                print("   TIKTOK_CLIENT_KEY=your_client_key")
                print("   TIKTOK_CLIENT_SECRET=your_client_secret")
                print("   TIKTOK_ACCESS_TOKEN=your_access_token")
            elif "not found" in result["error"].lower():
                print(
                    "\n💡 Make sure you have a video file starting with 'final_video' in the output/ directory"
                )

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        print(f"\n💥 Critical error: {str(e)}")


if __name__ == "__main__":
    main()
