import { CheckCircle2 } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';

interface OnboardingCompleteScreenProps {
  taskCount: number;
  onContinue: () => void;
}

export function OnboardingCompleteScreen({ taskCount, onContinue }: OnboardingCompleteScreenProps) {
  return (
    <ScreenWrapper
      title="Tudo certo! Agora vamos ver o que você precisa fazer"
      subtitle={`Encontramos ${taskCount} ${taskCount === 1 ? 'coisa' : 'coisas'} para você completar`}
      primaryAction={{
        label: 'Ver minha lista',
        onClick: onContinue,
      }}
    >
      <div className="flex justify-center mb-8">
        <div className="bg-green-100 rounded-full p-8">
          <CheckCircle2 className="h-16 w-16 text-green-600" />
        </div>
      </div>
    </ScreenWrapper>
  );
}
