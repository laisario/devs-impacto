import React, { useState, useRef, useEffect } from 'react';
import { ScreenWrapper } from '../shared/ScreenWrapper';
import { getOnboardingStatus, submitOnboardingAnswer, updateProfileField } from '../../services/api/onboarding';
import { ApiClientError } from '../../services/api/client';
import type { OnboardingQuestion } from '../../services/api/types';

interface OnboardingScreenProps {
  onComplete: () => void;
  onBack?: () => void;
}

export function OnboardingScreen({ onComplete, onBack }: OnboardingScreenProps) {
  const [currentQuestion, setCurrentQuestion] = useState<OnboardingQuestion | null>(null);
  const [status, setStatus] = useState<{ progress: number; total: number; answered: number } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDapCafInput, setShowDapCafInput] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const dapCafInputRef = useRef<HTMLInputElement>(null);

  const loadNextQuestion = async () => {
    setIsLoading(true);
    setError('');

    try {
      const statusResponse = await getOnboardingStatus();
      setStatus({
        progress: statusResponse.progress_percentage,
        total: statusResponse.total_questions,
        answered: statusResponse.answered_questions,
      });

      if (statusResponse.status === 'completed') {
        setIsLoading(false);
        onComplete();
        return;
      }

      if (statusResponse.next_question) {
        setCurrentQuestion(statusResponse.next_question);
        setSelectedOptions([]);
        setIsLoading(false);
      } else {
        setIsLoading(false);
        onComplete();
      }
    } catch (err) {
      setIsLoading(false);
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao carregar pergunta. Tente novamente.');
      } else {
        setError('Erro ao carregar pergunta. Tente novamente.');
      }
    }
  };

  useEffect(() => {
    loadNextQuestion();
  }, []);

  const handleAnswer = async (val: string | boolean | string[]) => {
    if (!currentQuestion) return;

    setIsSubmitting(true);
    setError('');

    try {
      let answerValue: string | boolean | string[] = val;
      if (currentQuestion.question_type === 'boolean') {
        answerValue = val === 'true' || val === 'Sim' || val === true;
      } else if (currentQuestion.allow_multiple && Array.isArray(val)) {
        answerValue = val;
      }

      await submitOnboardingAnswer({
        question_id: currentQuestion.question_id,
        answer: answerValue,
      });

      if (currentQuestion.question_id === 'has_dap_caf' && (answerValue === true || answerValue === 'true')) {
        setShowDapCafInput(true);
        setIsSubmitting(false);
        return;
      }

      if (currentQuestion.question_id === 'has_dap_caf' && (answerValue === false || answerValue === 'false')) {
        setShowDapCafInput(false);
      }

      if (inputRef.current) inputRef.current.value = '';
      setShowDapCafInput(false);
      await loadNextQuestion();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao salvar resposta. Tente novamente.');
      } else {
        setError('Erro ao salvar resposta. Tente novamente.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDapCafSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const value = dapCafInputRef.current?.value?.trim();
    if (!value) {
      setError('Por favor, insira o número da DAP/CAF');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await updateProfileField('dap_caf_number', value);
      if (dapCafInputRef.current) dapCafInputRef.current.value = '';
      setShowDapCafInput(false);
      await loadNextQuestion();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao salvar número DAP/CAF. Tente novamente.');
      } else {
        setError('Erro ao salvar número DAP/CAF. Tente novamente.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const value = inputRef.current?.value?.trim();
    if (value) handleAnswer(value);
  };

  const handleChoiceClick = (opt: string) => {
    if (currentQuestion?.question_type === 'boolean') {
      handleAnswer(opt === 'Sim' || opt.toLowerCase() === 'sim' || opt === 'true');
    } else if (currentQuestion?.allow_multiple) {
      setSelectedOptions((prev) => {
        if (prev.includes(opt)) {
          return prev.filter((o) => o !== opt);
        } else {
          return [...prev, opt];
        }
      });
    } else {
      handleAnswer(opt);
    }
  };

  const handleMultiSelectSubmit = async () => {
    if (selectedOptions.length === 0) {
      setError('Por favor, selecione pelo menos uma opção');
      return;
    }
    await handleAnswer(selectedOptions);
  };

  if (isLoading) {
    return (
      <ScreenWrapper
        title="Carregando..."
        subtitle="Preparando suas perguntas"
        progress={status ? { current: status.answered + 1, total: status.total } : undefined}
      >
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      </ScreenWrapper>
    );
  }

  if (error && !currentQuestion) {
    return (
      <ScreenWrapper
        title="Erro ao carregar perguntas"
        subtitle={error}
        primaryAction={{
          label: 'Tentar novamente',
          onClick: loadNextQuestion,
        }}
        showBack={!!onBack}
        onBack={onBack}
      />
    );
  }

  const questionNumber = status ? status.answered + 1 : 1;
  const totalQuestions = status?.total || 0;

  if (showDapCafInput) {
    return (
      <ScreenWrapper
        title="Qual é o número da sua DAP/CAF?"
        primaryAction={{
          label: isSubmitting ? 'Salvando...' : 'Continuar',
          onClick: handleDapCafSubmit,
          disabled: isSubmitting,
        }}
        showBack={!!onBack}
        onBack={onBack}
        progress={status ? { current: questionNumber, total: totalQuestions, label: `Pergunta ${questionNumber} de ${totalQuestions}` } : undefined}
      >
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}
        <form onSubmit={handleDapCafSubmit} className="space-y-4">
          <input
            ref={dapCafInputRef}
            type="text"
            placeholder="Digite o número da sua DAP/CAF"
            className="w-full p-4 border-2 border-slate-200 rounded-xl focus:border-green-500 focus:outline-none text-lg"
            autoFocus
            disabled={isSubmitting}
          />
        </form>
      </ScreenWrapper>
    );
  }

  if (!currentQuestion) {
    return null;
  }

  return (
    <ScreenWrapper
      title={currentQuestion.question_text}
      showBack={!!onBack}
      onBack={onBack}
      progress={status ? { current: questionNumber, total: totalQuestions, label: `Pergunta ${questionNumber} de ${totalQuestions}` } : undefined}
    >
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-3">
        {currentQuestion.question_type === 'boolean' && (
          <>
            <button
              onClick={() => handleChoiceClick('Sim')}
              disabled={isSubmitting}
              className="w-full text-left p-4 border-2 border-slate-100 rounded-xl hover:border-green-500 hover:bg-green-50 transition font-medium text-slate-700 active:scale-95 disabled:opacity-50 min-h-[56px] text-lg"
            >
              Sim
            </button>
            <button
              onClick={() => handleChoiceClick('Não')}
              disabled={isSubmitting}
              className="w-full text-left p-4 border-2 border-slate-100 rounded-xl hover:border-green-500 hover:bg-green-50 transition font-medium text-slate-700 active:scale-95 disabled:opacity-50 min-h-[56px] text-lg"
            >
              Não
            </button>
          </>
        )}

        {currentQuestion.question_type === 'choice' && currentQuestion.options && (
          <>
            {currentQuestion.allow_multiple ? (
              <>
                {currentQuestion.options.map((opt) => {
                  const isSelected = selectedOptions.includes(opt);
                  return (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleChoiceClick(opt)}
                      disabled={isSubmitting}
                      className={`w-full text-left p-4 border-2 rounded-xl transition font-medium active:scale-95 disabled:opacity-50 flex items-center gap-3 min-h-[56px] text-lg ${
                        isSelected
                          ? 'border-green-500 bg-green-50 text-slate-800'
                          : 'border-slate-100 hover:border-green-500 hover:bg-green-50 text-slate-700'
                      }`}
                    >
                      <div
                        className={`w-6 h-6 rounded border-2 flex items-center justify-center shrink-0 ${
                          isSelected
                            ? 'bg-green-500 border-green-500'
                            : 'border-slate-300 bg-white'
                        }`}
                      >
                        {isSelected && (
                          <svg
                            className="w-4 h-4 text-white"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path d="M5 13l4 4L19 7"></path>
                          </svg>
                        )}
                      </div>
                      <span>{opt.charAt(0).toUpperCase() + opt.slice(1).toLowerCase()}</span>
                    </button>
                  );
                })}
                <button
                  onClick={handleMultiSelectSubmit}
                  disabled={isSubmitting || selectedOptions.length === 0}
                  className="mt-4 bg-green-600 text-white font-bold py-4 rounded-xl hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed min-h-[56px] text-lg"
                >
                  {isSubmitting ? 'Salvando...' : 'Continuar'}
                </button>
              </>
            ) : (
              currentQuestion.options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => handleChoiceClick(opt)}
                  disabled={isSubmitting}
                  className="w-full text-left p-4 border-2 border-slate-100 rounded-xl hover:border-green-500 hover:bg-green-50 transition font-medium text-slate-700 active:scale-95 disabled:opacity-50 min-h-[56px] text-lg"
                >
                  {opt.charAt(0).toUpperCase() + opt.slice(1).toLowerCase()}
                </button>
              ))
            )}
          </>
        )}

        {currentQuestion.question_type === 'text' && (
          <form onSubmit={handleTextSubmit} className="space-y-4">
            <input
              ref={inputRef}
              type="text"
              placeholder="Digite sua resposta"
              className="w-full p-4 border-2 border-slate-200 rounded-xl focus:border-green-500 focus:outline-none text-lg"
              autoFocus
              disabled={isSubmitting}
            />
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-green-600 text-white font-bold py-4 rounded-xl hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed min-h-[56px] text-lg"
            >
              {isSubmitting ? 'Salvando...' : 'Continuar'}
            </button>
          </form>
        )}
      </div>
    </ScreenWrapper>
  );
}
