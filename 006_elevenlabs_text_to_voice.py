#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ElevenLabs Text-to-Speech and Video Processing Script

This script performs the following operations:
1. Reads storyline text from stories/storyline.txt
2. Converts text to audio using ElevenLabs API
3. Merges all videos from the videos folder
4. Combines the generated audio with the merged video
5. Outputs the final video with voiceover

Requirements:
- ElevenLabs API key set as environment variable ELEVENLABS_API_KEY
- ffmpeg installed for video processing
- elevenlabs Python package
"""

import os
import sys
import glob
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/elevenlabs_tts.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Import ElevenLabs
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
except ImportError:
    logger.error("ElevenLabs package not found. Install with: pip install elevenlabs")
    sys.exit(1)


class ElevenLabsVideoProcessor:
    """Main class for processing text-to-speech and video operations"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the processor

        Args:
            api_key: ElevenLabs API key. If not provided, uses ELEVENLABS_API_KEY env var
        """
        # Set up API key
        if api_key:
            os.environ["ELEVENLABS_API_KEY"] = api_key
        elif not os.environ.get("ELEVENLABS_API_KEY"):
            logger.error("ELEVENLABS_API_KEY environment variable not set")
            sys.exit(1)

        # Initialize ElevenLabs client
        self.client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

        # Create necessary directories
        self.ensure_directories()

        # Default voice settings
        self.voice_id = "JBFqnCBsd6RMkjVDRZzb"  # George - default voice
        self.model_id = "eleven_multilingual_v2"  # High quality model

        # Voice settings for natural speech
        self.voice_settings = VoiceSettings(
            stability=0.75, similarity_boost=0.85, style=0.25, use_speaker_boost=True
        )

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = ["stories", "videos", "output", "logs", "audio"]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")

    def read_storyline(self, storyline_path: str = "stories/storyline.txt") -> str:
        """
        Read the storyline text from file

        Args:
            storyline_path: Path to the storyline text file

        Returns:
            The storyline text content
        """
        if not os.path.exists(storyline_path):
            logger.error(f"Storyline file not found: {storyline_path}")
            sys.exit(1)

        try:
            with open(storyline_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    logger.error("Storyline file is empty")
                    sys.exit(1)

                logger.info(f"Successfully read storyline ({len(content)} characters)")
                logger.info(f"Preview: {content[:100]}...")
                return content

        except Exception as e:
            logger.error(f"Error reading storyline file: {e}")
            sys.exit(1)

    def convert_text_to_speech(
        self, text: str, output_path: str = "audio/voiceover.mp3"
    ) -> str:
        """
        Convert text to speech using ElevenLabs API

        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file

        Returns:
            Path to the generated audio file
        """
        try:
            logger.info("Converting text to speech...")
            logger.info(f"Using voice ID: {self.voice_id}")
            logger.info(f"Using model: {self.model_id}")

            # Generate audio
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model_id,
                voice_settings=self.voice_settings,
                output_format="mp3_44100_128",
            )

            # Save audio to file
            with open(output_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            logger.info(f"Audio generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            sys.exit(1)

    def get_video_files(self, videos_dir: str = "videos") -> List[str]:
        """
        Get all video files from the videos directory

        Args:
            videos_dir: Directory containing video files

        Returns:
            List of video file paths sorted by modification time
        """
        if not os.path.exists(videos_dir):
            logger.error(f"Videos directory not found: {videos_dir}")
            sys.exit(1)

        # Get all video files
        video_extensions = ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.webm"]
        video_files = []

        for extension in video_extensions:
            video_files.extend(glob.glob(os.path.join(videos_dir, extension)))

        if not video_files:
            logger.error(f"No video files found in {videos_dir}")
            sys.exit(1)

        # Sort by modification time (oldest first for chronological order)
        video_files.sort(key=lambda x: os.path.getmtime(x))

        logger.info(f"Found {len(video_files)} video files:")
        for i, video in enumerate(video_files, 1):
            logger.info(f"  {i}. {os.path.basename(video)}")

        return video_files

    def get_video_duration(self, video_path: str) -> float:
        """
        Get duration of a video file in seconds

        Args:
            video_path: Path to the video file

        Returns:
            Duration in seconds
        """
        try:
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                video_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not get duration for {video_path}: {e}")
            return 5.0  # Default 5 seconds

    def merge_videos(
        self, video_files: List[str], output_path: str = "output/merged_video.mp4"
    ) -> str:
        """
        Merge multiple video files into one

        Args:
            video_files: List of video file paths
            output_path: Path for the merged video

        Returns:
            Path to the merged video file
        """
        try:
            logger.info(f"Merging {len(video_files)} videos...")

            # Create a temporary file list for ffmpeg
            filelist_path = "temp_filelist.txt"
            with open(filelist_path, "w") as f:
                for video_file in video_files:
                    # Use absolute path and escape quotes
                    abs_path = os.path.abspath(video_file)
                    f.write(f"file '{abs_path}'\n")

            # FFmpeg command to concatenate videos
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                filelist_path,
                "-c",
                "copy",  # Copy codecs for faster processing
                output_path,
            ]

            logger.info("Running FFmpeg video merge...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Clean up temporary file
            os.remove(filelist_path)

            # Get merged video duration
            duration = self.get_video_duration(output_path)
            logger.info(f"Videos merged successfully: {output_path} ({duration:.2f}s)")

            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error during video merge: {e.stderr}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error merging videos: {e}")
            sys.exit(1)

    def combine_audio_video(
        self, video_path: str, audio_path: str, output_path: str = None
    ) -> str:
        """
        Combine audio and video into final output

        Args:
            video_path: Path to the video file
            audio_path: Path to the audio file
            output_path: Path for the final output

        Returns:
            Path to the final video with audio
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/final_video_with_voiceover_{timestamp}.mp4"

        try:
            logger.info("Combining audio and video...")

            # Get video and audio durations
            video_duration = self.get_video_duration(video_path)

            # FFmpeg command to combine audio and video
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-i",
                audio_path,
                "-c:v",
                "libx264",  # Video codec
                "-c:a",
                "aac",  # Audio codec
                "-strict",
                "experimental",
                "-shortest",  # End when shortest stream ends
                "-map",
                "0:v:0",  # Map first video stream
                "-map",
                "1:a:0",  # Map first audio stream
                output_path,
            ]

            logger.info("Running FFmpeg audio/video combination...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            final_duration = self.get_video_duration(output_path)
            logger.info(f"Final video created: {output_path} ({final_duration:.2f}s)")

            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error during audio/video combination: {e.stderr}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error combining audio and video: {e}")
            sys.exit(1)

    def process_full_pipeline(
        self,
        storyline_path: str = "stories/storyline.txt",
        voice_id: Optional[str] = None,
    ) -> str:
        """
        Run the complete pipeline: text-to-speech + video merge + combine

        Args:
            storyline_path: Path to the storyline text file
            voice_id: Optional custom voice ID

        Returns:
            Path to the final output video
        """
        logger.info("Starting complete ElevenLabs video processing pipeline...")

        # Set custom voice if provided
        if voice_id:
            self.voice_id = voice_id
            logger.info(f"Using custom voice ID: {voice_id}")

        # Step 1: Read storyline
        logger.info("Step 1: Reading storyline...")
        storyline_text = self.read_storyline(storyline_path)

        # Step 2: Convert to speech
        logger.info("Step 2: Converting text to speech...")
        audio_path = self.convert_text_to_speech(storyline_text)

        # Step 3: Get and merge videos
        logger.info("Step 3: Processing videos...")
        video_files = self.get_video_files()
        merged_video_path = self.merge_videos(video_files)

        # Step 4: Combine audio and video
        logger.info("Step 4: Combining audio and video...")
        final_output = self.combine_audio_video(merged_video_path, audio_path)

        logger.info(f"✅ Pipeline completed successfully!")
        logger.info(f"📁 Final output: {final_output}")

        return final_output


def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(
        description="ElevenLabs Text-to-Speech Video Processing Pipeline"
    )
    parser.add_argument(
        "--storyline",
        "-s",
        default="stories/storyline.txt",
        help="Path to storyline text file (default: stories/storyline.txt)",
    )
    parser.add_argument(
        "--voice-id",
        "-v",
        help="ElevenLabs voice ID (default: JBFqnCBsd6RMkjVDRZzb - George)",
    )
    parser.add_argument(
        "--api-key",
        "-k",
        help="ElevenLabs API key (can also use ELEVENLABS_API_KEY env var)",
    )

    args = parser.parse_args()

    # Check for ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("FFmpeg not found. Please install FFmpeg to use this script.")
        sys.exit(1)

    # Initialize processor
    processor = ElevenLabsVideoProcessor(api_key=args.api_key)

    # Run the pipeline
    try:
        final_output = processor.process_full_pipeline(
            storyline_path=args.storyline, voice_id=args.voice_id
        )

        print(f"\n🎉 SUCCESS! Your video with voiceover is ready:")
        print(f"📁 File: {final_output}")
        print(f"📏 Size: {os.path.getsize(final_output) / (1024 * 1024):.1f} MB")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
