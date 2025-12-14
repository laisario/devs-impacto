import { CheckCircle, AlertCircle, Loader2, MessageSquare } from 'lucide-react';
import type { ChatState } from '../../services/api/chat';

interface ChatStatusIndicatorProps {
  state: ChatState;
  currentTaskCode?: string | null;
  className?: string;
}

export function ChatStatusIndicator({ state, currentTaskCode, className = '' }: ChatStatusIndicatorProps) {
  const getStatusConfig = () => {
    switch (state) {
      case 'idle':
        return {
          icon: MessageSquare,
          color: 'text-slate-500',
          bgColor: 'bg-slate-50',
          label: 'Pronto para ajudar',
        };
      case 'explaining_task':
        return {
          icon: Loader2,
          color: 'text-blue-500',
          bgColor: 'bg-blue-50',
          label: currentTaskCode ? `Explicando: ${currentTaskCode}` : 'Explicando tarefa...',
          animate: true,
        };
      case 'waiting_confirmation':
        return {
          icon: AlertCircle,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-50',
          label: 'Aguardando confirmação',
        };
      case 'task_completed':
        return {
          icon: CheckCircle,
          color: 'text-green-500',
          bgColor: 'bg-green-50',
          label: 'Tarefa concluída!',
        };
      case 'error':
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-50',
          label: 'Erro',
        };
      default:
        return {
          icon: MessageSquare,
          color: 'text-slate-500',
          bgColor: 'bg-slate-50',
          label: 'Chat',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${config.bgColor} ${config.color} ${className}`}
    >
      <Icon
        className={`h-4 w-4 ${config.animate ? 'animate-spin' : ''}`}
        aria-hidden="true"
      />
      <span className="text-xs font-medium">{config.label}</span>
    </div>
  );
}
