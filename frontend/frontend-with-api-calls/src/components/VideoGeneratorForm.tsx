import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Play, Upload, Wand2, Mic, Image, Video, X } from 'lucide-react';
import { toast } from 'sonner';
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";

interface VideoGeneratorFormProps {
  onGenerationStart: () => void;
  onProgressUpdate: (progress: number) => void;
  onGenerationComplete: (videoUrl: string) => void;
}

// First, let's add an interface for the Voice type
interface Voice {
  voice_id: string;
  name: string;
  category: string;
  description: string;
  preview_url: string;
}

// First, add the interface for the video generation request
interface VideoGenerationRequest {
  prompt: string;
  motion_bucket_id: number;
  cond_aug: number;
  steps: number;
  deep_cache: 'none' | string; // Add other possible values if any
  fps: number;
  negative_prompt: string;
  video_size: 'landscape_16_9' | string; // Add other possible sizes if any
}

// Add this constant near the top of the file, after the interfaces
const videoStyles = [
  { value: 'cinematic', label: 'Cinematic' },
  { value: 'natural', label: 'Natural' },
  { value: 'stylized', label: 'Stylized' },
  { value: 'animated', label: 'Animated' }
];

// Add interface for the AI video generation response
interface AIVideoGenerationResponse {
  success: boolean;
  message: string;
  data: {
    task_id: string;
    status: string;
    check_status_url: string;
  };
  error: string | null;
  timestamp: string;
}

// Add interface for transcript processing response
interface TranscriptProcessingResponse {
  success: boolean;
  message: string;
  data: {
    task_id: string;
    status: string;
    check_status_url: string;
  };
  error: string | null;
  timestamp: string;
}

// Add this interface for the ElevenLabs response
interface ElevenLabsResponse {
  conversation_id: string;
  transcript: string;
}

// Add interface for the storyline response
interface StorylineResponse {
  success: boolean;
  message: string;
  data: {
    task_id: string;
    status: string;
    check_status_url: string;
  };
  error: null | string;
  timestamp: string;
}

// Add storylineTaskId to the form data interface
interface FormData {
  title: string;
  script: string;
  voiceId: string;
  videoStyle: string;
  duration: string;
  aspectRatio: string;
  backgroundType: string;
  customBackground: File | null;
  motion_bucket_id: number;
  cond_aug: number;
  steps: number;
  deep_cache: 'none';
  fps: number;
  negative_prompt: string;
  storylineTaskId?: string;
  selectedVoiceId: string;
}

// Add this interface for the text-to-speech response
interface TextToSpeechResponse {
  success: boolean;
  message: string;
  data: {
    task_id: string;
    status: string;
    check_status_url: string;
  };
  error: null | string;
  timestamp: string;
}

// Add this interface with the other interfaces at the top of the file
interface TikTokUploadResponse {
  success: boolean;
  message: string;
  data: {
    task_id: string;
    status: string;
    check_status_url: string;
  };
  error: null | string;
  timestamp: string;
}

// Add interface for YouTube upload response
interface YouTubeUploadResponse {
  success: boolean;
  message: string;
  data: {
    task_id: string;
    status: string;
    check_status_url: string;
  };
  error: null | string;
  timestamp: string;
}

// Add these constants at the top of your file
const ELEVEN_LABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb";
const ELEVEN_LABS_MODEL_ID = "eleven_multilingual_v2";
const ELEVENLABS_AGENT_ID = "agent_01jwk4yynnemwsf3vr3kj9da45";

