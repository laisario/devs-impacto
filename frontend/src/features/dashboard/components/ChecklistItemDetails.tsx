import { useMemo, useState } from 'react';
import { CheckCircle2, ChevronLeft, FileText, Info, Lightbulb, ShieldCheck, Upload, Sparkles } from 'lucide-react';
import type { ChecklistItem, Document } from '../../../domain/models';
import type { FormalizationGuideResponse } from '../../../services/api/types';
import { generateFormalizationGuide } from '../../../services/api/ai';
import { ApiClientError } from '../../../services/api/client';
import { useFileUpload } from '../hooks/useFileUpload';
import { AIGuideSection } from './AIGuideSection';
import { ERROR_MESSAGES, UI_MESSAGES } from '../constants/messages';

export function ChecklistItemDetails({
  item,
  documents,
  onBack,
  onMarkDone,
  onUploadDoc,
}: {
  item: ChecklistItem;
  documents: Document[];
  onBack: () => void;
  onMarkDone: (id: string) => void;
  onUploadDoc: (id: string) => void;
}) {
  const [expandedStepHelp, setExpandedStepHelp] = useState<number | null>(null);
  const [aiGuide, setAiGuide] = useState<FormalizationGuideResponse | null>(null);
  const [isLoadingGuide, setIsLoadingGuide] = useState(false);
  const [guideError, setGuideError] = useState('');

  const relatedDoc = useMemo(
    () => (item.relatedDocId ? documents.find((d) => d.id === item.relatedDocId) : undefined),
    [documents, item.relatedDocId]
  );

  const fileUpload = useFileUpload({
    relatedDoc,
    needUpload: item.needUpload,
    onUploadDoc,
  });

  const handleGenerateGuide = async () => {
    if (!item.requirementId) {
      setGuideError(ERROR_MESSAGES.NO_GUIDE_AVAILABLE);
      return;
    }

    setIsLoadingGuide(true);
    setGuideError('');

    try {
      const guide = await generateFormalizationGuide({
        requirement_id: item.requirementId,
      });
      setAiGuide(guide);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setGuideError(err.message || ERROR_MESSAGES.GUIDE_GENERATION_ERROR);
      } else {
        setGuideError(ERROR_MESSAGES.GUIDE_GENERATION_ERROR);
      }
    } finally {
      setIsLoadingGuide(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans flex flex-col relative">
      <header className="bg-white shadow-sm p-4 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto w-full">
          <button onClick={onBack} className="flex items-center text-slate-500 hover:text-slate-800 text-sm font-medium">
            <ChevronLeft className="h-5 w-5 mr-1" />
            Voltar ao Checklist
          </button>
        </div>
      </header>

      <div className="flex-1 max-w-3xl mx-auto w-full p-6 pb-24">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-primary-500 mb-2">{item.title}</h2>
              <p className="text-slate-500">{item.description}</p>
            </div>
            {item.priority === 'high' && (
              <span className="bg-red-100 text-red-700 text-xs font-bold px-3 py-1 rounded-full uppercase">{UI_MESSAGES.IMPORTANT}</span>
            )}
          </div>

          <AIGuideSection
            requirementId={item.requirementId}
            guide={aiGuide}
            isLoading={isLoadingGuide}
            error={guideError}
            onGenerate={handleGenerateGuide}
          />

          {item.detailedSteps && item.detailedSteps.length > 0 && (
            <div className="mb-10">
              <h3 className="font-bold text-lg text-slate-800 mb-4 flex items-center gap-2">
                <Info className="h-5 w-5 text-blue-500" />
                Passo a Passo
              </h3>

              <div className="space-y-4">
                {item.detailedSteps.map((step, idx) => (
                  <div key={idx} className="flex flex-col gap-3">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-sm border border-blue-100">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-slate-700 mt-1">{step.text}</p>

                        {step.helpContent && (
                          <button
                            onClick={() => setExpandedStepHelp(expandedStepHelp === idx ? null : idx)}
                            className="mt-2 text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1.5 transition"
                          >
                            {expandedStepHelp === idx ? (
                              <>{UI_MESSAGES.HIDE_GUIDE}</>
                            ) : (
                              <>
                                <Lightbulb className="h-3 w-3" />
                                {UI_MESSAGES.USEFUL_TIP}
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    </div>

                    {expandedStepHelp === idx && step.helpContent && (
                      <div className="ml-12 bg-blue-50 border border-blue-100 rounded-lg p-4 animate-in slide-in-from-top-2 fade-in">
                        <h4 className="font-bold text-sm text-blue-800 mb-2 flex items-center gap-2">
                          <Info className="h-4 w-4" />
                          {step.helpContent.title}
                        </h4>
                        <p className="text-sm text-blue-700 leading-relaxed">{step.helpContent.description}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {(relatedDoc || item.needUpload) && (
            <div className="bg-slate-50 rounded-lg p-6 border border-slate-200">
              <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                <FileText className="h-5 w-5 text-green-600" />
                {relatedDoc ? `Documento Necessário: ${relatedDoc.name}` : 'Enviar Documento'}
              </h3>
              <p className="text-sm text-slate-500 mb-4">
                {relatedDoc
                  ? 'Após concluir os passos acima, envie a foto ou PDF do documento aqui para validação.'
                  : 'Envie uma foto ou PDF do documento relacionado a esta tarefa.'}
              </p>

              <div className="flex items-center gap-4">
                {relatedDoc && (
                  <div className="flex-1">
                    {relatedDoc.status === 'missing' && (
                      <span className="text-xs bg-slate-200 text-slate-600 px-2 py-1 rounded font-bold">{UI_MESSAGES.PENDING}</span>
                    )}
                    {(relatedDoc.status === 'uploaded' || relatedDoc.status === 'ai_reviewed') && (
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded font-bold">{UI_MESSAGES.SENT}</span>
                    )}
                  </div>
                )}

                <input
                  ref={fileUpload.fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={fileUpload.handleFileSelect}
                  className="hidden"
                  disabled={fileUpload.isUploading || (relatedDoc?.status === 'uploaded' || relatedDoc?.status === 'ai_reviewed')}
                />

                <button
                  onClick={fileUpload.handleUploadClick}
                  disabled={fileUpload.isUploading || (relatedDoc?.status === 'uploaded' || relatedDoc?.status === 'ai_reviewed')}
                  className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {fileUpload.isUploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>{UI_MESSAGES.UPLOADING}</span>
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      {relatedDoc?.status === 'missing' || !relatedDoc ? UI_MESSAGES.UPLOAD_NOW : UI_MESSAGES.UPLOAD_COMPLETE}
                    </>
                  )}
                </button>
              </div>

              {fileUpload.uploadProgress > 0 && fileUpload.uploadProgress < 100 && (
                <div className="mt-3">
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 transition-all duration-300"
                      style={{ width: `${fileUpload.uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {fileUpload.uploadError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                  {fileUpload.uploadError}
                </div>
              )}

              {relatedDoc?.aiNotes && (
                <div className="mt-4 bg-gradient-to-r from-primary-50 to-primary-100 p-4 rounded-lg border-2 border-primary-300 shadow-sm">
                  <div className="flex items-start gap-3">
                    <div className="bg-primary-500 p-2 rounded-lg shrink-0">
                      <ShieldCheck className="h-5 w-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className="bg-primary-600 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5">
                          <Sparkles className="h-3 w-3" />
                          Validado por IA
                        </span>
                        {relatedDoc.aiConfidence && (
                          <span className="bg-primary-100 text-primary-800 px-2.5 py-1 rounded-full text-xs font-medium">
                            Confiança: {relatedDoc.aiConfidence}
                          </span>
                        )}
                      </div>
                      <div className="bg-white/80 backdrop-blur-sm p-3 rounded border border-primary-200">
                        <p className="text-sm text-slate-700 leading-relaxed font-medium">{relatedDoc.aiNotes}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="mt-10 pt-6 border-t border-slate-100 flex justify-end">
            <button
              onClick={() => onMarkDone(item.id)}
              className={`px-6 py-3 rounded-lg font-bold transition flex items-center gap-2 ${
                item.status === 'done' ? 'bg-primary-100 text-primary-700' : 'bg-primary-500 text-white hover:bg-primary-600'
              }`}
            >
              <CheckCircle2 className="h-5 w-5" />
              {item.status === 'done' ? UI_MESSAGES.TASK_COMPLETE : UI_MESSAGES.MARK_AS_COMPLETE}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
