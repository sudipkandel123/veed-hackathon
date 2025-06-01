# 🎙️ ElevenLabs Text-to-Speech Usage Examples

This guide shows you exactly how to use the `006_elevenlabs_text_to_voice.py` script to create professional voiceovers for your videos.

## 🚀 Quick Start

### 1. Set Your API Key

First, set your ElevenLabs API key as an environment variable:

```bash
export ELEVENLABS_API_KEY="your_api_key_here"
```

Or create a `.env` file:
```env
ELEVENLABS_API_KEY=your_api_key_here
```

### 2. Basic Usage

The simplest way to run the script:

```bash
python3 006_elevenlabs_text_to_voice.py
```

This will:
- Read storyline from `stories/storyline.txt`
- Use the default George voice
- Merge all videos from `videos/` folder
- Create final video in `output/` folder

## 🎭 Voice Options

### Popular Voice IDs

Try different voices by using the `--voice-id` parameter:

```bash
# Male Voices
python3 006_elevenlabs_text_to_voice.py --voice-id "JBFqnCBsd6RMkjVDRZzb"  # George (default)
python3 006_elevenlabs_text_to_voice.py --voice-id "AZnzlk1XvdvUeBnXmlld"  # Domi (energetic)
python3 006_elevenlabs_text_to_voice.py --voice-id "1SM7GgM6IMuvQlz2BwM3"  # Mark (relaxed)

# Female Voices  
python3 006_elevenlabs_text_to_voice.py --voice-id "21m00Tcm4TlvDq8ikWAM"  # Rachel (professional)
python3 006_elevenlabs_text_to_voice.py --voice-id "EXAVITQu4vr4xnSDxMaL"  # Bella (young)
python3 006_elevenlabs_text_to_voice.py --voice-id "dj3G1R1ilKoFKhBnWOzG"  # Eryn (friendly)

# Character Voices
python3 006_elevenlabs_text_to_voice.py --voice-id "kdmDKE6EkgrWrrykO9Qt"  # Alexandra (chatty)
python3 006_elevenlabs_text_to_voice.py --voice-id "OYTbf65OHHFELVut7v2H"  # Hope (uplifting)
```

### Voice Characteristics

| Voice ID | Name | Gender | Style | Best For |
|----------|------|--------|-------|----------|
| `JBFqnCBsd6RMkjVDRZzb` | George | Male | Natural, clear | General narration |
| `21m00Tcm4TlvDq8ikWAM` | Rachel | Female | Professional | Corporate content |
| `AZnzlk1XvdvUeBnXmlld` | Domi | Male | Energetic | YouTube content |
| `EXAVITQu4vr4xnSDxMaL` | Bella | Female | Young, modern | Social media |
| `kdmDKE6EkgrWrrykO9Qt` | Alexandra | Female | Conversational | Tutorials |
| `OYTbf65OHHFELVut7v2H` | Hope | Female | Uplifting | Motivational |

## 📝 Custom Storylines

### Using Custom Files

```bash
# Use a different storyline file
python3 006_elevenlabs_text_to_voice.py --storyline "my_custom_story.txt"

# Use a file from a different location
python3 006_elevenlabs_text_to_voice.py --storyline "/path/to/my/storyline.txt"
```

### Creating Your Own Storyline

Create a text file with your voiceover script:

```text
# Example: travel_story.txt
Welcome to the most incredible journey through London! 
First, we're exploring the stunning Greenwich Park with its rolling green hills.
Next, we dive underground into the bustling Bank Station.
Finally, we witness the majestic Big Ben in all its glory!
Don't forget to like and subscribe for more amazing travel content!
```

Then use it:
```bash
python3 006_elevenlabs_text_to_voice.py --storyline "travel_story.txt" --voice-id "21m00Tcm4TlvDq8ikWAM"
```

## 🎬 Complete Workflow Examples

### Example 1: Travel Vlog

```bash
# Step 1: Generate storyline (if you haven't already)
python3 02_download_image_from_transcript.py --seconds-per-video 6 --style "travel vlog"

# Step 2: Create video with energetic voice
python3 006_elevenlabs_text_to_voice.py --voice-id "AZnzlk1XvdvUeBnXmlld"
```

