# TikTok Video Upload Setup Guide

This guide will help you set up automatic video posting to TikTok using the `z005_post_to_tiktok.py` script.

## Prerequisites

1. **TikTok Business Account**: You need a TikTok Business account to access the API
2. **TikTok Developer Account**: Register at [TikTok Developers](https://developers.tiktok.com/)
3. **Python Environment**: Ensure you have Python 3.7+ installed

## Step 1: Create a TikTok Developer App

1. Go to [TikTok Developers](https://developers.tiktok.com/)
2. Sign in with your TikTok Business account
3. Click "Manage Apps" → "Create an App"
4. Fill in your app details:
   - **App Name**: Choose a descriptive name
   - **App Description**: Describe your video automation use case
   - **Category**: Select appropriate category (e.g., "Content & Publishing")
5. After creation, note down your:
   - **Client Key** (App ID)
   - **Client Secret**

## Step 2: Configure API Permissions

1. In your app dashboard, go to "Products"
2. Add the following products:
   - **Video Kit** (for video uploading)
   - **Login Kit** (for authentication)
3. Configure scopes:
   - `video.upload` - Required for uploading videos
   - `user.info.basic` - Basic user information

## Step 3: Get Access Token

### Option A: Manual OAuth Flow (Recommended for Testing)

1. Generate authorization URL:

   ```
   https://www.tiktok.com/auth/authorize/?client_key=YOUR_CLIENT_KEY&scope=video.upload,user.info.basic&response_type=code&redirect_uri=YOUR_REDIRECT_URI&state=state
   ```
2. After user authorization, exchange the code for access token:

   ```bash
   curl -X POST "https://open.tiktokapis.com/v2/oauth/token/" \
   -H "Content-Type: application/x-www-form-urlencoded" \
   -d "client_key=YOUR_CLIENT_KEY&client_secret=YOUR_CLIENT_SECRET&code=AUTHORIZATION_CODE&grant_type=authorization_code&redirect_uri=YOUR_REDIRECT_URI"
   ```

### Option B: Use TikTok's Postman Collection

TikTok provides a Postman collection that can help you obtain tokens more easily.

## Step 4: Create Environment File

1. Create a `.env` file in your project root:

   ```bash
   touch .env
   ```
2. Add your credentials to the `.env` file:

   ```env
   # TikTok API Configuration
   TIKTOK_CLIENT_KEY=your_client_key_here
   TIKTOK_CLIENT_SECRET=your_client_secret_here
   TIKTOK_ACCESS_TOKEN=your_access_token_here
   ```

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 6: Test the Script

1. Make sure you have a video file starting with "final_video" in the `output/` directory
2. Run the script:
   ```bash
   python z005_post_to_tiktok.py
   ```

## Script Features

- **Automatic Video Detection**: Finds the latest video starting with "final_video" in the output folder
- **Smart Upload**: Handles large video files with chunked uploads
- **Error Handling**: Comprehensive error handling with helpful messages
- **Logging**: Detailed logs saved to `logs/tiktok_upload.log`
- **Status Tracking**: Tracks upload progress and final publish status

## Video Requirements

TikTok has specific requirements for uploaded videos:

- **Format**: MP4, MOV, MPEG, 3GPP, WEBM
- **Resolution**:
  - Minimum: 540x960 (9:16 aspect ratio recommended)
  - Maximum: 1080x1920
- **Duration**: 15 seconds to 10 minutes
- **File Size**: Maximum 4GB
- **Frame Rate**: 23-60 FPS

## Troubleshooting

### Common Issues

1. **"Missing TikTok API credentials"**

   - Ensure your `.env` file exists and contains all required credentials
   - Check that credential names match exactly
2. **"No final_video found"**

   - Verify you have a video file starting with "final_video" in the `output/` directory
   - Check file permissions
3. **"Failed to initialize upload session"**

   - Verify your access token is valid and not expired
   - Check that your app has the correct permissions
   - Ensure your video meets TikTok's requirements
4. **"Failed to upload video file"**

   - Check your internet connection
   - Verify the video file isn't corrupted
   - Try with a smaller video file first

### Rate Limits

TikTok API has rate limits:

- **Video Upload**: 100 videos per day per user
- **API Calls**: 1000 requests per hour per app

### Token Refresh

Access tokens typically expire after some time. You may need to:

1. Implement token refresh logic using the refresh token
2. Re-authenticate users when tokens expire

## Advanced Configuration

### Custom Video Metadata

You can modify the script to customize:

- Video title and description
- Hashtags
- Privacy settings (comments, duets, stitches)
- Cover image timestamp

### Batch Upload

To upload multiple videos, modify the script to loop through multiple files:

```python
# Example: Upload all final_video files
pattern = "output/final_video*.mp4"
for video_path in glob.glob(pattern):
    result = uploader.upload_and_post(video_path)
    print(f"Upload result for {video_path}: {result}")
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use environment variables** in production
3. **Rotate credentials regularly**
4. **Monitor API usage** to detect unauthorized access
5. **Use HTTPS** for all API calls (handled automatically by the script)

## Support

- [TikTok Developer Documentation](https://developers.tiktok.com/doc/)
- [TikTok API Status](https://developers.tiktok.com/doc/api-status/)
- [TikTok Community Forum](https://developers.tiktok.com/community/)

## Example Usage

```python
from z005_post_to_tiktok import TikTokUploader

# Initialize uploader
uploader = TikTokUploader()

# Upload specific video
result = uploader.upload_and_post("output/final_video_20241201.mp4")

# Upload latest video (automatic detection)
result = uploader.upload_and_post()

if result['success']:
    print(f"✅ Video uploaded successfully!")
    print(f"Publish ID: {result['publish_id']}")
else:
    print(f"❌ Upload failed: {result['error']}")
```
