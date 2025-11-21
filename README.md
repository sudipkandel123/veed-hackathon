# 🎬 AI-Powered YouTube Short Creator

Create engaging YouTube Shorts automatically by combining multiple videos with AI-generated storylines and narration.

## ✨ Features

- 🤖 **AI Storyline Generation**: Uses OpenAI GPT-4 to create compelling narratives from video metadata
- 🎙️ **Professional Narration**: ElevenLabs AI voice synthesis for high-quality audio
- 📱 **YouTube Shorts Format**: Automatically formats videos for 9:16 aspect ratio (1080x1920)
- 📝 **Dynamic Subtitles**: Generates and overlays subtitles synchronized with narration
- 🎞️ **Multi-Video Composition**: Seamlessly combines multiple video clips
- ⚡ **Smart Speed Adjustment**: Automatically adjusts video speed to fit target duration
- 🔄 **Complete Pipeline**: End-to-end processing from storyline creation to final video with voiceover

## 🚀 Quick Start

### 1. Setup

```bash
# Clone or download the project
# Install dependencies and setup environment
python setup.py
```

### 2. Configure API Keys

Add your API keys to the `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

**Get your API keys:**
- OpenAI: https://platform.openai.com/api-keys
- ElevenLabs: https://elevenlabs.io/

### 3. Choose Your Workflow

#### Option A: Complete Pipeline (Recommended)
```bash
# Step 1: Generate storyline from existing images/videos
python 02_download_image_from_transcript.py

# Step 2: Create video with ElevenLabs voiceover
python 006_elevenlabs_text_to_voice.py
```

#### Option B: Advanced Custom Workflow
```bash
# Use the subtitle-based approach
python combine_multiple_video_with_subtitle.py
```

### 4. Prepare Video Metadata

Update `video.json` with your video information:

```json
{
  "videos": [
    {
      "id": 1,
      "file_path": "videos/your_video1.mp4",
      "title": "Scene Title",
      "description": "What happens in this video segment",
      "duration": 5.2,
      "content_tags": ["tag1", "tag2"],
      "mood": "energetic",
      "key_moments": "Description of key visual elements"
    }
  ],
  "project_info": {
    "theme": "Your video theme",
    "target_duration": 15,
    "style": "fast-paced YouTube short",
    "target_audience": "your target audience"
  }
}
```

### 5. Create Your YouTube Short

```bash
python combine_multiple_video_with_subtitle.py
```

The generated video will be saved in the `output/` directory.

## 📋 Requirements

### System Requirements
- Python 3.8+
- FFmpeg (for video processing)

### Python Packages
- openai>=1.3.0
- elevenlabs>=0.2.26
- moviepy>=1.0.3
- python-dotenv>=0.19.0

### API Accounts
- OpenAI API account (for storyline generation)
- ElevenLabs API account (for voice synthesis)

## 🔧 Installation

### Option 1: Automatic Setup
```bash
python setup.py
```

### Option 2: Manual Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install FFmpeg
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
sudo apt install ffmpeg

# Create .env file and add your API keys
cp .env.example .env
# Edit .env with your actual API keys
```

## 📖 How It Works

### Complete Pipeline (Recommended)

1. **Image Analysis & Storyline Creation** (`02_download_image_from_transcript.py`):
   - Analyzes existing images/videos in your folders
   - Uses OpenAI GPT-4 to create YouTube Shorts-optimized storylines
   - Downloads additional contextual images if needed
   - Saves clean voiceover script to `stories/storyline.txt`

2. **Text-to-Speech & Video Assembly** (`006_elevenlabs_text_to_voice.py`):
   - Reads storyline from `stories/storyline.txt`
   - Converts text to high-quality audio using ElevenLabs
   - Merges all videos from the `videos/` folder
   - Combines audio and video into final output

### Legacy Subtitle Workflow

