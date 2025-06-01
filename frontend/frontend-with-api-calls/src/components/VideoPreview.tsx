
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, Share2, RotateCcw, Play, Pause, Volume2, VolumeX, Maximize } from 'lucide-react';
import { toast } from 'sonner';

interface VideoPreviewProps {
  videoUrl: string;
  onReset: () => void;
}

export const VideoPreview: React.FC<VideoPreviewProps> = ({
  videoUrl,
  onReset
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = videoUrl;
    link.download = 'ai-generated-video.mp4';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Download started!');
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'My AI Generated Video',
          text: 'Check out this video I created with AI!',
          url: videoUrl
        });
      } catch (error) {
        console.log('Share failed:', error);
      }
    } else {
      // Fallback to copying URL
      navigator.clipboard.writeText(videoUrl);
      toast.success('Video URL copied to clipboard!');
    }
  };

  const togglePlay = () => {
    const video = document.getElementById('preview-video') as HTMLVideoElement;
    if (video) {
      if (isPlaying) {
        video.pause();
      } else {
        video.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    const video = document.getElementById('preview-video') as HTMLVideoElement;
    if (video) {
      video.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const toggleFullscreen = () => {
    const video = document.getElementById('preview-video') as HTMLVideoElement;
    if (video) {
      if (!isFullscreen) {
        video.requestFullscreen();
      } else {
        document.exitFullscreen();
      }
      setIsFullscreen(!isFullscreen);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Your AI Generated Video</span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onReset}
                className="bg-white/10 border-white/20 text-white hover:bg-white/20"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Create New
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Video Player */}
          <div className="relative bg-black rounded-lg overflow-hidden group">
            <video
              id="preview-video"
              src={videoUrl}
              className="w-full h-auto"
              controls={false}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onLoadedMetadata={() => {
                // Auto-play on load
                const video = document.getElementById('preview-video') as HTMLVideoElement;
                if (video) {
                  video.play();
                  setIsPlaying(true);
                }
              }}
            />
            
            {/* Custom Controls Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <div className="absolute bottom-4 left-4 right-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={togglePlay}
                      className="bg-black/50 hover:bg-black/70 text-white"
                    >
                      {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={toggleMute}
                      className="bg-black/50 hover:bg-black/70 text-white"
                    >
                      {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                    </Button>
                  </div>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleFullscreen}
                    className="bg-black/50 hover:bg-black/70 text-white"
                  >
                    <Maximize className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 mt-6">
            <Button
              onClick={handleDownload}
              className="flex-1 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Video
            </Button>
            
            <Button
              onClick={handleShare}
              variant="outline"
              className="flex-1 bg-white/10 border-white/20 text-white hover:bg-white/20"
            >
              <Share2 className="w-4 h-4 mr-2" />
              Share Video
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Video Details */}
      <Card className="bg-white/5 backdrop-blur-sm border-white/10 text-white">
        <CardContent className="pt-6">
          <h3 className="font-medium mb-4 text-purple-400">Generation Details</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-white/60">Resolution</p>
              <p className="font-medium">1920x1080</p>
            </div>
            <div>
              <p className="text-white/60">Duration</p>
              <p className="font-medium">30 seconds</p>
            </div>
            <div>
              <p className="text-white/60">Format</p>
              <p className="font-medium">MP4</p>
            </div>
            <div>
              <p className="text-white/60">Quality</p>
              <p className="font-medium">HD</p>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-gradient-to-r from-purple-500/20 to-cyan-500/20 rounded-lg border border-purple-500/30">
            <h4 className="font-medium mb-2">🎉 Video Generated Successfully!</h4>
            <p className="text-sm text-white/80">
              Your video has been created using cutting-edge AI technology. Each frame was carefully 
              crafted to match your script and style preferences.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
