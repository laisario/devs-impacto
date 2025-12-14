import React from 'react';

interface ProgressBarProps {
  current: number;
  total: number;
  label?: string;
}

export function ProgressBar({ current, total, label }: ProgressBarProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  const displayLabel = label || `Passo ${current} de ${total}`;

  return (
    <div className="w-full bg-white">
      <div className="max-w-lg mx-auto px-4 py-3">
        <div className="text-center text-sm font-medium text-slate-600 mb-2">
          {displayLabel}
        </div>
        <div className="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all duration-500"
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={current}
            aria-valuemin={0}
            aria-valuemax={total}
            aria-label={displayLabel}
          />
        </div>
      </div>
    </div>
  );
}
