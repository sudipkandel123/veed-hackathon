#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transcript to Image Downloader with Storyline Creator

This script reads transcripts from session_transcripts folder,
uses OpenAI API to extract visual concepts, downloads relevant images,
and creates storylines based on existing videos in the videos folder.
"""

import os
import sys
import glob
import asyncio
import aiohttp
import requests
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from PIL import Image
from io import BytesIO
import openai


class TranscriptImageDownloader:
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the Transcript Image Downloader with Storyline Creator

        Args:
            openai_api_key: OpenAI API key for transcript analysis
        """
        # Set up OpenAI
        if openai_api_key:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
        elif os.environ.get("OPENAI_API_KEY"):
            self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        else:
            raise ValueError(
                "OpenAI API key must be provided either as parameter or OPENAI_API_KEY environment variable"
            )

        # Create directories if they don't exist
        os.makedirs("images", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("videos", exist_ok=True)
        os.makedirs("stories", exist_ok=True)

        print(
            "✅ Transcript Image Downloader with Storyline Creator initialized successfully"
        )

    def read_transcript_file(self, file_path: str) -> str:
        """Read and return the content of a transcript file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"📄 Successfully read transcript: {os.path.basename(file_path)}")
            return content
        except Exception as e:
            print(f"❌ Error reading transcript file {file_path}: {e}")
            return ""

    def extract_image_concepts_with_chatgpt(self, transcript_content: str) -> List[str]:
        """
        Use ChatGPT to analyze transcript and extract visual concepts

        Args:
            transcript_content: Raw transcript content

        Returns:
            List of image search terms like "image of..."
        """
        try:
            prompt = """
            Analyze the following conversation transcript and extract exactly 5 visual concepts that would be perfect for finding relevant images.

            Your response should ONLY contain 5 lines, each starting with "image of" followed by 2-4 words that describe a visual concept from the transcript.

            Focus on:
            - Main subjects, people, objects, or places mentioned
            - Key topics, products, or services discussed
            - Visual elements or concepts that came up
            - Important themes or ideas that have visual representation

            Format each line exactly like this:
            image of [concept]
            
            Example responses:
            image of business meeting
            image of coffee shop
            image of laptop computer
            image of mountain landscape
            image of team collaboration

            Only provide the 5 lines, nothing else.

            Transcript:
            {transcript}
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing conversations and extracting key visual concepts for image search. Always respond with exactly 5 lines starting with 'image of'.",
                    },
                    {
                        "role": "user",
                        "content": prompt.format(transcript=transcript_content),
                    },
                ],
                max_tokens=150,
                temperature=0.3,
            )

            # Extract and clean the image concepts
            concepts_text = response.choices[0].message.content.strip()
            image_concepts = []

            for line in concepts_text.split("\n"):
                line = line.strip()
                if line.lower().startswith("image of"):
                    # Extract the concept part (remove "image of" prefix)
                    concept = line[8:].strip()  # Remove "image of" (8 characters)
                    if concept:
                        image_concepts.append(concept)

            # Ensure we have exactly 5 concepts
            image_concepts = image_concepts[:5]

            print(f"🎯 Extracted {len(image_concepts)} image concepts:")
            for i, concept in enumerate(image_concepts, 1):
                print(f"   {i}. image of {concept}")

            return image_concepts

        except Exception as e:
            print(f"❌ Error extracting image concepts with ChatGPT: {e}")
            return []

    async def search_google_images(self, query: str, max_results: int = 2) -> List[str]:
        """
        Search Google Images for the given query (JPG/JPEG only)

        Args:
            query: Search query
            max_results: Maximum number of image URLs to return

        Returns:
            List of JPG/JPEG image URLs
        """
        try:
            # Format search query
            search_query = f"image of {query}".replace(" ", "+")
            search_url = (
                f"https://www.google.com/search?q={search_query}&tbm=isch&tbs=isz:m"
            )

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            print(f"🔍 Searching Google Images for JPG/JPEG: {query}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()

                        # Extract image URLs using regex (JPG/JPEG only)
                        img_pattern = r'"(https://[^"]*\.(?:jpg|jpeg))"'
                        matches = re.findall(img_pattern, html_content, re.IGNORECASE)

                        # Filter valid JPG/JPEG URLs only
                        valid_urls = []
                        for url in matches:
                            if any(ext in url.lower() for ext in [".jpg", ".jpeg"]):
                                # Skip very small or thumbnail images
                                if not any(
                                    skip in url.lower()
                                    for skip in ["thumb", "icon", "avatar", "logo"]
                                ):
                                    valid_urls.append(url)
                                    if len(valid_urls) >= max_results:
                                        break

                        print(
                            f"✅ Found {len(valid_urls)} JPG/JPEG image URLs for: {query}"
                        )
                        return valid_urls[:max_results]
                    else:
                        print(f"⚠️ Google search failed with status: {response.status}")
                        return []

        except Exception as e:
            print(f"❌ Error searching Google Images for '{query}': {e}")
            return []

    async def download_and_save_image(self, url: str, concept: str, index: int) -> bool:
        """
        Download image from URL and save to images folder

        Args:
            url: Image URL
            concept: The concept being searched for
            index: Index number for filename

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create filename
            safe_concept = re.sub(r"[^\w\s-]", "", concept).strip().replace(" ", "_")
            filename = f"{safe_concept}_{index}.jpg"
            filepath = os.path.join("images", filename)

            print(f"📥 Downloading image: {filename}")

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        image_data = await response.read()

                        # Process image with PIL
                        with Image.open(BytesIO(image_data)) as img:
                            # Convert to RGB if necessary
                            if img.mode in ("RGBA", "LA", "P"):
                                img = img.convert("RGB")

                            # Resize if too large
                            max_size = (1024, 1024)
                            img.thumbnail(max_size, Image.Resampling.LANCZOS)

                            # Save as JPEG
                            img.save(filepath, "JPEG", quality=85, optimize=True)

                        print(f"✅ Successfully saved: {filename}")
                        return True
                    else:
                        print(f"⚠️ Failed to download image: HTTP {response.status}")
                        return False

        except Exception as e:
            print(f"❌ Error downloading/saving image: {e}")
            return False

    async def process_single_transcript(self, transcript_path: str) -> Dict[str, Any]:
        """
        Process a single transcript file

        Args:
            transcript_path: Path to the transcript file

        Returns:
            Processing results dictionary
        """
        print(f"\n🚀 Processing transcript: {os.path.basename(transcript_path)}")
        print("=" * 50)

        # Read transcript
        transcript_content = self.read_transcript_file(transcript_path)
        if not transcript_content:
            return {"success": False, "error": "Could not read transcript file"}

        # Extract image concepts using ChatGPT
        image_concepts = self.extract_image_concepts_with_chatgpt(transcript_content)
        if not image_concepts:
            return {"success": False, "error": "Could not extract image concepts"}

        # Search and download images for each concept
        results = {
            "success": True,
            "transcript_file": transcript_path,
            "concepts": image_concepts,
            "downloaded_images": [],
            "errors": [],
        }

        for i, concept in enumerate(image_concepts, 1):
            try:
                # Search for images
                image_urls = await self.search_google_images(concept, max_results=1)

                if not image_urls:
                    error_msg = f"No images found for: {concept}"
                    print(f"⚠️ {error_msg}")
                    results["errors"].append(error_msg)
                    continue

                # Download the first (best) image
                url = image_urls[0]
                success = await self.download_and_save_image(url, concept, i)

                if success:
                    safe_concept = (
                        re.sub(r"[^\w\s-]", "", concept).strip().replace(" ", "_")
                    )
                    filename = f"{safe_concept}_{i}.jpg"
                    results["downloaded_images"].append(
                        {"concept": concept, "filename": filename, "url": url}
                    )
                else:
                    results["errors"].append(f"Failed to download image for: {concept}")

            except Exception as e:
                error_msg = f"Error processing concept '{concept}': {e}"
                print(f"❌ {error_msg}")
                results["errors"].append(error_msg)

        # Update success status
        results["success"] = len(results["downloaded_images"]) > 0

        print(f"\n📊 Processing Summary for {os.path.basename(transcript_path)}:")
        print(f"   ✅ Concepts extracted: {len(image_concepts)}")
        print(f"   📸 Images downloaded: {len(results['downloaded_images'])}")
        print(f"   ⚠️ Errors: {len(results['errors'])}")

        return results

    async def process_all_transcripts(
        self, transcripts_dir: str = "session_transcripts"
    ) -> List[Dict[str, Any]]:
        """
        Process all transcript files in the specified directory

        Args:
            transcripts_dir: Directory containing transcript files

        Returns:
            List of processing results for each transcript
        """
        if not os.path.exists(transcripts_dir):
            print(f"❌ Transcripts directory '{transcripts_dir}' does not exist")
            return []

        # Find all transcript files
        transcript_files = glob.glob(os.path.join(transcripts_dir, "*.txt"))
        if not transcript_files:
            print(f"⚠️ No transcript files found in '{transcripts_dir}'")
            return []

        print(f"📁 Found {len(transcript_files)} transcript files to process")

        # Process each transcript file
        all_results = []
        for transcript_file in transcript_files:
            try:
                result = await self.process_single_transcript(transcript_file)
                all_results.append(result)
            except Exception as e:
                print(f"❌ Error processing {transcript_file}: {e}")
                all_results.append(
                    {
                        "success": False,
                        "transcript_file": transcript_file,
                        "error": str(e),
                    }
                )

        return all_results

    def save_processing_log(self, results: List[Dict[str, Any]]) -> str:
        """Save processing results to a log file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"transcript_processing_log_{timestamp}.json"
            log_path = os.path.join("logs", log_filename)

            log_data = {
                "timestamp": timestamp,
                "total_transcripts": len(results),
                "successful_transcripts": sum(
                    1 for r in results if r.get("success", False)
                ),
                "total_images_downloaded": sum(
                    len(r.get("downloaded_images", [])) for r in results
                ),
                "results": results,
            }

            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            print(f"📄 Processing log saved to: {log_path}")
            return log_path

        except Exception as e:
            print(f"❌ Error saving processing log: {e}")
            return ""

    def count_videos_in_folder(self, videos_dir: str = "videos") -> int:
        """
        Count the number of video files in the videos directory

        Args:
            videos_dir: Directory containing video files

        Returns:
            Number of video files found
        """
        if not os.path.exists(videos_dir):
            print(f"❌ Videos directory '{videos_dir}' does not exist")
            return 0

        # Look for common video file extensions
        video_extensions = ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.webm", "*.flv"]
        video_files = []

        for extension in video_extensions:
            video_files.extend(glob.glob(os.path.join(videos_dir, extension)))

        video_count = len(video_files)
        print(f"📹 Found {video_count} video files in '{videos_dir}'")

        if video_count > 0:
            print("   Video files:")
            for video_file in video_files:
                print(f"      - {os.path.basename(video_file)}")

        return video_count

    def calculate_story_duration(
        self, video_count: int, seconds_per_video: int = 5
    ) -> int:
        """
        Calculate total story duration based on video count and seconds per video

        Args:
            video_count: Number of videos
            seconds_per_video: Duration per video in seconds (default: 5)

        Returns:
            Total story duration in seconds
        """
        total_duration = video_count * seconds_per_video
        print(f"📊 Story Duration Calculation:")
        print(f"   📹 Videos: {video_count}")
        print(f"   ⏱️ Seconds per video: {seconds_per_video}")
        print(
            f"   🎬 Total story duration: {total_duration} seconds ({total_duration / 60:.1f} minutes)"
        )
        return total_duration

    def analyze_existing_images(self, images_dir: str = "images") -> List[str]:
        """
        Analyze existing images to understand the context for storyline creation

        Args:
            images_dir: Directory containing downloaded images

        Returns:
            List of image concepts/descriptions
        """
        if not os.path.exists(images_dir):
            print(f"❌ Images directory '{images_dir}' does not exist")
            return []

        # Look for image files
        image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
        image_files = []

        for extension in image_extensions:
            image_files.extend(glob.glob(os.path.join(images_dir, extension)))

        if not image_files:
            print(f"⚠️ No image files found in '{images_dir}'")
            return []

        print(f"🖼️ Found {len(image_files)} image files to analyze")

        # Extract concepts from filenames (assuming they contain descriptive names)
        concepts = []
        for image_file in image_files:
            filename = os.path.basename(image_file)
            # Remove extension and common suffixes like _1, _2, etc.
            concept = re.sub(
                r"_\d+\.(jpg|jpeg|png|webp)$", "", filename, flags=re.IGNORECASE
            )
            concept = concept.replace("_", " ").strip()
            if concept and concept not in concepts:
                concepts.append(concept)

        print(f"🎯 Extracted concepts from existing images:")
        for i, concept in enumerate(concepts, 1):
            print(f"   {i}. {concept}")

        return concepts

    def create_storyline_with_chatgpt(
        self, existing_concepts: List[str], total_duration: int, video_count: int
    ) -> Dict[str, Any]:
        """
        Use ChatGPT to create a YouTube Shorts voiceover script based on existing image concepts

        Args:
            existing_concepts: List of concepts from existing images
            total_duration: Total story duration in seconds
            video_count: Number of videos in the sequence

        Returns:
            Dictionary containing the complete storyline
        """
        try:
            concepts_text = (
                ", ".join(existing_concepts)
                if existing_concepts
                else "modern lifestyle content"
            )

            prompt = f"""
            Create a {total_duration}-second YouTube Shorts voiceover script based on these visual concepts: {concepts_text}

            You need to write ONLY the spoken words that will be converted to voice. No formatting, no instructions, no scene descriptions - just the exact text that the narrator will say.

            Requirements:
            - Write for exactly {total_duration} seconds of speech (approximately {total_duration * 2.5} words)
            - Based on the visual concepts: {concepts_text}
            - Make it engaging for YouTube Shorts (hook in first 3 seconds)
            - Modern, relatable content that people will share
            - Natural speaking pace and rhythm
            - Include a call-to-action at the end
            - Make it sound conversational and authentic
            - No historical or ancient themes - keep it current and trendy

            Write ONLY the voiceover script - nothing else. The script should flow naturally as one continuous narration.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a YouTube Shorts voiceover writer. Create engaging, modern scripts that are perfect for text-to-speech conversion. Write only the spoken words - no formatting, no instructions, no descriptions.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                max_tokens=800,
                temperature=0.8,
            )

            # Get the clean voiceover script
            voiceover_script = response.choices[0].message.content.strip()

            # Remove any formatting that might have been added
            voiceover_script = voiceover_script.replace("**", "").replace("*", "")
            voiceover_script = re.sub(
                r"\[.*?\]", "", voiceover_script
            )  # Remove any [instructions]
            voiceover_script = re.sub(
                r"\(.*?\)", "", voiceover_script
            )  # Remove any (instructions)
            voiceover_script = voiceover_script.strip()

            # Create storyline data for internal use
            storyline_data = {
                "story": {
                    "title": "YouTube Shorts Voiceover",
                    "genre": "YouTube Shorts",
                    "theme": "Modern viral content",
                    "overall_description": f"Voiceover script based on {concepts_text}",
                    "duration_seconds": total_duration,
                    "mood": "Engaging",
                },
                "additional_concepts_needed": [
                    "trending music",
                    "good lighting",
                    "mobile setup",
                ],
                "video_count": video_count,
                "format": "Voiceover Script",
                "raw_text": voiceover_script,
            }

            print(f"🎙️ Generated YouTube Shorts voiceover script")
            print(f"   ⏱️ Duration: {total_duration} seconds")
            print(f"   📝 Word count: ~{len(voiceover_script.split())} words")
            print(f"   🎯 Ready for text-to-speech conversion")

            return storyline_data

        except Exception as e:
            print(f"❌ Error creating voiceover script with ChatGPT: {e}")
            return self.create_fallback_voiceover_script(
                existing_concepts, total_duration, video_count
            )

    def create_fallback_voiceover_script(
        self, existing_concepts: List[str], total_duration: int, video_count: int
    ) -> Dict[str, Any]:
        """
        Create a simple fallback voiceover script if ChatGPT fails

        Args:
            existing_concepts: List of concepts from existing images
            total_duration: Total story duration in seconds
            video_count: Number of videos in the sequence

        Returns:
            Dictionary containing a basic voiceover script
        """
        print("🔄 Creating fallback voiceover script...")

        concepts_text = (
            ", ".join(existing_concepts) if existing_concepts else "modern lifestyle"
        )

        # Create a simple voiceover script
        if "coffee" in concepts_text.lower():
            fallback_script = f"Hey everyone! Today I'm sharing my ultimate {concepts_text} discovery. You won't believe how this simple change transformed my entire routine. Watch this. This is exactly what I needed in my life. The results speak for themselves. Try this yourself and let me know what you think in the comments!"
        elif "travel" in concepts_text.lower() or "city" in concepts_text.lower():
            fallback_script = f"This {concepts_text} experience completely blew my mind. I never expected to find something this amazing. Look at this incredible view. The energy here is absolutely unmatched. This is why I love exploring new places. Make sure to save this location for your next adventure!"
        elif "work" in concepts_text.lower() or "laptop" in concepts_text.lower():
            fallback_script = f"This {concepts_text} hack is a total game changer. I've been doing this all wrong until now. Here's the secret that changed everything. The productivity boost is incredible. This simple method saves me hours every day. You need to try this immediately!"
        else:
            fallback_script = f"This {concepts_text} discovery is absolutely incredible. I had to share this with you immediately. The transformation is unreal. This changed my entire perspective. The results are beyond what I expected. You have to see this for yourself!"

        storyline = {
            "story": {
                "title": f"Modern {concepts_text.title()} Voiceover",
                "genre": "YouTube Shorts",
                "theme": "Modern viral content",
                "overall_description": f"A {total_duration}-second voiceover script about {concepts_text}",
                "duration_seconds": total_duration,
                "mood": "Modern and engaging",
            },
            "additional_concepts_needed": [
                "trending music",
                "good lighting",
                "mobile setup",
            ],
            "video_count": video_count,
            "format": "Voiceover Script",
            "raw_text": fallback_script,
        }

        return storyline

    def save_storyline(
        self, storyline: Dict[str, Any], additional_images: List[Dict[str, Any]] = None
    ) -> str:
        """
        Save the voiceover script to a clean text file

        Args:
            storyline: The storyline dictionary
            additional_images: List of additional images downloaded

        Returns:
            Path to the saved storyline file
        """
        try:
            storyline_filename = "storyline.txt"
            storyline_path = os.path.join("stories", storyline_filename)

            # Get the clean voiceover script
            voiceover_script = storyline.get("raw_text", "")

            if not voiceover_script:
                # Create basic voiceover if raw text is not available
                voiceover_script = "This content is absolutely amazing. I had to share this discovery with you. The transformation is incredible. This changed everything for me. You need to try this yourself and see the results!"

            # Write only the clean voiceover script (no formatting, no metadata)
            with open(storyline_path, "w", encoding="utf-8") as f:
                f.write(voiceover_script)

            print(f"🎙️ Voiceover script saved to: {storyline_path}")
            print(f"✅ Ready for text-to-speech conversion")
            return storyline_path

        except Exception as e:
            print(f"❌ Error saving voiceover script: {e}")
            return ""

    async def generate_additional_images_for_story(
        self, additional_concepts: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate additional images to enhance the storyline

        Args:
            additional_concepts: List of additional concepts needed for the story

        Returns:
            List of results for additional image downloads
        """
        if not additional_concepts:
            print("ℹ️ No additional concepts needed for the story")
            return []

        print(
            f"🎨 Generating {len(additional_concepts)} additional images for story enhancement:"
        )
        for i, concept in enumerate(additional_concepts, 1):
            print(f"   {i}. {concept}")

        results = []
        for i, concept in enumerate(additional_concepts, 1):
            try:
                # Search for images
                image_urls = await self.search_google_images(concept, max_results=1)

                if image_urls:
                    # Download the image
                    url = image_urls[0]
                    success = await self.download_and_save_image(
                        url, concept, i + 100
                    )  # Use offset to avoid conflicts

                    if success:
                        safe_concept = (
                            re.sub(r"[^\w\s-]", "", concept).strip().replace(" ", "_")
                        )
                        filename = f"story_enhancement_{safe_concept}_{i + 100}.jpg"
                        results.append(
                            {
                                "concept": concept,
                                "filename": filename,
                                "url": url,
                                "success": True,
                            }
                        )
                    else:
                        results.append(
                            {
                                "concept": concept,
                                "success": False,
                                "error": "Download failed",
                            }
                        )
                else:
                    results.append(
                        {
                            "concept": concept,
                            "success": False,
                            "error": "No images found",
                        }
                    )

            except Exception as e:
                results.append({"concept": concept, "success": False, "error": str(e)})

        successful_downloads = [r for r in results if r.get("success", False)]
        print(
            f"✅ Successfully downloaded {len(successful_downloads)} additional images"
        )

        return results

    async def create_story_from_videos(
        self,
        videos_dir: str = "videos",
        seconds_per_video: int = 5,
        enhance_with_additional_images: bool = True,
    ) -> Dict[str, Any]:
        """
        Main function to create a storyline based on existing videos

        Args:
            videos_dir: Directory containing video files
            seconds_per_video: Duration per video in seconds
            enhance_with_additional_images: Whether to download additional images

        Returns:
            Complete storyline creation result
        """
        print("🎬 Starting storyline creation based on existing videos")
        print("=" * 60)

        # Step 1: Count videos
        video_count = self.count_videos_in_folder(videos_dir)
        if video_count == 0:
            print("❌ No videos found. Cannot create storyline without videos.")
            return {"success": False, "error": "No videos found"}

        # Step 2: Calculate story duration
        total_duration = self.calculate_story_duration(video_count, seconds_per_video)

        # Step 3: Analyze existing images for context
        existing_concepts = self.analyze_existing_images("images")

        # Step 4: Create storyline with ChatGPT
        print(f"\n🤖 Creating storyline with ChatGPT...")
        storyline = self.create_storyline_with_chatgpt(
            existing_concepts, total_duration, video_count
        )

        # Step 5: Optionally enhance with additional images
        additional_images = []
        if enhance_with_additional_images and storyline.get(
            "additional_concepts_needed"
        ):
            print(f"\n🎨 Enhancing story with additional images...")
            additional_images = await self.generate_additional_images_for_story(
                storyline["additional_concepts_needed"]
            )

        # Step 6: Save the complete storyline
        storyline_path = self.save_storyline(storyline, additional_images)

        # Create result summary
        result = {
            "success": True,
            "storyline": storyline,
            "video_count": video_count,
            "total_duration_seconds": total_duration,
            "seconds_per_video": seconds_per_video,
            "existing_concepts_used": len(existing_concepts),
            "additional_images_downloaded": len(
                [img for img in additional_images if img.get("success", False)]
            ),
            "storyline_file": storyline_path,
        }

        # Print final summary
        print(f"\n🎉 Storyline Creation Complete!")
        print(f"   📹 Videos analyzed: {video_count}")
        print(
            f"   ⏱️ Story duration: {total_duration} seconds ({total_duration / 60:.1f} minutes)"
        )
        print(f"   🎭 Story title: '{storyline['story']['title']}'")
        print(f"   🎯 Concepts used: {len(existing_concepts)}")
        if additional_images:
            successful_additional = len(
                [img for img in additional_images if img.get("success", False)]
            )
            print(
                f"   🎨 Additional images: {successful_additional}/{len(additional_images)}"
            )
        print(f"   📄 Storyline saved: {storyline_path}")

        return result


async def main():
    """Main function to run the transcript image downloader with storyline creator"""
    print("🤖 Transcript to Image Downloader with Storyline Creator")
    print("=" * 40)

    # Check for OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set it using: export OPENAI_API_KEY=your_openai_key")
        return

    try:
        # Initialize the downloader
        downloader = TranscriptImageDownloader(openai_api_key=openai_key)

        # Process all transcripts
        results = await downloader.process_all_transcripts("session_transcripts")

        if not results:
            print("❌ No transcripts were processed")
            return

        # Save processing log
        log_path = downloader.save_processing_log(results)

        # Print final summary
        print(f"\n🎉 Final Summary:")
        print(f"   📁 Total transcripts processed: {len(results)}")

        successful_results = [r for r in results if r.get("success", False)]
        print(f"   ✅ Successfully processed: {len(successful_results)}")

        total_images = sum(len(r.get("downloaded_images", [])) for r in results)
        print(f"   📸 Total images downloaded: {total_images}")

        if successful_results:
            print(f"\n📋 Downloaded Images:")
            for result in successful_results:
                transcript_name = os.path.basename(result["transcript_file"])
                print(f"   📄 {transcript_name}:")
                for img in result["downloaded_images"]:
                    print(f"      - {img['filename']} (image of {img['concept']})")

    except Exception as e:
        print(f"❌ Error in main function: {e}")


async def create_story_main(seconds_per_video: int = 5, enhance_images: bool = True):
    """Main function to create storyline from existing videos"""
    print("🎬 Storyline Creator from Existing Videos")
    print("=" * 50)

    # Check for OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set it using: export OPENAI_API_KEY=your_openai_key")
        return

    try:
        # Initialize the downloader/storyline creator
        downloader = TranscriptImageDownloader(openai_api_key=openai_key)

        # Create storyline from existing videos
        result = await downloader.create_story_from_videos(
            videos_dir="videos",
            seconds_per_video=seconds_per_video,
            enhance_with_additional_images=enhance_images,
        )

        if result.get("success"):
            print(f"\n✨ Storyline creation completed successfully!")
            print(f"📄 Check the storyline file: {result.get('storyline_file')}")
        else:
            print(f"\n❌ Storyline creation failed: {result.get('error')}")

    except Exception as e:
        print(f"❌ Error in storyline creation: {e}")


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing required dependencies...")

    required_packages = ["openai", "Pillow", "aiohttp", "requests"]

    for package in required_packages:
        try:
            __import__(package.lower().replace("-", "_"))
            print(f"✅ {package} is already installed")
        except ImportError:
            print(f"📦 Installing {package}...")
            os.system(f"pip install {package}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "install":
            install_dependencies()
        elif command == "story" or command == "storyline":
            # Parse additional arguments for story creation
            seconds_per_video = 5  # default
            enhance_images = True  # default

            # Parse optional arguments
            for i in range(2, len(sys.argv)):
                arg = sys.argv[i]
                if arg.startswith("--seconds="):
                    try:
                        seconds_per_video = int(arg.split("=")[1])
                    except (ValueError, IndexError):
                        print("⚠️ Invalid seconds value, using default (5)")
                elif arg == "--no-enhance":
                    enhance_images = False
                elif arg.startswith("--"):
                    print(f"⚠️ Unknown argument: {arg}")

            print(f"⚙️ Configuration:")
            print(f"   ⏱️ Seconds per video: {seconds_per_video}")
            print(f"   🎨 Enhance with additional images: {enhance_images}")
            print()

            asyncio.run(create_story_main(seconds_per_video, enhance_images))
        elif command == "transcripts":
            # Run original transcript processing
            print(f"\n🚀 Starting transcript processing...")
            asyncio.run(main())
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: 'install', 'story', 'transcripts'")
    else:
        # Default behavior: Run storyline creation with default settings
        print("🎬 Auto-running Storyline Creator with default settings")
        print("⚙️ Default Configuration:")
        print("   ⏱️ Seconds per video: 5")
        print("   🎨 Enhance with additional images: True")
        print("   📁 Output: stories/storyline.txt")
        print()
        print("💡 To customize settings, use:")
        print("   python 02_download_image_from_transcript.py story --seconds=10")
        print("   python 02_download_image_from_transcript.py story --no-enhance")
        print("   python 02_download_image_from_transcript.py transcripts")
        print()

        # Run storyline creation with default settings
        asyncio.run(create_story_main(seconds_per_video=5, enhance_images=True))
