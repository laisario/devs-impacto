import React from 'react';
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';
import type { EligibilityLevel } from '../../services/api/types';

interface EligibilityScreenProps {
  isEligible: boolean;
  eligibilityLevel: EligibilityLevel;
  score: number;
  onCreateProject: () => void;
  onViewTasks: () => void;
  onBack?: () => void;
}

export function EligibilityScreen({
  isEligible,
  eligibilityLevel,
  score,
  onCreateProject,
  onViewTasks,
  onBack,
}: EligibilityScreenProps) {
  const getTitle = () => {
    if (isEligible) {
      return 'Você pode vender para escolas!';
    }
    if (eligibilityLevel === 'partially_eligible') {
      return 'Quase lá! Falta pouco';
    }
    return 'Ainda não pode vender';
  };

  const getSubtitle = () => {
    return `Sua nota: ${score} de 100`;
  };

  const getExplanation = () => {
    if (isEligible) {
      return 'Parabéns! Você completou tudo que precisa. Agora pode criar seu projeto de venda.';
    }
    if (eligibilityLevel === 'partially_eligible') {
      return 'Você já fez bastante coisa! Complete as tarefas que faltam para poder vender.';
    }
    return 'Você ainda precisa completar algumas tarefas importantes. Vamos ver o que falta.';
  };

  const Icon = isEligible ? CheckCircle2 : eligibilityLevel === 'partially_eligible' ? AlertTriangle : Info;
  const iconColor = isEligible ? 'text-green-600' : eligibilityLevel === 'partially_eligible' ? 'text-yellow-600' : 'text-orange-600';
  const bgColor = isEligible ? 'bg-green-50' : eligibilityLevel === 'partially_eligible' ? 'bg-yellow-50' : 'bg-orange-50';

  return (
    <ScreenWrapper
      title={getTitle()}
      subtitle={getSubtitle()}
      primaryAction={{
        label: isEligible ? 'Criar projeto de venda' : 'Ver o que falta',
        onClick: isEligible ? onCreateProject : onViewTasks,
      }}
      showBack={!!onBack}
      onBack={onBack}
      className={bgColor}
    >
      <div className="flex justify-center mb-6">
        <div className={`${bgColor} rounded-full p-8 border-4 ${
          isEligible ? 'border-green-200' : eligibilityLevel === 'partially_eligible' ? 'border-yellow-200' : 'border-orange-200'
        }`}>
          <Icon className={`h-16 w-16 ${iconColor}`} />
        </div>
      </div>

      <div className={`p-4 rounded-xl border-2 ${
        isEligible ? 'bg-green-100 border-green-200' : eligibilityLevel === 'partially_eligible' ? 'bg-yellow-100 border-yellow-200' : 'bg-orange-100 border-orange-200'
      }`}>
        <p className={`text-base text-center ${
          isEligible ? 'text-green-800' : eligibilityLevel === 'partially_eligible' ? 'text-yellow-800' : 'text-orange-800'
        }`}>
          {getExplanation()}
        </p>
      </div>
    </ScreenWrapper>
  );
}
