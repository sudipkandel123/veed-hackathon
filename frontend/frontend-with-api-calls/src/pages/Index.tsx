import React, { useState } from 'react';
import { VideoGeneratorForm } from '@/components/VideoGeneratorForm';
import { GenerationProgress } from '@/components/GenerationProgress';
import { VideoPreview } from '@/components/VideoPreview';
import { ApiKeyManager } from '@/components/ApiKeyManager'; // this is for the api keys
import { VideoBackground } from '@/components/VideoBackground';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Sparkles, Video, Mic, Image, Scissors, Palette, LogOut } from 'lucide-react';

const Index = () => {
  const { user, signOut } = useAuth();
  const [currentStep, setCurrentStep] = useState<'setup' | 'generating' | 'preview'>('setup');
  const [generatedVideo, setGeneratedVideo] = useState<string | null>(null);
  const [generationProgress, setGenerationProgress] = useState(0);

  const handleGenerationStart = () => {
    setCurrentStep('generating');
    setGenerationProgress(0);
  };

  const handleGenerationComplete = (videoUrl: string) => {
    setGeneratedVideo(videoUrl);
    setCurrentStep('preview');
  };

  const handleReset = () => {
    setCurrentStep('setup');
    setGeneratedVideo(null);
    setGenerationProgress(0);
  };

  return (
    <div className="min-h-screen relative">
      <VideoBackground />
      
      {/* Header */}
      <div className="relative z-10 pt-12 pb-8">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-start mb-6">
            <div className="text-center flex-1">
              <div className="flex items-center justify-center gap-3 mb-6">
                <div className="p-3 bg-white/10 backdrop-blur-sm rounded-2xl">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <h1 className="text-5xl font-bold text-white bg-gradient-to-r from-white via-purple-200 to-cyan-200 bg-clip-text text-transparent">
                How my day was?
                </h1>
              </div>
              <p className="text-xl text-white/80 max-w-2xl mx-auto leading-relaxed">
               Record how your day was and we will generate a video of your day
              </p>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-white/70 text-sm">
                Welcome, {user?.email}
              </span>
              <Button
                onClick={signOut}
                variant="ghost"
                size="sm"
                className="text-white/70 hover:text-white hover:bg-white/10"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>ƒ

          {/* Feature Pills  - the api's are commented out for now*/}
          {/* <div className="flex flex-wrap justify-center gap-4 mt-8">
            {[
              { icon: Mic, label: 'ElevenLabs Voice' },
              { icon: Image, label: 'Fal.ai Generation' },
              { icon: Scissors, label: 'Veed Editing' },
              { icon: Video, label: 'Sieve Processing' },
              { icon: Palette, label: 'PhotoRoom AI' }
            ].map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-white/90 text-sm font-medium">
                <Icon className="w-4 h-4" />
                {label}
              </div>
            ))}
          </div> */}
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 container mx-auto px-4 pb-12">
        <div className="max-w-4xl mx-auto">
          {currentStep === 'setup' && (
            <div className="space-y-8">
              {/* <ApiKeyManager /> */}
              <VideoGeneratorForm 
                onGenerationStart={handleGenerationStart}
                onProgressUpdate={setGenerationProgress}
                onGenerationComplete={handleGenerationComplete}
              />
            </div>
          )}
          
          {currentStep === 'generating' && (
            <GenerationProgress 
              progress={generationProgress}
              onCancel={handleReset}
            />
          )}
          
          {currentStep === 'preview' && generatedVideo && (
            <VideoPreview 
              videoUrl={generatedVideo}
              onReset={handleReset}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Index;
