# YouTube Video Upload Setup Guide

This guide will help you set up automatic video posting to YouTube using the `z006_post_to_youtube.py` script.

## Prerequisites

1. **Google Account**: You need a Google account with a YouTube channel
2. **Google Cloud Project**: Create a project in Google Cloud Console
3. **Python Environment**: Ensure you have Python 3.7+ installed

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click "Select a Project" → "New Project"
4. Enter project details:
   - **Project Name**: Choose a descriptive name (e.g., "YouTube Video Uploader")
   - **Organization**: Select if applicable
5. Click "Create"

## Step 2: Enable YouTube Data API v3

1. In your Google Cloud project, go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click on "YouTube Data API v3"
4. Click "Enable"
5. Wait for the API to be enabled

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - **User Type**: Choose "External" (unless you have a Google Workspace)
   - **App Name**: Enter your app name
   - **User support email**: Your email
   - **Developer contact information**: Your email
   - Click "Save and Continue"
   - **Scopes**: Skip this step for now
   - **Test users**: Add your own email address
   - Click "Save and Continue"

4. Create OAuth client ID:
   - **Application type**: "Desktop application"
   - **Name**: "YouTube Uploader Client"
   - Click "Create"

5. Download the credentials:
   - Click the download button (⬇️) next to your new OAuth client
   - Save the file as `client_secrets.json` in your project root directory

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Step 5: First Time Authentication

1. Make sure you have a video file starting with "final_video" in the `output/` directory
2. Run the script for the first time:
   ```bash
   python z006_post_to_youtube.py
   ```

3. The script will:
   - Open your default web browser
   - Redirect you to Google's OAuth consent screen
   - Ask you to sign in and authorize the application
   - Display a success message and redirect back

4. After authorization, a `youtube_token.pickle` file will be created to store your credentials for future use

## Step 6: Test the Upload

Once authenticated, the script will automatically:
- Find the latest video starting with "final_video"
- Upload it to your YouTube channel
- Set it to public by default
- Display the video URL

## Script Features

### 🔧 **Automatic Features**
- **Video Detection**: Finds the latest video starting with "final_video"
- **Resumable Upload**: Handles large files with automatic retry on failures
- **Progress Tracking**: Shows upload progress in real-time
- **Error Handling**: Comprehensive error handling with helpful messages
- **Token Management**: Automatic token refresh when expired

### 📊 **Video Metadata**
- **Auto-generated Title**: "AI Generated Video - YYYYMMDD_HHMMSS"
- **Rich Description**: Includes generation timestamp and file info
- **Smart Tags**: AI, Generated, Content, Technology, etc.
- **Category**: Science & Technology (automatically set)
- **Privacy**: Public by default (configurable)

### 📝 **Logging**
- Detailed logs saved to `logs/youtube_upload.log`
- Real-time console output with emojis
- Upload progress tracking

## Video Requirements

YouTube accepts various video formats with these requirements:

### **Supported Formats**
- MP4 (recommended)
- MOV, AVI, WMV, FLV, WebM
- MPEG-1, MPEG-2, MPEG-4

### **Technical Specifications**
- **Resolution**: Up to 4K (3840x2160)
- **Frame Rate**: Up to 60fps
- **File Size**: Up to 256GB or 12 hours (whichever comes first)
- **Aspect Ratio**: Any (16:9 recommended for best experience)

### **Recommended Settings**
- **Container**: MP4
- **Video Codec**: H.264
- **Audio Codec**: AAC
- **Resolution**: 1920x1080 (1080p)
- **Frame Rate**: 30fps or 60fps

## Advanced Usage

### Custom Upload Parameters

```python
from z006_post_to_youtube import YouTubeUploader

uploader = YouTubeUploader()

# Upload with custom metadata
result = uploader.upload_and_post(
    video_path="output/final_video_20241201.mp4",
    title="My Custom AI Video Title",
    description="Custom description with more details...",
    privacy="unlisted"  # or "private", "public"
)

if result['success']:
    print(f"✅ Video uploaded: {result['video_url']}")
else:
    print(f"❌ Upload failed: {result['error']}")
```

### Batch Upload Multiple Videos

```python
import glob
from z006_post_to_youtube import YouTubeUploader

uploader = YouTubeUploader()

# Upload all final_video files
pattern = "output/final_video*.mp4"
for video_path in glob.glob(pattern):
    result = uploader.upload_and_post(
        video_path=video_path,
        privacy="unlisted"  # Upload as unlisted first
    )
    print(f"Upload result for {video_path}: {result['success']}")
```

### Custom Video Metadata

