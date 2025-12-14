import { CheckCircle2, PartyPopper, TrendingUp } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';

interface AllCompleteScreenProps {
  score?: number;
  onViewProject?: () => void;
}

export function AllCompleteScreen({ score = 100 }: AllCompleteScreenProps) {
  return (
    <ScreenWrapper
      title="Parabéns! Você está pronto!"
      subtitle="Você completou todas as tarefas e está pronto para vender para escolas públicas."
      className="bg-gradient-to-br from-green-50 via-emerald-50 to-green-100"
    >
      <div className="flex flex-col items-center mb-8">
        {/* Celebration Icon */}
        <div className="relative mb-6">
          <div className="bg-green-600 rounded-full p-8 shadow-lg">
            <CheckCircle2 className="h-20 w-20 text-white" />
          </div>
          <div className="absolute -top-2 -right-2 bg-yellow-400 rounded-full p-3 animate-bounce">
            <PartyPopper className="h-6 w-6 text-yellow-800" />
          </div>
        </div>

        {/* Score Display */}
        <div className="w-full max-w-sm bg-white rounded-xl border-2 border-green-200 p-6 shadow-lg mb-6">
          <div className="flex items-center justify-center gap-2 mb-3">
            <TrendingUp className="h-6 w-6 text-green-600" />
            <p className="text-2xl font-bold text-green-600">
              Sua nota: {score}/100
            </p>
          </div>
          <div className="w-full h-3 bg-green-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-green-600 rounded-full transition-all duration-1000"
              style={{ width: `${score}%` }}
            />
          </div>
          <p className="text-center text-sm text-slate-600 mt-3 font-medium">
            Você está 100% pronto para vender!
          </p>
        </div>

        {/* Success Message */}
        <div className="bg-white rounded-xl border-2 border-green-200 p-6 shadow-sm w-full max-w-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-3 text-center">
            O que vem agora?
          </h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="bg-green-100 rounded-full p-1.5 mt-0.5">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">
                Você pode criar seu projeto de venda quando quiser
              </p>
            </div>
            <div className="flex items-start gap-3">
              <div className="bg-green-100 rounded-full p-1.5 mt-0.5">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">
                Fique de olho nos editais públicos da sua região
              </p>
            </div>
            <div className="flex items-start gap-3">
              <div className="bg-green-100 rounded-full p-1.5 mt-0.5">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">
                Está tudo certo para participar e começar a vender
              </p>
            </div>
          </div>
        </div>
      </div>
    </ScreenWrapper>
  );
}
