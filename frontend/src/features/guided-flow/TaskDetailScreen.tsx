import React, { useState, useEffect } from 'react';
import { FileText, Lightbulb, Loader2, CheckCircle, ArrowRight } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';
import type { ChecklistItem } from '../../domain/models';
import type { FormalizationGuideResponse } from '../../services/api/types';
import { generateFormalizationGuide } from '../../services/api/ai';
import { ApiClientError } from '../../services/api/client';

interface TaskDetailScreenProps {
  task: ChecklistItem;
  taskNumber: number;
  totalTasks: number;
  onUploadDocument: () => void;
  onMarkComplete: () => void;
  onBack: () => void;
}

export function TaskDetailScreen({
  task,
  taskNumber,
  totalTasks,
  onUploadDocument,
  onMarkComplete,
  onBack,
}: TaskDetailScreenProps) {
  const [guide, setGuide] = useState<FormalizationGuideResponse | null>(null);
  const [isLoadingGuide, setIsLoadingGuide] = useState(false);
  const [guideError, setGuideError] = useState('');

  // Load guide automatically on mount
  useEffect(() => {
    const loadGuide = async () => {
      if (!task.requirementId) {
        setGuideError('Guia não disponível para esta tarefa');
        return;
      }

      setIsLoadingGuide(true);
      setGuideError('');

      try {
        const generatedGuide = await generateFormalizationGuide({
          requirement_id: task.requirementId,
        });
        setGuide(generatedGuide);
      } catch (err) {
        if (err instanceof ApiClientError) {
          setGuideError(err.message || 'Erro ao carregar guia. Tente novamente.');
        } else {
          setGuideError('Erro ao carregar guia. Tente novamente.');
        }
      } finally {
        setIsLoadingGuide(false);
      }
    };

    loadGuide();
  }, [task.requirementId]);

  const needsDocument = task.needUpload || task.relatedDocId;

  return (
    <ScreenWrapper
      title={task.title}
      subtitle={task.description}
      primaryAction={
        needsDocument
          ? {
              label: 'Enviar documento',
              onClick: onUploadDocument,
            }
          : {
              label: 'Marcar como feito',
              onClick: onMarkComplete,
            }
      }
      showBack
      onBack={onBack}
      progress={{
        current: taskNumber,
        total: totalTasks,
        label: `Tarefa ${taskNumber} de ${totalTasks}`,
      }}
    >
      {guideError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {guideError}
        </div>
      )}

      {needsDocument && (
        <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="h-6 w-6 text-green-600" />
            <p className="font-medium text-slate-800">Você precisa enviar um documento</p>
          </div>
          <p className="text-sm text-slate-600">
            Clique em "Enviar documento" para escolher o arquivo do seu celular.
          </p>
        </div>
      )}

      {task.priority === 'high' && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm font-medium text-red-800">
            Esta tarefa é muito importante. Faça ela primeiro!
          </p>
        </div>
      )}

      {/* Guide Section - Always visible when loaded */}
      <div className="mb-6 -mx-2 sm:mx-0">
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border-2 border-green-200 shadow-sm overflow-hidden">
          {/* Header */}
          <div className="bg-green-600 px-4 sm:px-6 py-4 sm:py-5">
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="bg-white/20 rounded-full p-2.5 sm:p-3 flex-shrink-0">
                <Lightbulb className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-base sm:text-lg font-bold text-white leading-tight">Como fazer esta tarefa</h3>
                <p className="text-xs sm:text-sm text-green-100 mt-0.5">Siga os passos abaixo</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="px-4 sm:px-6 py-5 sm:py-6">
            {isLoadingGuide && (
              <div className="flex flex-col items-center justify-center py-10 sm:py-12">
                <Loader2 className="h-8 w-8 sm:h-10 sm:w-10 text-green-600 animate-spin mb-4" />
                <p className="text-green-700 font-medium text-sm sm:text-base">Carregando guia...</p>
              </div>
            )}

            {guideError && (
              <div className="p-4 sm:p-5 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm sm:text-base leading-relaxed">{guideError}</p>
              </div>
            )}

            {guide && guide.steps && guide.steps.length > 0 && (
              <div className="space-y-4 sm:space-y-5">
                {guide.steps.map((step, idx) => (
                  <div
                    key={idx}
                    className="bg-white rounded-lg border border-green-100 p-4 sm:p-6 shadow-sm"
                  >
                    <div className="flex gap-3 sm:gap-4">
                      {/* Step Number */}
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gradient-to-br from-green-500 to-green-600 text-white font-bold flex items-center justify-center text-base sm:text-lg shadow-md">
                          {idx + 1}
                        </div>
                      </div>

                      {/* Step Content */}
                      <div className="flex-1 min-w-0">
                        {step.title && (
                          <h4 className="text-base sm:text-lg font-bold text-slate-800 mb-2 sm:mb-3 leading-tight">
                            {step.title}
                          </h4>
                        )}
                        <p className="text-sm sm:text-base text-slate-700 leading-relaxed sm:leading-loose">
                          {step.description}
                        </p>
                      </div>

                      {/* Arrow Icon - Hidden on mobile, shown on larger screens */}
                      {idx < guide.steps.length - 1 && (
                        <div className="hidden sm:flex flex-shrink-0 items-start pt-1">
                          <ArrowRight className="h-5 w-5 text-green-400" />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {guide && guide.summary && (
              <div className="mt-5 sm:mt-6 p-4 sm:p-5 bg-white/80 backdrop-blur-sm rounded-lg border-2 border-green-200">
                <div className="flex items-start gap-3 sm:gap-4">
                  <CheckCircle className="h-5 w-5 sm:h-6 sm:w-6 text-green-600 flex-shrink-0 mt-0.5" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm sm:text-base font-bold text-green-800 mb-1.5 sm:mb-2">Resumo</p>
                    <p className="text-sm sm:text-base text-slate-700 leading-relaxed sm:leading-loose">{guide.summary}</p>
                  </div>
                </div>
              </div>
            )}

            {!isLoadingGuide && !guide && !guideError && (
              <div className="text-center py-8 sm:py-10">
                <p className="text-slate-500 text-sm sm:text-base">Guia não disponível para esta tarefa</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </ScreenWrapper>
  );
}
