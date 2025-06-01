
import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { X, Loader2, Mic, Image, Video, Scissors, Palette } from 'lucide-react';

interface GenerationProgressProps {
  progress: number;
  onCancel: () => void;
}

export const GenerationProgress: React.FC<GenerationProgressProps> = ({
  progress,
  onCancel
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const steps = [
    {
      icon: Mic,
      title: 'Voice Generation',
      description: 'Converting text to speech with ElevenLabs AI',
      duration: 'Estimated 15-30 seconds'
    },
    {
      icon: Image,
      title: 'Visual Creation',
      description: 'Generating images and animations with Fal.ai',
      duration: 'Estimated 30-60 seconds'
    },
    {
      icon: Palette,
      title: 'Background Processing',
      description: 'Enhancing visuals with PhotoRoom AI',
      duration: 'Estimated 20-40 seconds'
    },
    {
      icon: Scissors,
      title: 'Video Editing',
      description: 'Compositing and editing with Veed.io',
      duration: 'Estimated 40-80 seconds'
    },
    {
      icon: Video,
      title: 'Final Processing',
      description: 'Optimizing and finalizing with Sieve',
      duration: 'Estimated 10-20 seconds'
    }
  ];

  useEffect(() => {
    const stepIndex = Math.floor(progress / 20);
    setCurrentStep(stepIndex);
    
    // Mark completed steps
    const completed = [];
    for (let i = 0; i < stepIndex; i++) {
      completed.push(i);
    }
    setCompletedSteps(completed);
  }, [progress]);

  return (
    <div className="space-y-6">
      <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              Generating Your AI Video
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={onCancel}
              className="text-white/70 hover:text-white"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Progress */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Overall Progress</span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} className="w-full h-2" />
          </div>

          {/* Step by Step Progress */}
          <div className="space-y-4">
            {steps.map((step, index) => {
              const isCompleted = completedSteps.includes(index);
              const isCurrent = currentStep === index && progress < 100;
              const isUpcoming = index > currentStep;

              return (
                <div
                  key={index}
                  className={`flex items-start gap-4 p-4 rounded-lg transition-all duration-500 ${
                    isCompleted
                      ? 'bg-green-500/20 border border-green-500/30'
                      : isCurrent
                      ? 'bg-purple-500/20 border border-purple-500/30'
                      : 'bg-white/5 border border-white/10'
                  }`}
                >
                  <div
                    className={`p-2 rounded-lg transition-all duration-300 ${
                      isCompleted
                        ? 'bg-green-500 text-white'
                        : isCurrent
                        ? 'bg-purple-500 text-white'
                        : 'bg-white/10 text-white/60'
                    }`}
                  >
                    {React.createElement(step.icon, {
                      className: `w-5 h-5 ${isCurrent ? 'animate-pulse' : ''}`
                    })}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3
                        className={`font-medium ${
                          isCompleted
                            ? 'text-green-400'
                            : isCurrent
                            ? 'text-purple-400'
                            : 'text-white/60'
                        }`}
                      >
                        {step.title}
                      </h3>
                      {isCompleted && (
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      )}
                      {isCurrent && (
                        <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
                      )}
                    </div>
                    
                    <p
                      className={`text-sm ${
                        isUpcoming ? 'text-white/40' : 'text-white/70'
                      }`}
                    >
                      {step.description}
                    </p>
                    
                    <p
                      className={`text-xs mt-1 ${
                        isUpcoming ? 'text-white/30' : 'text-white/50'
                      }`}
                    >
                      {step.duration}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Status Message */}
          <div className="text-center p-4 bg-white/5 rounded-lg">
            <p className="text-white/80">
              {progress < 100
                ? `Processing step ${currentStep + 1} of ${steps.length}...`
                : 'Finalizing your video...'}
            </p>
            <p className="text-sm text-white/60 mt-1">
              This may take a few minutes depending on the complexity of your video.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Tips Card */}
      <Card className="bg-white/5 backdrop-blur-sm border-white/10 text-white">
        <CardContent className="pt-6">
          <h3 className="font-medium mb-3 text-purple-400">💡 While You Wait</h3>
          <ul className="space-y-2 text-sm text-white/70">
            <li>• Your video is being processed by multiple AI services simultaneously</li>
            <li>• ElevenLabs is creating natural-sounding speech from your script</li>
            <li>• Fal.ai is generating stunning visuals that match your content</li>
            <li>• PhotoRoom AI is enhancing backgrounds and removing unwanted elements</li>
            <li>• Veed.io is handling professional video editing and composition</li>
            <li>• Sieve is optimizing the final output for best quality</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};
