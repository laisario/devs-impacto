import { useRef, useState, useEffect, type FormEvent } from 'react';
import { MessageSquare } from 'lucide-react';
import { getOnboardingStatus, submitOnboardingAnswer, updateProfileField } from '../../services/api/onboarding';
import { ApiClientError } from '../../services/api/client';
import type { OnboardingQuestion } from '../../services/api/types';

// Helper function to capitalize first letter
const capitalize = (str: string): string => {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export function OnboardingFlow({
  onFinish,
  isLoading: externalLoading,
}: {
  onFinish: () => void;
  isLoading: boolean;
}) {
  const [currentQuestion, setCurrentQuestion] = useState<OnboardingQuestion | null>(null);
  const [status, setStatus] = useState<{ progress: number; total: number; answered: number } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDapCafInput, setShowDapCafInput] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]); // For multi-select
  const inputRef = useRef<HTMLInputElement>(null);
  const dapCafInputRef = useRef<HTMLInputElement>(null);

  const loadNextQuestion = async () => {
    setIsLoading(true);
    setError('');
    try {
      const statusResponse = await getOnboardingStatus();
      console.log('Onboarding status response:', statusResponse);
      
      setStatus({
        progress: statusResponse.progress_percentage,
        total: statusResponse.total_questions,
        answered: statusResponse.answered_questions,
      });

      if (statusResponse.status === 'completed') {
        setIsLoading(false);
        onFinish();
        return;
      }

      if (statusResponse.next_question) {
        setCurrentQuestion(statusResponse.next_question);
        // Reset multi-select state when loading new question
        setSelectedOptions([]);
        setIsLoading(false);
      } else {
        // No next question available
        if (statusResponse.total_questions === 0) {
          // No questions in database yet - redirect to dashboard
          setIsLoading(false);
          console.warn('No onboarding questions available, redirecting to dashboard');
          onFinish();
        } else {
          // All questions answered or no more questions
          setIsLoading(false);
          onFinish();
        }
      }
    } catch (err) {
      console.error('Error loading onboarding question:', err);
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
      // Convert answer based on question type
      let answerValue: string | boolean | string[] = val;
      if (currentQuestion.question_type === 'boolean') {
        answerValue = val === 'true' || val === 'Sim' || val === true;
      } else if (currentQuestion.allow_multiple && Array.isArray(val)) {
        // For multi-select, answer is already an array
        answerValue = val;
      }

      await submitOnboardingAnswer({
        question_id: currentQuestion.question_id,
        answer: answerValue,
      });

      // If answered "Sim" to has_dap_caf, show input for number
      if (currentQuestion.question_id === 'has_dap_caf' && (answerValue === true || answerValue === 'true')) {
        setShowDapCafInput(true);
        setIsSubmitting(false);
        return; // Don't load next question yet, wait for DAP/CAF number
      }
      
      // If answered "Não" to has_dap_caf, hide input and continue
      if (currentQuestion.question_id === 'has_dap_caf' && (answerValue === false || answerValue === 'false')) {
        setShowDapCafInput(false);
      }

      if (inputRef.current) inputRef.current.value = '';
      setShowDapCafInput(false);

      // Load next question
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

  const handleDapCafSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const value = dapCafInputRef.current?.value?.trim();
    if (!value) {
      setError('Por favor, insira o número da DAP/CAF');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      // Save DAP/CAF number directly to profile
      await updateProfileField('dap_caf_number', value);
      
      if (dapCafInputRef.current) dapCafInputRef.current.value = '';
      setShowDapCafInput(false);

      // Load next question
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

  const handleTextSubmit = (e: FormEvent) => {
    e.preventDefault();
    const value = inputRef.current?.value?.trim();
    if (value) handleAnswer(value);
  };

  const handleChoiceClick = (opt: string) => {
    if (currentQuestion?.question_type === 'boolean') {
      handleAnswer(opt === 'Sim' || opt.toLowerCase() === 'sim' || opt === 'true');
    } else if (currentQuestion?.allow_multiple) {
      // Multi-select: toggle option in selectedOptions
      setSelectedOptions((prev) => {
        if (prev.includes(opt)) {
          return prev.filter((o) => o !== opt);
        } else {
          return [...prev, opt];
        }
      });
    } else {
      // Single choice: submit immediately
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

  if (isLoading || externalLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mb-4"></div>
        <h2 className="text-xl font-bold text-slate-800">Carregando...</h2>
        <p className="text-slate-500">Preparando suas perguntas.</p>
      </div>
    );
  }

  // If no question and not loading, show error or redirect
  if (!currentQuestion && !isLoading) {
    if (error) {
      return (
        <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-6 text-center">
          <div className="bg-white rounded-2xl shadow-lg p-8 border border-slate-100 max-w-md">
            <h2 className="text-xl font-bold text-slate-800 mb-4">Erro ao carregar perguntas</h2>
            <p className="text-slate-600 mb-6">{error}</p>
            <button
              onClick={onFinish}
              className="w-full bg-primary-500 text-white font-bold py-3 px-4 rounded-lg hover:bg-primary-600 transition-colors"
            >
              Continuar para Dashboard
            </button>
          </div>
        </div>
      );
    }
    // No error but no question - redirect to dashboard
    onFinish();
    return null;
  }

  const progressPercent = status ? status.progress : 0;
  const questionNumber = status ? status.answered + 1 : 1;
  const totalQuestions = status?.total || 0;

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="w-full bg-slate-50 h-2">
        <div
          className="bg-primary-500 h-2 transition-all duration-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <div className="flex-1 flex flex-col max-w-lg mx-auto w-full p-6 justify-center">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {showDapCafInput ? (
          <form onSubmit={handleDapCafSubmit} className="flex flex-col gap-4">
            <div className="mb-8 animate-fade-in">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-primary-100 p-2 rounded-lg">
                  <MessageSquare className="text-primary-500 h-6 w-6" />
                </div>
                <span className="text-sm font-bold text-slate-400 uppercase tracking-wide">
                  Informação Adicional
                </span>
              </div>
              <h2 className="text-2xl font-bold text-primary-500 leading-snug">
                Qual é o número da sua DAP/CAF?
              </h2>
            </div>
            <div>
              <input
                ref={dapCafInputRef}
                type="text"
                placeholder="Digite o número da sua DAP/CAF"
                className="w-full p-4 border-2 border-slate-200 rounded-xl focus:border-primary-500 focus:outline-none text-lg"
                autoFocus
                disabled={isSubmitting}
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-primary-500 text-white font-bold py-4 rounded-xl hover:bg-primary-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Salvando...</span>
                </>
              ) : (
                'Continuar'
              )}
            </button>
          </form>
        ) : currentQuestion ? (
          <>
            <div className="mb-8 animate-fade-in">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-primary-100 p-2 rounded-lg">
                  <MessageSquare className="text-primary-500 h-6 w-6" />
                </div>
                <span className="text-sm font-bold text-slate-400 uppercase tracking-wide">
                  {totalQuestions > 0 ? `Pergunta ${questionNumber} de ${totalQuestions}` : 'Pergunta'}
                </span>
              </div>
              <h2 className="text-2xl font-bold text-primary-500 leading-snug">{currentQuestion.question_text}</h2>
            </div>

            <div className="space-y-3">
              {currentQuestion.question_type === 'boolean' && (
                <>
                  <button
                    onClick={() => handleChoiceClick('Sim')}
                    disabled={isSubmitting}
                    className="w-full text-left p-4 border-2 border-slate-100 rounded-xl hover:border-primary-500 hover:bg-primary-50 transition font-medium text-slate-700 active:scale-95 disabled:opacity-50"
                  >
                    Sim
                  </button>
                  <button
                    onClick={() => handleChoiceClick('Não')}
                    disabled={isSubmitting}
                    className="w-full text-left p-4 border-2 border-slate-100 rounded-xl hover:border-primary-500 hover:bg-primary-50 transition font-medium text-slate-700 active:scale-95 disabled:opacity-50"
                  >
                    Não
                  </button>
                </>
              )}

              {currentQuestion.question_type === 'choice' && currentQuestion.options && (
                <>
                  {currentQuestion.allow_multiple ? (
                    // Multi-select: show checkboxes
                    <>
                      {currentQuestion.options.map((opt) => {
                        const isSelected = selectedOptions.includes(opt);
                        return (
                          <button
                            key={opt}
                            type="button"
                            onClick={() => handleChoiceClick(opt)}
                            disabled={isSubmitting}
                            className={`w-full text-left p-4 border-2 rounded-xl transition font-medium active:scale-95 disabled:opacity-50 flex items-center gap-3 ${
                              isSelected
                                ? 'border-green-500 bg-green-50 text-slate-800'
                                : 'border-slate-100 hover:border-primary-500 hover:bg-primary-50 text-slate-700'
                            }`}
                          >
                            <div
                              className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 ${
                                isSelected
                                  ? 'bg-green-500 border-green-500'
                                  : 'border-slate-300 bg-white'
                              }`}
                            >
                              {isSelected && (
                                <svg
                                  className="w-3 h-3 text-white"
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
                            <span>{capitalize(opt)}</span>
                          </button>
                        );
                      })}
                      <button
                        onClick={handleMultiSelectSubmit}
                        disabled={isSubmitting || selectedOptions.length === 0}
                        className="mt-4 bg-primary-500 text-white font-bold py-4 rounded-xl hover:bg-primary-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        {isSubmitting ? (
                          <>
                            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                            <span>Salvando...</span>
                          </>
                        ) : (
                          'Continuar'
                        )}
                      </button>
                    </>
                  ) : (
                    // Single choice: show buttons that submit immediately
                    <>
                      {currentQuestion.options.map((opt) => (
                        <button
                          key={opt}
                          onClick={() => handleChoiceClick(opt)}
                          disabled={isSubmitting}
                          className="w-full text-left p-4 border-2 border-slate-100 rounded-xl hover:border-primary-500 hover:bg-primary-50 transition font-medium text-slate-700 active:scale-95 disabled:opacity-50"
                        >
                          {capitalize(opt)}
                        </button>
                      ))}
                    </>
                  )}
                </>
              )}

              {currentQuestion.question_type === 'text' && (
                <form onSubmit={handleTextSubmit} className="flex flex-col gap-4">
                  <input
                    ref={inputRef}
                    type="text"
                    placeholder="Digite sua resposta"
                    className="w-full p-4 border-2 border-slate-200 rounded-xl focus:border-primary-500 focus:outline-none text-lg"
                    autoFocus
                    disabled={isSubmitting}
                  />
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-primary-500 text-white font-bold py-4 rounded-xl hover:bg-primary-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Salvando...</span>
                      </>
                    ) : (
                      'Continuar'
                    )}
                  </button>
                </form>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
