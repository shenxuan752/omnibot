import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, RefreshCw, Volume2, Repeat } from 'lucide-react';

interface AudioPlayerProps {
  src: string | null;
  label: string;
  enableSpeedControl?: boolean;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ src, label, enableSpeedControl = false }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [isLooping, setIsLooping] = useState(false);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.loop = isLooping;
    }
  }, [isLooping]);

  const togglePlay = () => {
    if (!audioRef.current || !src) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleEnded = () => {
    if (!isLooping) {
      setIsPlaying(false);
    }
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 flex flex-col gap-3 shadow-inner">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-300 font-medium text-sm">
          <Volume2 size={16} className="text-blue-400" />
          {label}
        </div>
        <div className="flex gap-2">
          {enableSpeedControl && (
             <span className="text-[10px] font-mono text-slate-400 bg-slate-700/50 px-2 py-0.5 rounded border border-slate-700">
               {playbackRate}x
             </span>
          )}
        </div>
      </div>

      <audio ref={audioRef} src={src || undefined} onEnded={handleEnded} className="hidden" />

      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          disabled={!src}
          className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg font-medium transition-colors text-sm ${
            !src 
            ? 'bg-slate-800 text-slate-600 cursor-not-allowed border border-slate-700' 
            : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20'
          }`}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          {isPlaying ? 'Pause' : 'Play'}
        </button>

        {enableSpeedControl && (
          <>
            <button 
              onClick={() => setIsLooping(!isLooping)}
              className={`p-2 rounded-lg transition-colors border ${
                isLooping 
                ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' 
                : 'bg-slate-800 text-slate-500 border-slate-700 hover:text-slate-300'
              }`}
              title="Toggle Loop"
            >
              <Repeat size={16} />
            </button>

            <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-lg border border-slate-700">
               <button 
                  onClick={() => setPlaybackRate(prev => Math.max(0.5, prev - 0.25))}
                  className="text-slate-400 hover:text-white w-6 h-6 flex items-center justify-center font-bold text-xs"
               >-</button>
               <span className="text-[9px] uppercase text-slate-500 font-bold tracking-wider">Speed</span>
               <button 
                  onClick={() => setPlaybackRate(prev => Math.min(2.0, prev + 0.25))}
                  className="text-slate-400 hover:text-white w-6 h-6 flex items-center justify-center font-bold text-xs"
               >+</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AudioPlayer;