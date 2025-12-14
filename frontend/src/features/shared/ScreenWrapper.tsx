import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { ProgressBar } from './ProgressBar';

interface ScreenWrapperProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  primaryAction?: {
    label: string;
    onClick: () => void;
    disabled?: boolean;
    variant?: 'primary' | 'secondary';
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
    disabled?: boolean;
  };
  showBack?: boolean;
  onBack?: () => void;
  progress?: {
    current: number;
    total: number;
    label?: string;
  };
  className?: string;
}

export function ScreenWrapper({
  title,
  subtitle,
  children,
  primaryAction,
  secondaryAction,
  showBack = false,
  onBack,
  progress,
  className = '',
}: ScreenWrapperProps) {
  return (
    <div className={`min-h-screen bg-white flex flex-col ${className}`}>
      {progress && <ProgressBar current={progress.current} total={progress.total} label={progress.label} />}
      
      <div className="flex-1 flex flex-col max-w-lg mx-auto w-full px-4 sm:px-6 py-6 sm:py-8">
        {showBack && onBack && (
          <button
            onClick={onBack}
            className="flex items-center text-slate-500 hover:text-slate-800 text-base font-medium mb-6 self-start"
            aria-label="Voltar"
          >
            <ChevronLeft className="h-5 w-5 mr-1" />
            Voltar
          </button>
        )}

        <div className="flex-1 flex flex-col justify-center">
          <div className="mb-8">
            <h1 className="text-2xl md:text-3xl font-bold text-slate-800 leading-tight mb-3">
              {title}
            </h1>
            {subtitle && (
              <p className="text-base md:text-lg text-slate-600 leading-relaxed">
                {subtitle}
              </p>
            )}
          </div>

          <div className="mb-8">
            {children}
          </div>

          <div className="space-y-4">
            {primaryAction && (
              <button
                onClick={primaryAction.onClick}
                disabled={primaryAction.disabled}
                className={`w-full min-h-[56px] px-6 py-4 rounded-xl font-bold text-lg transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ${
                  primaryAction.variant === 'secondary'
                    ? 'bg-white text-green-600 border-2 border-green-600 hover:bg-green-50'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
                aria-label={primaryAction.label}
              >
                {primaryAction.label}
              </button>
            )}

            {secondaryAction && (
              <button
                onClick={secondaryAction.onClick}
                disabled={secondaryAction.disabled}
                className="w-full min-h-[48px] px-6 py-3 rounded-xl font-medium text-base text-slate-600 border-2 border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label={secondaryAction.label}
              >
                {secondaryAction.label}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
