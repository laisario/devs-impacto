import { CheckCircle2 } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';

interface TaskCompleteScreenProps {
  completedCount: number;
  totalCount: number;
  onNextTask: () => void;
  onViewResult: () => void;
}

export function TaskCompleteScreen({
  completedCount,
  totalCount,
  onNextTask,
  onViewResult,
}: TaskCompleteScreenProps) {
  const allDone = completedCount >= totalCount;

  return (
    <ScreenWrapper
      title="Tarefa concluída!"
      subtitle={`Você já fez ${completedCount} de ${totalCount} ${totalCount === 1 ? 'tarefa' : 'tarefas'}`}
      primaryAction={{
        label: allDone ? 'Ver resultado' : 'Próxima tarefa',
        onClick: allDone ? onViewResult : onNextTask,
      }}
      className="bg-green-50"
    >
      <div className="flex justify-center mb-8">
        <div className="bg-green-600 rounded-full p-8">
          <CheckCircle2 className="h-16 w-16 text-white" />
        </div>
      </div>
    </ScreenWrapper>
  );
}
