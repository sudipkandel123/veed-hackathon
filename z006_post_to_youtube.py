#!/usr/bin/env python3
"""
YouTube Video Uploader Script

This script automatically finds videos in the output folder that start with 'final_video'
and posts them to YouTube using YouTube Data API v3.

Requirements:
- Google Cloud Project with YouTube Data API v3 enabled
- OAuth 2.0 credentials (client_secrets.json)
- YouTube channel

Setup:
1. Create Google Cloud Project and enable YouTube Data API v3
2. Create OAuth 2.0 credentials and download client_secrets.json
3. Install required packages:
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

Usage:
python z006_post_to_youtube.py
"""

import os
import glob
import json
import time
import logging
import pickle
from datetime import datetime
from pathlib import Path

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/youtube_upload.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class YouTubeUploader:
    def __init__(self, client_secrets_file="client_secrets.json"):
        """Initialize YouTube uploader with OAuth credentials."""

        # YouTube API configuration
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.client_secrets_file = client_secrets_file
        self.credentials = None
        self.youtube = None

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Initialize YouTube service
        self._authenticate()

    def _authenticate(self):
        """Authenticate with YouTube API using OAuth 2.0."""
        creds = None

        # Token file stores the user's access and refresh tokens
        token_file = "youtube_token.pickle"

        if os.path.exists(token_file):
            with open(token_file, "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed YouTube credentials")
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"Client secrets file not found: {self.client_secrets_file}\n"
                        "Please download OAuth 2.0 credentials from Google Cloud Console"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes
                )
                creds = flow.run_local_server(port=0)
                logger.info("Completed YouTube OAuth authentication")

            # Save the credentials for the next run
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)

        self.credentials = creds
        self.youtube = build(self.api_service_name, self.api_version, credentials=creds)
        logger.info("YouTube API service initialized")

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

    def create_video_metadata(
        self, video_info, custom_title=None, custom_description=None
    ):
        """
        Create video metadata for YouTube upload.

        Args:
            video_info (dict): Video file information
            custom_title (str, optional): Custom video title
            custom_description (str, optional): Custom video description

        Returns:
            dict: Video metadata for YouTube API
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Default title and description
        title = custom_title or f"AI Generated Video - {timestamp}"
        description = (
            custom_description
            or f"""
🤖 AI Generated Content

This video was automatically generated using AI technology.

📹 Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📁 Original file: {video_info["filename"]}
📊 File size: {video_info["size_mb"]} MB

#AI #Generated #Content #Automation #Creative #Technology #ArtificialIntelligence