### Example 2: Educational Content

```bash
# Step 1: Generate educational storyline
python3 02_download_image_from_transcript.py --seconds-per-video 8 --style "educational"

# Step 2: Use professional female voice
python3 006_elevenlabs_text_to_voice.py --voice-id "21m00Tcm4TlvDq8ikWAM"
```

### Example 3: Entertainment/Social Media

```bash
# Step 1: Generate upbeat storyline
python3 02_download_image_from_transcript.py --seconds-per-video 4 --style "viral TikTok"

# Step 2: Use young, energetic voice
python3 006_elevenlabs_text_to_voice.py --voice-id "EXAVITQu4vr4xnSDxMaL"
```

## 🔧 Advanced Options

### Combining All Parameters

```bash
python3 006_elevenlabs_text_to_voice.py \
    --storyline "stories/my_story.txt" \
    --voice-id "21m00Tcm4TlvDq8ikWAM" \
    --api-key "your_api_key_if_not_in_env"
```

### Testing Different Voices

Create a script to test multiple voices:

```bash
#!/bin/bash
# test_voices.sh

voices=(
    "JBFqnCBsd6RMkjVDRZzb"  # George
    "21m00Tcm4TlvDq8ikWAM"  # Rachel  
    "AZnzlk1XvdvUeBnXmlld"  # Domi
)

for voice in "${voices[@]}"; do
    echo "Testing voice: $voice"
    python3 006_elevenlabs_text_to_voice.py --voice-id "$voice"
    echo "Completed voice: $voice"
    echo "---"
done
```

## 📊 Output Information

The script will provide detailed information during processing:

```
INFO - Starting complete ElevenLabs video processing pipeline...
INFO - Step 1: Reading storyline...
INFO - Successfully read storyline (442 characters)
INFO - Step 2: Converting text to speech...
INFO - Using voice ID: JBFqnCBsd6RMkjVDRZzb
INFO - Using model: eleven_multilingual_v2
INFO - Audio generated successfully: audio/voiceover.mp3
INFO - Step 3: Processing videos...
INFO - Found 4 video files:
INFO   1. 20250531_224244_Greenwich_Park_1.mp4
INFO   2. 20250531_221924_Big_Ben_2.mp4
INFO   3. 20250531_224246_Big_Ben_3.mp4
INFO   4. 20250531_224247_Bank_Station_4.mp4
INFO - Videos merged successfully: output/merged_video.mp4 (20.50s)
INFO - Step 4: Combining audio and video...
INFO - Final video created: output/final_video_with_voiceover_20250101_123456.mp4 (20.50s)
INFO - ✅ Pipeline completed successfully!
INFO - 📁 Final output: output/final_video_with_voiceover_20250101_123456.mp4

🎉 SUCCESS! Your video with voiceover is ready:
📁 File: output/final_video_with_voiceover_20250101_123456.mp4
📏 Size: 15.2 MB
```

## 🚨 Troubleshooting

### Common Issues

**API Key Error:**
```bash
# Make sure your API key is set
echo $ELEVENLABS_API_KEY
```

**No Videos Found:**
```bash
# Check if videos exist
ls -la videos/
```

**FFmpeg Missing:**
```bash
# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

**Permission Issues:**
```bash
# Make script executable
chmod +x 006_elevenlabs_text_to_voice.py
```

## 💡 Tips for Best Results

1. **Voice Selection**: Match voice personality to content style
2. **Storyline Length**: Keep it concise for better engagement
3. **Video Quality**: Use high-quality source videos for best results
4. **Audio Settings**: The script uses optimized settings for clarity
5. **File Organization**: Keep videos in chronological order for smooth flow

## 🎯 Next Steps

After creating your video:

1. **Review Output**: Check the final video quality
2. **Social Media**: Share on YouTube, TikTok, Instagram
3. **Optimization**: Try different voices for different content types
4. **Automation**: Create batch scripts for multiple videos

---

**Need Help?** Check the main README.md or create an issue if you encounter problems! 