import React from 'react';
import { Feather } from 'lucide-react';

// Custom Artistic Feather Components
// Type A: The "Quill" - Long, elegant, curved, resembling calligraphy
const ArtisticFeatherA = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 100 200" className={className} fill="currentColor">
    <path d="M50 0C50 0 55 10 52 25C48 45 40 60 35 80C30 100 35 130 50 160C55 170 60 180 60 190C60 195 55 200 50 200C45 190 40 170 30 150C20 130 10 100 20 60C25 40 40 10 50 0Z" opacity="0.9" />
    <path d="M50 0C50 0 45 15 48 30C52 50 60 70 65 90C70 110 65 140 50 170C50 170 80 120 75 80C70 50 60 20 50 0Z" opacity="0.6" />
    <path d="M50 5 Q 45 80 50 190" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.4" />
  </svg>
);

// Type B: The "Plume" - Softer, wider, drifting
const ArtisticFeatherB = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 100 150" className={className} fill="currentColor">
    <path d="M50 10C50 10 20 40 20 80C20 110 40 130 50 140C60 130 80 110 80 80C80 40 50 10 50 10Z" opacity="0.8" />
    {/* Barbs/Texture cuts */}
    <path d="M20 80 Q 35 90 50 140" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
    <path d="M80 80 Q 65 90 50 140" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.3" />
    <circle cx="50" cy="140" r="2" opacity="0.5" />
  </svg>
);

// Type C: The "Fragment" - Minimalist shard
const ArtisticFeatherC = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 50 100" className={className} fill="currentColor">
     <path d="M25 0 Q 0 40 25 100 Q 50 40 25 0" opacity="0.7" />
  </svg>
);

const Banner: React.FC = () => {
  return (
    <div className="relative w-full py-24 md:py-36 mb-8 overflow-hidden group">
      
      {/* Background Ambience Container */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
        
        {/* 1. Base Radial Vignette (Atmosphere) */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(249,248,244,0.9)_100%)] dark:bg-[radial-gradient(circle_at_center,transparent_0%,rgba(24,24,27,0.8)_100%)] z-0" />
        
        {/* 2. Dynamic Light Orbs (Glow Layer) */}
        {/* Orb 1: Golden Nebula (Left) */}
        <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-gold/10 dark:bg-gold/5 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-[80px] opacity-100 animate-blob z-0"></div>
        
        {/* Orb 2: Paper/Mineral Mist (Right) */}
        <div className="absolute top-[10%] right-[-10%] w-[35rem] h-[35rem] bg-gray-200/40 dark:bg-mineral-700/20 rounded-full mix-blend-multiply dark:mix-blend-screen filter blur-[80px] opacity-100 animate-blob z-0" style={{ animationDelay: '2s' }}></div>
        

        {/* 3. Artistic Floating Feathers (Texture Layer) */}
        
        {/* Feather 1: The Giant Shadow (Depth) 
            Low opacity, high blur, background element.
        */}
        <div className="absolute top-0 -left-12 opacity-[0.03] dark:opacity-[0.02] animate-sway text-paper-900 dark:text-white z-0" style={{ animationDuration: '25s' }}>
          <ArtisticFeatherA className="w-96 h-96 blur-[2px] rotate-12" />
        </div>

        {/* Feather 2: The Golden Drifter (Accent)
            Mid-ground, slight gold tint, elegant curve.
        */}
        <div className="absolute top-[20%] right-[10%] opacity-10 dark:opacity-10 animate-sway-delayed text-gold-light dark:text-gold z-0" style={{ animationDuration: '20s' }}>
           <ArtisticFeatherA className="w-48 h-48 rotate-[-15deg]" />
        </div>

        {/* Feather 3: The Falling Plume (Movement)
            Near bottom, simulating falling.
        */}
        <div className="absolute bottom-[10%] left-[20%] opacity-5 dark:opacity-[0.04] animate-float text-paper-900 dark:text-gray-400 z-0" style={{ animationDuration: '15s', animationDelay: '1s' }}>
           <ArtisticFeatherB className="w-32 h-32 rotate-[30deg]" />
        </div>

        {/* Feather 4: The Foreground Shard (Detail)
            Closer to viewer, sharper, gold accent.
        */}
        <div className="absolute top-[15%] left-[25%] opacity-20 dark:opacity-20 animate-float text-gold-light dark:text-gold z-0" style={{ animationDuration: '12s', animationDelay: '3s' }}>
           <ArtisticFeatherC className="w-12 h-24 rotate-[-10deg]" />
        </div>

         {/* Feather 5: Far Background Detail */}
         <div className="absolute bottom-0 right-[25%] opacity-[0.04] dark:opacity-[0.03] animate-sway text-paper-900 dark:text-white z-0" style={{ animationDuration: '22s', animationDelay: '5s' }}>
           <ArtisticFeatherB className="w-64 h-64 blur-[1px] rotate-[45deg]" />
        </div>

      </div>

      <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
        
        {/* Logo/Icon Container - Glassmorphism */}
        <div className="flex justify-center mb-10 animate-fade-in">
          <div className="relative group/icon">
            <div className="absolute inset-0 bg-gold/20 dark:bg-gold/10 rounded-full blur-xl opacity-0 group-hover/icon:opacity-100 transition-opacity duration-1000" />
            <div className="relative p-5 rounded-full bg-paper-50/30 dark:bg-mineral-800/30 backdrop-blur-sm border border-black/5 dark:border-white/5 shadow-sm ring-1 ring-white/20 dark:ring-white/5 animate-slide-up">
              <Feather className="w-8 h-8 text-gold-light dark:text-gold opacity-90" strokeWidth={1} />
            </div>
          </div>
        </div>

        {/* Main Title (Slogan) */}
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-serif font-bold tracking-tight text-paper-900 dark:text-mineral-100 mb-8 leading-tight animate-slide-up drop-shadow-sm" style={{ animationDelay: '0.1s' }}>
          繁芜世界 <span className="text-gold-light dark:text-gold mx-2 opacity-60 font-light">·</span> 仅取片羽
        </h1>

        {/* Subtitle / Description */}
        <p className="text-base md:text-lg text-gray-500 dark:text-gray-400 font-light max-w-xl mx-auto leading-relaxed animate-slide-up tracking-wide" style={{ animationDelay: '0.2s' }}>
          在信息过载的洪流中，建立高信噪比的个人珍藏。
          <br className="hidden md:block"/>
          拾取那些在暗夜中闪光的智慧碎片。
        </p>

        {/* Decorative Line - Ritualistic */}
        <div className="mt-16 flex items-center justify-center gap-6 opacity-30 animate-fade-in" style={{ animationDelay: '0.4s' }}>
          <div className="h-[1px] w-12 md:w-24 bg-gradient-to-r from-transparent via-gray-400 dark:via-gray-500 to-transparent" />
          <div className="w-1 h-1 rounded-full bg-gold-light dark:bg-gold" />
          <div className="h-[1px] w-12 md:w-24 bg-gradient-to-l from-transparent via-gray-400 dark:via-gray-500 to-transparent" />
        </div>
      </div>
    </div>
  );
};

export default Banner;