1. **Metadata Loading**: Reads video information from `video.json`
2. **Storyline Generation**: Uses OpenAI GPT-4 to create a compelling narrative
3. **Voice Synthesis**: Generates narration audio using ElevenLabs
4. **Video Processing**: 
   - Combines multiple video clips
   - Adjusts speed to fit target duration
   - Resizes to YouTube Shorts format (9:16)
5. **Subtitle Generation**: Creates and overlays dynamic subtitles
6. **Final Composition**: Combines video, audio, and subtitles

## 🎯 Script Usage

### ElevenLabs Text-to-Speech Pipeline

The main processing script with multiple options:

```bash
# Basic usage (uses default settings)
python 006_elevenlabs_text_to_voice.py

# Custom storyline file
python 006_elevenlabs_text_to_voice.py --storyline "my_custom_story.txt"

# Custom voice (use ElevenLabs voice ID)
python 006_elevenlabs_text_to_voice.py --voice-id "21m00Tcm4TlvDq8ikWAM"

# Specify API key directly
python 006_elevenlabs_text_to_voice.py --api-key "your_elevenlabs_api_key"
```

**Available ElevenLabs Voices:**
- `JBFqnCBsd6RMkjVDRZzb` - George (default, natural male voice)
- `21m00Tcm4TlvDq8ikWAM` - Rachel (female voice)
- `AZnzlk1XvdvUeBnXmlld` - Domi (energetic male voice)
- `EXAVITQu4vr4xnSDxMaL` - Bella (young female voice)

### Storyline Generation

Create AI-generated storylines from your content:

```bash
# Auto-run with default settings (5 seconds per video, enhance images)
python 02_download_image_from_transcript.py

# Custom duration per video
python 02_download_image_from_transcript.py --seconds-per-video 8

# Disable additional image downloads
python 02_download_image_from_transcript.py --enhance-images false

# Custom target style
python 02_download_image_from_transcript.py --style "educational"
```

## 🎯 Customization

### Voice Settings
Modify the voice settings in the script:
```python
voice=Voice(
    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
    settings=VoiceSettings(
        stability=0.75,
        similarity_boost=0.75,
        style=0.5,
        use_speaker_boost=True
    )
)
```

### Video Output Settings
Adjust video quality and format:
```python
final_composition.write_videofile(
    output_path,
    codec='libx264',
    audio_codec='aac',
    fps=24,
    bitrate="8000k"
)
```

### Subtitle Styling
Customize subtitle appearance:
```python
TextClip(
    text,
    fontsize=24,
    color='white',
    font='Arial-Bold',
    stroke_color='black',
    stroke_width=2
)
```

## 📁 Project Structure

```
├── 006_elevenlabs_text_to_voice.py         # Main ElevenLabs TTS + Video pipeline
├── 02_download_image_from_transcript.py    # Storyline generation script
├── combine_multiple_video_with_subtitle.py # Legacy subtitle-based script
├── video.json                              # Video metadata (for legacy workflow)
├── requirements.txt                        # Python dependencies
├── setup.py                               # Setup script
├── .env                                   # API keys (create this)
├── videos/                                # Input video files
├── images/                                # Input image files  
├── stories/                               # Generated storylines
│   └── storyline.txt                      # Clean voiceover script
├── audio/                                 # Generated audio files
├── output/                                # Final video outputs
└── logs/                                  # Processing logs
```

## 🐛 Troubleshooting

### Common Issues

**FFmpeg not found:**
```bash
# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

**API Key errors:**
- Ensure your API keys are correctly set in `.env`
- Check that your OpenAI/ElevenLabs accounts have sufficient credits

**Video file not found:**
- Verify video file paths in `video.json`
- Ensure video files exist in the specified locations

**Memory issues with large videos:**
- Use smaller video files or reduce video quality
- Close other applications to free up memory

## 🎨 Example Outputs

The script generates:
- High-quality YouTube Shorts (1080x1920)
- Synchronized narration and subtitles
- Smooth transitions between video segments
- Professional-looking final composition

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 🆘 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Ensure all requirements are installed
3. Verify your API keys are valid
4. Check the console output for specific error messages
