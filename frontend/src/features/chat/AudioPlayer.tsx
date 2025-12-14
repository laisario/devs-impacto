import { useState, useRef, useEffect } from 'react';
import { Play, Square, Volume2 } from 'lucide-react';
import { normalizeUploadUrl } from '../../services/api/client';

interface AudioPlayerProps {
  audioUrl: string;
  onEnded?: () => void;
  className?: string;
}

export function AudioPlayer({ audioUrl, onEnded, className = '' }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // Normalize audio URL to handle internal Docker URLs
  const normalizedAudioUrl = normalizeUploadUrl(audioUrl);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handlePlay = () => {
      setIsPlaying(true);
      setIsLoading(false);
    };

    const handlePause = () => {
      setIsPlaying(false);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      onEnded?.();
    };

    const handleLoadStart = () => {
      setIsLoading(true);
    };

    const handleCanPlay = () => {
      setIsLoading(false);
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('loadstart', handleLoadStart);
    audio.addEventListener('canplay', handleCanPlay);

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('loadstart', handleLoadStart);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, [audioUrl, onEnded]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play().catch((error) => {
        console.error('Error playing audio:', error);
        setIsLoading(false);
      });
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <audio ref={audioRef} src={normalizedAudioUrl} preload="auto" />
      <button
        onClick={togglePlay}
        disabled={isLoading}
        className="flex items-center gap-2 px-3 py-1.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50 text-sm font-medium"
        title={isPlaying ? 'Pausar áudio' : 'Ouvir áudio'}
      >
        {isLoading ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Carregando...</span>
          </>
        ) : isPlaying ? (
          <>
            <Square className="h-4 w-4 fill-current" />
            <span>Pausar</span>
          </>
        ) : (
          <>
            <Play className="h-4 w-4 fill-current" />
            <span>Ouvir</span>
          </>
        )}
      </button>
      {audioUrl && (
        <div className="flex items-center gap-1 text-xs text-slate-500">
          <Volume2 className="h-3 w-3" />
          <span>Áudio disponível</span>
        </div>
      )}
    </div>
  );
}