```python
# Modify the create_video_metadata method for custom metadata
metadata = uploader.create_video_metadata(
    video_info,
    custom_title="My Amazing AI Video",
    custom_description="""
    🤖 This is my custom AI-generated video!
    
    ✨ Features:
    - AI-powered content generation
    - Automated voice synthesis
    - Dynamic visual effects
    
    #AI #MachineLearning #ContentCreation
    """
)
```

## Troubleshooting

### Common Issues

1. **"Client secrets file not found"**
   ```
   ❌ Error: Client secrets file not found: client_secrets.json
   ```
   - **Solution**: Download OAuth 2.0 credentials from Google Cloud Console
   - Save as `client_secrets.json` in project root

2. **"Quota exceeded"**
   ```
   ❌ Error: HTTP error: <HttpError 403 when requesting ... quotaExceeded>
   ```
   - **Solution**: YouTube API has daily upload quotas
   - Default quota allows ~6 videos per day
   - Request quota increase in Google Cloud Console if needed

3. **"Access blocked"**
   ```
   ❌ Error: This app is blocked
   ```
   - **Solution**: Your OAuth app needs verification for production use
   - For personal use, add your email to test users
   - For public use, submit for verification

4. **"Invalid credentials"**
   ```
   ❌ Error: Invalid credentials
   ```
   - **Solution**: Delete `youtube_token.pickle` and re-authenticate
   - Check that `client_secrets.json` is correct

5. **"Upload failed"**
   ```
   ❌ Error: Upload failed - HTTP 400
   ```
   - **Solution**: Check video file format and size
   - Ensure video meets YouTube requirements
   - Try with a smaller test video first

### OAuth Consent Screen Status

If you see "This app isn't verified":
- For **personal use**: Click "Advanced" → "Go to [App Name] (unsafe)"
- For **production**: Submit app for verification in Google Cloud Console

### API Quotas and Limits

YouTube Data API v3 has these limits:
- **Daily quota**: 10,000 units per day (default)
- **Video upload**: ~1,600 units per upload
- **Maximum uploads**: ~6 videos per day with default quota

To request quota increase:
1. Go to Google Cloud Console → APIs & Services → Quotas
2. Find "YouTube Data API v3"
3. Request increase with justification

## Security Best Practices

1. **Protect Credentials**
   - Never commit `client_secrets.json` to version control
   - Add to `.gitignore`: `client_secrets.json` and `youtube_token.pickle`
   - Store credentials securely in production

2. **Scope Limitation**
   - Script only requests `youtube.upload` scope (minimum required)
   - Does not access other Google services

3. **Token Management**
   - Tokens are stored locally in `youtube_token.pickle`
   - Tokens auto-refresh when expired
   - Delete token file to force re-authentication

## File Structure

After setup, your project should look like:

```
your-project/
├── z006_post_to_youtube.py      # Main upload script
├── client_secrets.json          # OAuth credentials (don't commit)
├── youtube_token.pickle         # Stored tokens (don't commit)
├── requirements.txt             # Dependencies
├── output/                      # Video files
│   └── final_video_*.mp4
├── logs/                        # Log files
│   └── youtube_upload.log
└── .gitignore                   # Git ignore file
```

## Production Deployment

For production environments:

1. **Environment Variables**
   ```python
   # Set credentials via environment
   import os
   client_secrets_path = os.getenv('GOOGLE_CLIENT_SECRETS_PATH')
   uploader = YouTubeUploader(client_secrets_path)
   ```

2. **Service Account** (for server environments)
   - Use service account instead of OAuth for automated uploads
   - Requires YouTube brand account delegation

3. **Error Monitoring**
   - Implement proper error tracking
   - Set up alerts for failed uploads
   - Monitor API quota usage

## Support Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube API Quotas](https://developers.google.com/youtube/v3/getting-started#quota)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)

## Example Output

When successful, you'll see:
```
🎬 Starting YouTube video upload process...
📹 Found latest video: output/final_video_with_voiceover_20250601_003404.mp4
📋 Preparing upload for: final_video_with_voiceover_20250601_003404.mp4 (5.2 MB)
📤 Starting upload of final_video_with_voiceover_20250601_003404.mp4
📊 Upload progress: 25%
📊 Upload progress: 50%
📊 Upload progress: 75%
✅ Video upload completed successfully

🎉 Success! Successfully uploaded final_video_with_voiceover_20250601_003404.mp4 to YouTube!
📹 Video: final_video_with_voiceover_20250601_003404.mp4
📊 Size: 5.2 MB
🆔 Video ID: dQw4w9WgXcQ
🔗 URL: https://youtube.com/watch?v=dQw4w9WgXcQ
👁️ Privacy: public
``` 