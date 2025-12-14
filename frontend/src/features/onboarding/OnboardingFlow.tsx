import { useRef, useState, type FormEvent } from 'react';
import { MessageSquare } from 'lucide-react';
import { ONBOARDING_QUESTIONS } from './questions';

export function OnboardingFlow({
  onFinish,
  isLoading,
}: {
  onFinish: (answers: Record<string, string>) => void;
  isLoading: boolean;
}) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const inputRef = useRef<HTMLInputElement>(null);

  const currentQ = ONBOARDING_QUESTIONS[step];

  const handleAnswer = (val: string) => {
    const newAnswers = { ...answers, [currentQ.key]: val };
    setAnswers(newAnswers);
    if (inputRef.current) inputRef.current.value = '';

    if (step < ONBOARDING_QUESTIONS.length - 1) {
      setStep(step + 1);
      return;
    }

    onFinish(newAnswers);
  };

  const handleTextSubmit = (e: FormEvent) => {
    e.preventDefault();
    const value = inputRef.current?.value?.trim();
    if (value) handleAnswer(value);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mb-4"></div>
        <h2 className="text-xl font-bold text-slate-800">Analisando seu caso...</h2>
        <p className="text-slate-500">Nossa IA está verificando as exigências para o seu perfil.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="w-full bg-slate-50 h-2">
        <div
          className="bg-green-500 h-2 transition-all duration-500"
          style={{ width: `${((step + 1) / ONBOARDING_QUESTIONS.length) * 100}%` }}
        />
      </div>

      <div className="flex-1 flex flex-col max-w-lg mx-auto w-full p-6 justify-center">
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-green-100 p-2 rounded-lg">
              <MessageSquare className="text-green-600 h-6 w-6" />
            </div>
            <span className="text-sm font-bold text-slate-400 uppercase tracking-wide">
              Pergunta {step + 1} de {ONBOARDING_QUESTIONS.length}
            </span>
          </div>
          <h2 className="text-2xl font-bold text-slate-800 leading-snug">{currentQ.text}</h2>
        </div>

        <div className="space-y-3">
          {currentQ.type === 'choice' &&
            currentQ.options?.map((opt) => (
              <button
                key={opt}
                onClick={() => handleAnswer(opt)}
                className="w-full text-left p-4 border-2 border-slate-100 rounded-xl hover:border-green-500 hover:bg-green-50 transition font-medium text-slate-700 active:scale-95"
              >
                {opt}
              </button>
            ))}

          {currentQ.type === 'text' && (
            <form onSubmit={handleTextSubmit} className="flex flex-col gap-4">
              <input
                ref={inputRef}
                type="text"
                placeholder={currentQ.placeholder}
                className="w-full p-4 border-2 border-slate-200 rounded-xl focus:border-green-500 focus:outline-none text-lg"
                autoFocus
              />
              <button
                type="submit"
                className="bg-green-600 text-white font-bold py-4 rounded-xl hover:bg-green-700 transition"
              >
                Continuar
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
