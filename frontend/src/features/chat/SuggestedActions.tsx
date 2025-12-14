import { CheckCircle, ExternalLink, FileText } from 'lucide-react';
import type { SuggestedAction } from '../../services/api/chat';
import { updateTaskStatus } from '../../services/api/formalization';
import type { TaskStatus } from '../../services/api/types';

interface SuggestedActionsProps {
  actions: SuggestedAction[];
  onActionExecuted?: (action: SuggestedAction) => void;
  onError?: (error: Error) => void;
}

export function SuggestedActions({ actions, onActionExecuted, onError }: SuggestedActionsProps) {
  if (actions.length === 0) {
    return null;
  }

  const handleAction = async (action: SuggestedAction) => {
    try {
      if (action.type === 'mark_task_done' && action.task_code) {
        // Mark task as done
        await updateTaskStatus(action.task_code, 'done' as TaskStatus);
        onActionExecuted?.(action);
      } else if (action.type === 'go_to_screen' && action.screen) {
        // Navigate to screen (handled by parent)
        onActionExecuted?.(action);
      } else if (action.type === 'open_guide' && action.requirement_id) {
        // Open guide (handled by parent)
        onActionExecuted?.(action);
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error('Failed to execute action');
      onError?.(err);
    }
  };

  const getActionLabel = (action: SuggestedAction): string => {
    switch (action.type) {
      case 'mark_task_done':
        return 'Marcar como concluída';
      case 'go_to_screen':
        return `Ir para ${action.screen}`;
      case 'open_guide':
        return 'Ver guia completo';
      default:
        return 'Executar ação';
    }
  };

  const getActionIcon = (action: SuggestedAction) => {
    switch (action.type) {
      case 'mark_task_done':
        return <CheckCircle className="h-4 w-4" />;
      case 'go_to_screen':
        return <ExternalLink className="h-4 w-4" />;
      case 'open_guide':
        return <FileText className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-slate-200">
      {actions.map((action, index) => (
        <button
          key={index}
          onClick={() => handleAction(action)}
          className="flex items-center gap-2 px-3 py-1.5 bg-primary-50 hover:bg-primary-100 text-primary-700 rounded-lg transition-colors text-sm font-medium border border-primary-200"
        >
          {getActionIcon(action)}
          <span>{getActionLabel(action)}</span>
        </button>
      ))}
    </div>
  );
}