export const VideoGeneratorForm: React.FC<VideoGeneratorFormProps> = ({
  onGenerationStart,
  onProgressUpdate,
  onGenerationComplete
}) => {
  // State declarations
  const [formData, setFormData] = useState<FormData>({
    title: '',
    script: '',
    voiceId: '',
    videoStyle: 'cinematic',
    duration: '30',
    aspectRatio: '16:9',
    backgroundType: 'ai-generated',
    customBackground: null,
    motion_bucket_id: 127,
    cond_aug: 0.02,
    steps: 20,
    deep_cache: 'none' as const,
    fps: 10,
    negative_prompt: "unrealistic, saturated, high contrast, big nose, painting, drawing, sketch, cartoon, anime, manga, render, CG, 3d, watermark, signature, label",
    storylineTaskId: undefined,
    selectedVoiceId: '21m00Tcm4TlvDq8ikWAM'
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | null>(null);
  const [uploadedImages, setUploadedImages] = useState<File[]>([]);
  const [isPreviewExpanded, setIsPreviewExpanded] = useState(false);
  const [isCreatingStoryline, setIsCreatingStoryline] = useState(false);
  const [isTranscriptProcessed, setIsTranscriptProcessed] = useState(false);
  const [isTTSProcessing, setIsTTSProcessing] = useState(false);
  const [ttsTaskId, setTTSTaskId] = useState<string | null>(null);
  const [isUploadingToTikTok, setIsUploadingToTikTok] = useState(false);
  const [tiktokTaskId, setTiktokTaskId] = useState<string | null>(null);
  const [tiktokPrivacy, setTiktokPrivacy] = useState<'public' | 'private'>('public');
  const [isUploadingToYouTube, setIsUploadingToYouTube] = useState(false);
  const [youtubeTaskId, setYoutubeTaskId] = useState<string | null>(null);
  const [youtubePrivacy, setYoutubePrivacy] = useState<'public' | 'private'>('public');
  const [socialShareData, setSocialShareData] = useState({
    title: '',
    privacy: 'public' as 'public' | 'private'
  });

  const handleAudioTranscription = async (audioBlob: Blob) => {
    try {
      setIsTranscribing(true);
      
      // Convert audio blob to base64
      const base64Promise = new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          // Get the base64 string without the data URL prefix
          const base64 = reader.result?.toString().split(',')[1];
          resolve(base64);
        };
        reader.readAsDataURL(audioBlob);
      });

      const base64Audio = await base64Promise;

      // Send the request with the correct format
      const response = await fetch('http://0.0.0.0:8001/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({
          audio_data: base64Audio,
          agent_id: "agent_01jwk4yynnemwsf3vr3kj9da45",
          api_key: "sk_6048733473bdee5dc87d5f695a515374ecb7fbe4bf5bdfe7", // ElevenLabs API key from your Python code
          openai_api_key: "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",
          transcripts_dir: "session_transcripts"
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to process transcript: ${JSON.stringify(errorData)}`);
      }

      const result = await response.json();
      if (result.success) {
        setFormData(prev => ({
          ...prev,
          script: result.data?.text || ''
        }));
        setIsTranscriptProcessed(true);
        toast.success('Transcript processed successfully!');
      }
    } catch (error) {
      console.error('Transcription error:', error);
      toast.error('Failed to process transcript');
    } finally {
      setIsTranscribing(false);
    }
  };

  const startTextToSpeech = async () => {
    try {
      setIsTTSProcessing(true);
      
      const response = await fetch('http://0.0.0.0:8002/text-to-speech-pipeline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({
          storyline_path: "stories/storyline.txt",
          voice_id: ELEVEN_LABS_VOICE_ID,
          model_id: ELEVEN_LABS_MODEL_ID // Adding the model ID
        })
      });

      if (!response.ok) {
        throw new Error('Failed to start text-to-speech pipeline');
      }

      const result: TextToSpeechResponse = await response.json();
      
      if (result.success) {
        setTTSTaskId(result.data.task_id);
        toast.success('Text-to-speech conversion started');
      } else {
        throw new Error(result.error || 'Failed to start text-to-speech');
      }
    } catch (error) {
      console.error('Text-to-speech error:', error);
      toast.error('Failed to start text-to-speech conversion');
    } finally {
      setIsTTSProcessing(false);
    }
  };

  const createStoryline = async () => {
    try {
      setIsCreatingStoryline(true);
      toast.info('Creating storyline...');
      
      const response = await fetch('http://0.0.0.0:8002/create-storyline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({
          videos_dir: "videos",
          seconds_per_video: 5,
          enhance_with_additional_images: true
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create storyline');
      }

      const result: StorylineResponse = await response.json();
      
      if (result.success) {
        setFormData(prev => ({
          ...prev,
          storylineTaskId: result.data.task_id
        }));
        toast.success('Storyline creation started');
        
        // Start text-to-speech pipeline after storyline creation
        await startTextToSpeech();
      } else {
        throw new Error(result.error || 'Failed to create storyline');
      }
    } catch (error) {
      console.error('Storyline creation error:', error);
      toast.error('Failed to create storyline');
    } finally {
      setIsCreatingStoryline(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          sampleSize: 16
        }
      });
      
      // Check supported MIME types
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
      
      const recorder = new MediaRecorder(stream, {
        mimeType: mimeType,
        audioBitsPerSecond: 16000
      });
      
      const audioChunks: BlobPart[] = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: mimeType });
        await handleAudioTranscription(audioBlob);
      };

      recorder.start(1000); // Record in 1-second chunks
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      toast.error('Failed to start recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      const newImages = Array.from(files);
      setUploadedImages(prevImages => [...prevImages, ...newImages]);
    }
  };

  const handleGenerateVideo = async () => {
    try {
      // First API call: generate-video-user
      const userVideoResponse = await fetch('http://0.0.0.0:8002/generate-video-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({
          image_dir: "./user_images",
          pattern: "*.jpg",
          model: "fal-ai/veo2/image-to-video",
          prompt: "Generate a natural motion video",
          max_concurrent: 3
        })
      });

      if (!userVideoResponse.ok) {
        throw new Error('Failed to generate user video');
      }

      const userVideoResult = await userVideoResponse.json();
      toast.success('User video generation started');

      // Second API call: generate-video-ai
      const aiVideoResponse = await fetch('http://0.0.0.0:8002/generate-video-ai', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({
          image_dir: "./user_images",
          pattern: "*.jpg",
          model: "fal-ai/veo2/image-to-video",
          prompt: "Generate a natural motion video",
          max_concurrent: 3
        })
      });

      if (!aiVideoResponse.ok) {
        throw new Error('Failed to generate AI video');
      }

      const aiVideoResult = await aiVideoResponse.json();
      toast.success('AI video generation started');

    } catch (error) {
      console.error('Error generating video:', error);
      toast.error('Failed to generate video');
    }
  };

  const uploadToTikTok = async () => {
    try {
      setIsUploadingToTikTok(true);
      toast.info('Starting TikTok upload...');

      const response = await fetch('http://0.0.0.0:8002/upload-to-tiktok', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({
          video_path: "videos/final_video.mp4", // Path to the final video
          title: formData.title || "AI Generated Video",
          description: "Created with AI #aigenerated #video #ai",
          privacy: "public" // Added the privacy parameter
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to upload to TikTok: ${JSON.stringify(errorData)}`);
      }

      const result: TikTokUploadResponse = await response.json();
      
      if (result.success) {
        setTiktokTaskId(result.data.task_id);
        toast.success('TikTok upload started successfully!');
      } else {
        throw new Error(result.error || 'Failed to upload to TikTok');
      }
    } catch (error) {
      console.error('TikTok upload error:', error);
      toast.error('Failed to upload to TikTok');
    } finally {
      setIsUploadingToTikTok(false);
    }
  };

  const uploadToYouTube = async () => {
    try {
      setIsUploadingToYouTube(true);
      toast.info('Starting YouTube upload...');

      const response = await fetch('http://0.0.0.0:8002/upload-to-youtube', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'accept': 'application/json'
        },
        body: JSON.stringify({
          video_path: "videos/final_video.mp4",
          title: formData.title || "AI Generated Video",
          description: "Created with AI #aigenerated #video #ai",
          privacy: "public"
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to upload to YouTube: ${JSON.stringify(errorData)}`);
      }

      const result: YouTubeUploadResponse = await response.json();
      
      if (result.success) {
        setYoutubeTaskId(result.data.task_id);
        toast.success('YouTube upload started successfully!');
      } else {
        throw new Error(result.error || 'Failed to upload to YouTube');
      }
    } catch (error) {
      console.error('YouTube upload error:', error);
      toast.error('Failed to upload to YouTube');
    } finally {
      setIsUploadingToYouTube(false);
    }
  };

  // Return JSX
  return (
    <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wand2 className="w-5 h-5" />
          AI Video Generator
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="upload" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-white/10">
            <TabsTrigger value="upload" className="data-[state=active]:bg-white/20">
              <Upload className="w-4 h-4 mr-2" />
              Upload Images
            </TabsTrigger>
            <TabsTrigger value="record" className="data-[state=active]:bg-white/20">
              <Mic className="w-4 h-4 mr-2" />
              Record Voice
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="space-y-4">
            <div className="space-y-4">
              <Input
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageUpload}
                className="bg-white/5 border-white/20"
              />
              
              {uploadedImages.length > 0 && (
                <div className="space-y-4">
                  <Button 
                    onClick={handleGenerateVideo}
                    className="w-full bg-green-500 hover:bg-green-600"
                  >
                    Generate Video
                  </Button>
                  
                  <div className={`grid grid-cols-3 gap-4 ${isPreviewExpanded ? '' : 'max-h-40 overflow-hidden'}`}>
                    {uploadedImages.map((image, index) => (
                      <div key={index} className="relative">
                        <img
                          src={URL.createObjectURL(image)}
                          alt={`Preview ${index + 1}`}
                          className="w-full h-32 object-cover rounded-lg"
                        />
                        <Button
                          size="icon"
                          variant="destructive"
                          className="absolute top-1 right-1 h-6 w-6"
                          onClick={() => {
                            setUploadedImages(images => images.filter((_, i) => i !== index));
                          }}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                  
                  {uploadedImages.length > 6 && (
                    <Button
                      variant="ghost"
                      onClick={() => setIsPreviewExpanded(!isPreviewExpanded)}
                      className="w-full"
                    >
                      {isPreviewExpanded ? 'Show Less' : 'Show More'}
                    </Button>
                  )}
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="record" className="space-y-4">
            <div className="p-6 bg-white/5 rounded-lg border border-white/20 text-center">
              <div className="space-y-4">
                <div className="mx-auto w-20 h-20 bg-white/10 rounded-full flex items-center justify-center">
                  <Mic className={`w-10 h-10 ${isRecording ? 'text-red-500 animate-pulse' : 'text-white/70'}`} />
                </div>
                <div>
                  <h3 className="text-xl font-medium">
                    {isRecording ? 'Recording in Progress...' : 'Start Recording'}
                  </h3>
                  <p className="text-sm text-white/70 mt-2">
                    {isRecording 
                      ? 'Click stop when you are finished speaking' 
                      : 'Click the button below to start recording your voice'}
                  </p>
                </div>
                <Button 
                  className={`w-full ${isRecording ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'}`}
                  onClick={async () => {
                    if (!isRecording) {
                      try {
                        await startRecording();
                        toast.success("Recording started...");
                      } catch (error) {
                        toast.error("Failed to start recording. Please check your microphone permissions.");
                      }
                    } else {
                      stopRecording();
                    }
                  }}
                  disabled={isTranscribing}
                >
                  {isTranscribing ? (
                    <span className="animate-pulse">Transcribing...</span>
                  ) : isRecording ? (
                    <span className="animate-pulse">Stop Recording</span>
                  ) : (
                    <>
                      <Mic className="w-4 h-4 mr-2" />
                      Start Recording
                    </>
                  )}
                </Button>
              </div>
            </div>

            {isTranscriptProcessed && (
              <div className="mt-6 border-t border-white/10 pt-6">
                <div className="bg-white/5 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Wand2 className="w-5 h-5" />
                    Create Your Story
                  </h3>
                  
                  <div className="mb-4">
                    <Label>Processed Transcript</Label>
                    <Textarea
                      value={formData.script}
                      readOnly
                      className="mt-2 bg-white/10 border-white/20"
                      rows={4}
                    />
                  </div>

                  <Button
                    onClick={createStoryline}
                    disabled={isCreatingStoryline || !!formData.storylineTaskId}
                    className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                  >
                    {isCreatingStoryline ? (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin w-4 h-4 border-2 border-white/20 border-t-white rounded-full" />
                        <span>Creating Storyline...</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Wand2 className="w-4 h-4" />
                        <span>Create Storyline</span>
                      </div>
                    )}
                  </Button>

                  {formData.storylineTaskId && (
                    <div className="mt-4 p-4 bg-white/5 rounded-lg border border-white/20">
                      <div className="space-y-4">
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 rounded-full bg-green-500 animate-pulse" />
                          <span className="text-sm">
                            Storyline creation in progress...
                          </span>
                        </div>
                        
                        {ttsTaskId && (
                          <div className="flex items-center gap-2">
                            <div className="w-4 h-4 rounded-full bg-blue-500 animate-pulse" />
                            <span className="text-sm">
                              Converting text to speech...
                            </span>
                          </div>
                        )}
                        
                        <div className="text-xs text-white/70">
                          {formData.storylineTaskId && (
                            <div>Storyline Task ID: {formData.storylineTaskId}</div>
                          )}
                          {ttsTaskId && (
                            <div>TTS Task ID: {ttsTaskId}</div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>

        <div className="mt-6 border-t border-white/10 pt-6">
          <div className="bg-white/5 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Wand2 className="w-5 h-5" />
              Voice Selection
            </h3>
            
            <Select
              value={formData.selectedVoiceId}
              onValueChange={(value) => setFormData(prev => ({ ...prev, selectedVoiceId: value }))}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a voice" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="21m00Tcm4TlvDq8ikWAM">Josh</SelectItem>
                <SelectItem value="AZnzlk1XvdvUeBnXmlld">Rachel</SelectItem>
                <SelectItem value="EXAVITQu4vr4xnSDxMaL">Domi</SelectItem>
                {/* Add more voices as needed */}
              </SelectContent>
            </Select>
          </div>
        </div>

        {ttsTaskId && !isUploadingToTikTok && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center gap-4">
              <Label htmlFor="tiktok-title">TikTok Title</Label>
              <Input
                id="tiktok-title"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter video title"
                className="bg-white/5 border-white/20"
              />
            </div>
            
            <div className="flex items-center gap-4">
              <Label>Privacy Setting</Label>
              <Select
                value={tiktokPrivacy}
                onValueChange={(value: 'public' | 'private') => setTiktokPrivacy(value)}
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Select privacy" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="public">Public</SelectItem>
                  <SelectItem value="private">Private</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={uploadToTikTok}
              disabled={isUploadingToTikTok || !formData.title}
              className="w-full bg-black hover:bg-gray-900 flex items-center justify-center gap-2"
            >
              {isUploadingToTikTok ? (
                <>
                  <div className="animate-spin w-4 h-4 border-2 border-white/20 border-t-white rounded-full" />
                  <span>Uploading to TikTok...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 015.2-2.32V9.4a8.66 8.66 0 005.64 2.18V8.73a5.81 5.81 0 01-3.77-1.39 5.81 5.81 0 013.77-1.39v-.72a4.83 4.83 0 013.77 4.25v2.83a8.66 8.66 0 01-5.64-2.18v5.6a6.35 6.35 0 11-6.35-6.35" />
                  </svg>
                  <span>Share on TikTok</span>
                </>
              )}
            </Button>
          </div>
        )}

        {ttsTaskId && !isUploadingToYouTube && (
          <div className="mt-4 space-y-4">
            <div className="flex items-center gap-4">
              <Label htmlFor="youtube-title">YouTube Title</Label>
              <Input
                id="youtube-title"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter video title"
                className="bg-white/5 border-white/20"
              />
            </div>
            
            <div className="flex items-center gap-4">
              <Label>Privacy Setting</Label>
              <Select
                value={youtubePrivacy}
                onValueChange={(value: 'public' | 'private') => setYoutubePrivacy(value)}
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Select privacy" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="public">Public</SelectItem>
                  <SelectItem value="private">Private</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={uploadToYouTube}
              disabled={isUploadingToYouTube || !formData.title}
              className="w-full bg-red-600 hover:bg-red-700 flex items-center justify-center gap-2"
            >
              {isUploadingToYouTube ? (
                <>
                  <div className="animate-spin w-4 h-4 border-2 border-white/20 border-t-white rounded-full" />
                  <span>Uploading to YouTube...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                  </svg>
                  <span>Share on YouTube</span>
                </>
              )}
            </Button>
          </div>
        )}

        {youtubeTaskId && (
          <div className="mt-4 p-4 bg-white/5 rounded-lg border border-white/20">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-red-500 animate-pulse" />
              <span className="text-sm">
                Uploading to YouTube...
              </span>
            </div>
            <div className="text-xs text-white/70 mt-2">
              Task ID: {youtubeTaskId}
            </div>
          </div>
        )}

        {ttsTaskId && (
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Share on TikTok</h3>
              {/* TikTok upload UI */}
              {/* ... existing TikTok upload code ... */}
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Share on YouTube</h3>
              {/* YouTube upload UI */}
              {/* ... YouTube upload code from above ... */}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