---
Created with AI video generation tools
        """.strip()
        )

        # YouTube video metadata
        metadata = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": [
                    "AI",
                    "Generated",
                    "Content",
                    "Automation",
                    "Creative",
                    "Technology",
                    "Artificial Intelligence",
                    "AI Video",
                    "Auto Generated",
                ],
                "categoryId": "28",  # Science & Technology category
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "public",  # Can be 'private', 'public', or 'unlisted'
                "madeForKids": False,
                "selfDeclaredMadeForKids": False,
            },
        }

        return metadata

    def upload_video(self, video_path, metadata):
        """
        Upload video to YouTube.

        Args:
            video_path (str): Path to the video file
            metadata (dict): Video metadata

        Returns:
            dict: Upload result with video ID or error info
        """
        try:
            # Create MediaFileUpload object
            media = MediaFileUpload(
                video_path,
                chunksize=-1,  # Upload in a single chunk
                resumable=True,
                mimetype="video/mp4",
            )

            # Call the API's videos.insert method to create and upload the video
            insert_request = self.youtube.videos().insert(
                part=",".join(metadata.keys()), body=metadata, media_body=media
            )

            # Execute the upload
            logger.info(f"Starting upload of {os.path.basename(video_path)}")
            response = self._resumable_upload(insert_request)

            if response:
                video_id = response["id"]
                logger.info(
                    f"Video uploaded successfully: https://youtube.com/watch?v={video_id}"
                )
                return {
                    "success": True,
                    "video_id": video_id,
                    "video_url": f"https://youtube.com/watch?v={video_id}",
                    "response": response,
                }
            else:
                return {
                    "success": False,
                    "error": "Upload failed - no response received",
                }

        except HttpError as e:
            logger.error(f"HTTP error during upload: {e}")
            return {"success": False, "error": f"HTTP error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return {"success": False, "error": f"Unexpected error: {e}"}

    def _resumable_upload(self, insert_request):
        """
        Execute a resumable upload with progress tracking.

        Args:
            insert_request: YouTube API insert request

        Returns:
            dict: API response or None if failed
        """
        response = None
        error = None
        retry = 0

        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if response is not None:
                    if "id" in response:
                        logger.info(f"Video upload completed successfully")
                        return response
                    else:
                        logger.error(
                            f"Upload failed with unexpected response: {response}"
                        )
                        return None
                elif status:
                    # Calculate and log progress
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")

            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    # Retry on server errors
                    retry += 1
                    if retry > 5:
                        logger.error(f"Upload failed after {retry} retries")
                        return None

                    wait_time = 2**retry
                    logger.warning(
                        f"Server error {e.resp.status}, retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Client error during upload: {e}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error during resumable upload: {e}")
                return None

        return response

    def upload_and_post(
        self, video_path=None, title=None, description=None, privacy="public"
    ):
        """
        Complete workflow to upload and post a video to YouTube.

        Args:
            video_path (str, optional): Specific video path. If None, finds latest final_video
            title (str, optional): Custom video title
            description (str, optional): Custom video description
            privacy (str): Privacy setting ('public', 'private', 'unlisted')

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
                f"Preparing upload for: {video_info['filename']} ({video_info['size_mb']} MB)"
            )

            # Create metadata
            metadata = self.create_video_metadata(video_info, title, description)
            metadata["status"]["privacyStatus"] = privacy

            # Upload video
            upload_result = self.upload_video(video_path, metadata)

            if upload_result["success"]:
                return {
                    "success": True,
                    "video_path": video_path,
                    "video_info": video_info,
                    "video_id": upload_result["video_id"],
                    "video_url": upload_result["video_url"],
                    "metadata": metadata,
                    "message": f"Successfully uploaded {video_info['filename']} to YouTube!",
                }
            else:
                return {
                    "success": False,
                    "error": upload_result["error"],
                    "video_path": video_path,
                }

        except Exception as e:
            logger.error(f"Error in upload_and_post: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}


def main():
    """Main function to run the YouTube uploader."""
    try:
        logger.info("Starting YouTube video upload process...")

        # Create uploader instance
        uploader = YouTubeUploader()

        # Upload and post video
        result = uploader.upload_and_post()

        if result["success"]:
            logger.info(f"✅ {result['message']}")
            print(f"\n🎉 Success! {result['message']}")
            print(f"📹 Video: {result['video_info']['filename']}")
            print(f"📊 Size: {result['video_info']['size_mb']} MB")
            print(f"🆔 Video ID: {result['video_id']}")
            print(f"🔗 URL: {result['video_url']}")
            print(f"👁️  Privacy: {result['metadata']['status']['privacyStatus']}")
        else:
            logger.error(f"❌ Failed to upload video: {result['error']}")
            print(f"\n❌ Error: {result['error']}")

            # Provide helpful suggestions
            if "not found" in result["error"].lower():
                if "client_secrets" in result["error"]:
                    print("\n💡 Setup required:")
                    print("   1. Create Google Cloud Project")
                    print("   2. Enable YouTube Data API v3")
                    print("   3. Create OAuth 2.0 credentials")
                    print("   4. Download client_secrets.json to project root")
                elif "final_video" in result["error"]:
                    print(
                        "\n💡 Make sure you have a video file starting with 'final_video' in the output/ directory"
                    )
            elif "quota" in result["error"].lower():
                print(
                    "\n💡 YouTube API quota exceeded. Try again later or request quota increase."
                )

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        print(f"\n💥 Critical error: {str(e)}")


if __name__ == "__main__":
    main()
