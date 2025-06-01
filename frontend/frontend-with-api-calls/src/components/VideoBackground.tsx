
import React from 'react';

export const VideoBackground = () => {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden">
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
      >
        {/* replace this background with another cooler background video */}
        <source
          src="https://videos.pexels.com/video-files/7710243/7710243-uhd_2560_1440_30fps.mp4"
          type="video/mp4"
        />
        <source
          src="https://videos.pexels.com/video-files/7710243/7710243-hd_1920_1080_30fps.mp4"
          type="video/mp4"
        />
        {/* Fallback gradient background if video fails to load */}
      </video>
      {/* Dark overlay for better text readability */}
      <div className="absolute inset-0 bg-black/40"></div>
    </div>
  );
};
