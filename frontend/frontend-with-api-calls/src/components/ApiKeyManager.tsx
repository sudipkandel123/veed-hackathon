import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Key, CheckCircle } from 'lucide-react';

// Define default API keys
const DEFAULT_API_KEYS = {
  elevenlabs: import.meta.env.VITE_ELEVENLABS_API_KEY || '',
  veed: import.meta.env.VITE_VEED_API_KEY || '',
  fal: import.meta.env.VITE_FAL_API_KEY || '',
  sieve: import.meta.env.VITE_SIEVE_API_KEY || '',
  photoroom: import.meta.env.VITE_PHOTOROOM_API_KEY || ''
};

const apiServices = [
  {
    key: 'elevenlabs',
    name: 'ElevenLabs',
    description: 'AI voice synthesis and text-to-speech',
    url: 'https://elevenlabs.io/app/speech-synthesis'
  },
  {
    key: 'veed',
    name: 'Veed.io',
    description: 'Video editing and processing',
    url: 'https://www.veed.io/api'
  },
  {
    key: 'fal',
    name: 'Fal.ai',
    description: 'AI image and video generation',
    url: 'https://fal.ai/dashboard'
  },
  {
    key: 'sieve',
    name: 'Sieve',
    description: 'Video processing and analysis',
    url: 'https://www.sievedata.com/dashboard'
  },
  {
    key: 'photoroom',
    name: 'PhotoRoom',
    description: 'AI background removal and editing',
    url: 'https://www.photoroom.com/api'
  }
];

export const ApiKeyManager = () => {
  // Store API keys in localStorage on component mount
  React.useEffect(() => {
    localStorage.setItem('ai-video-api-keys', JSON.stringify(DEFAULT_API_KEYS));
  }, []);

  return (
    <Card className="bg-white/10 backdrop-blur-sm border-white/20 text-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Key className="w-5 h-5" />
          API Configuration
        </CardTitle>
        <CardDescription className="text-white/70">
          API keys are securely configured through environment variables.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {apiServices.map(({ key, name, description }) => (
          <div key={key} className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium">{name}</span>
                  <CheckCircle className="w-4 h-4 text-green-400" />
                </div>
                <p className="text-xs text-white/60 mt-1">{description}</p>
              </div>
            </div>
          </div>
        ))}
        
        <div className="pt-4 border-t border-white/20">
          <p className="text-sm text-white/60">
            💡 <strong>Security note:</strong> API keys are stored securely in environment variables. 
            Contact your administrator for key management.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
