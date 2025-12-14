import React from 'react';

interface PrimaryButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
  className?: string;
}

export function PrimaryButton({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
  className = '',
}: PrimaryButtonProps) {
  const baseClasses = 'w-full min-h-[56px] px-6 py-4 rounded-xl font-bold text-lg transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = variant === 'primary'
    ? 'bg-green-600 text-white hover:bg-green-700'
    : 'bg-white text-green-600 border-2 border-green-600 hover:bg-green-50';

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses} ${className}`}
      aria-label={typeof children === 'string' ? children : 'Botão de ação'}
    >
      {children}
    </button>
  );
}
