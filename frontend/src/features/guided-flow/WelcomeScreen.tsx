import { Leaf } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';

interface WelcomeScreenProps {
  onStart: () => void;
}

export function WelcomeScreen({ onStart }: WelcomeScreenProps) {
  return (
    <ScreenWrapper
      title="Bem-vindo ao CertificaFácil"
      subtitle="Vamos te ajudar a vender para escolas públicas. É simples e rápido!"
      primaryAction={{
        label: 'Começar',
        onClick: onStart,
      }}
      progress={{
        current: 1,
        total: 1,
        label: 'Bem-vindo',
      }}
    >
      <div className="flex justify-center mb-8">
        <div className="bg-green-100 rounded-full p-8">
          <Leaf className="h-16 w-16 text-green-600" />
        </div>
      </div>
    </ScreenWrapper>
  );
}
