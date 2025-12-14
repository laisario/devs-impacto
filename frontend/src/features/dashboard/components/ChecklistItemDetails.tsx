import { useMemo, useState, useRef } from 'react';
import { CheckCircle2, ChevronLeft, FileText, Info, Lightbulb, ShieldCheck, Upload, Sparkles } from 'lucide-react';
import type { ChecklistItem, Document } from '../../../domain/models';
import { uploadDocument } from '../../../services/api/documents';
import { generateFormalizationGuide } from '../../../services/api/ai';
import { ApiClientError } from '../../../services/api/client';
import type { FormalizationGuideResponse } from '../../../services/api/types';

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
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [aiGuide, setAiGuide] = useState<FormalizationGuideResponse | null>(null);
  const [isLoadingGuide, setIsLoadingGuide] = useState(false);
  const [guideError, setGuideError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const relatedDoc = useMemo(
    () => (item.relatedDocId ? documents.find((d) => d.id === item.relatedDocId) : undefined),
    [documents, item.relatedDocId]
  );

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !relatedDoc) return;

    setIsUploading(true);
    setUploadError('');
    setUploadProgress(0);

    try {
      // Map document type - you may need to adjust this mapping based on your needs
      const docTypeMap: Record<string, string> = {
        'identidade': 'cpf',
        'caf': 'dap_caf',
        'residencia': 'proof_address',
        'nota_fiscal': 'other',
      };
      const docType = docTypeMap[relatedDoc.type] || relatedDoc.type || 'other';

      await uploadDocument(file, docType);
      
      // Update document status
      onUploadDoc(relatedDoc.id);
      setUploadProgress(100);
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setUploadError(err.message || 'Erro ao fazer upload. Tente novamente.');
      } else {
        setUploadError('Erro ao fazer upload. Tente novamente.');
      }
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 2000);
    }
  };

  const handleUploadClick = () => {
    if (relatedDoc?.status === 'missing' && fileInputRef.current) {
      fileInputRef.current.click();
    } else {
      onUploadDoc(relatedDoc?.id || '');
    }
  };

  const handleGenerateGuide = async () => {
    if (!item.requirementId) {
      setGuideError('Este item não possui um guia de formalização disponível.');
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
        setGuideError(err.message || 'Erro ao gerar guia. Tente novamente.');
      } else {
        setGuideError('Erro ao gerar guia. Tente novamente.');
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
              <h2 className="text-2xl font-bold text-slate-800 mb-2">{item.title}</h2>
              <p className="text-slate-500">{item.description}</p>
            </div>
            {item.priority === 'high' && (
              <span className="bg-red-100 text-red-700 text-xs font-bold px-3 py-1 rounded-full uppercase">Importante</span>
            )}
          </div>

          {item.requirementId && (
            <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <h3 className="font-bold text-purple-800 mb-2 flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    Guia Personalizado de Formalização
                  </h3>
                  <p className="text-sm text-purple-700">
                    Obtenha um guia passo a passo personalizado gerado por IA para completar este requisito.
                  </p>
                </div>
                <button
                  onClick={handleGenerateGuide}
                  disabled={isLoadingGuide}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition whitespace-nowrap"
                >
                  {isLoadingGuide ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Gerando...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      <span>Gerar Guia</span>
                    </>
                  )}
                </button>
              </div>

              {guideError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                  {guideError}
                </div>
              )}

              {aiGuide && (
                <div className="mt-4 space-y-4">
                  <div className="bg-white p-4 rounded border border-purple-100">
                    <p className="text-sm text-slate-700">{aiGuide.summary}</p>
                  </div>

                  <div className="space-y-3">
                    {aiGuide.steps.map((step) => (
                      <div key={step.step} className="bg-white p-4 rounded border border-purple-100">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 h-6 w-6 rounded-full bg-purple-100 text-purple-700 font-bold flex items-center justify-center text-xs">
                            {step.step}
                          </div>
                          <div className="flex-1">
                            <h4 className="font-bold text-sm text-slate-800 mb-1">{step.title}</h4>
                            <p className="text-sm text-slate-600">{step.description}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="bg-white p-4 rounded border border-purple-100">
                    <p className="text-xs font-bold text-slate-600 mb-2">Tempo Estimado:</p>
                    <p className="text-sm text-slate-700">{aiGuide.estimated_time_days} dias</p>
                  </div>

                  {aiGuide.where_to_go.length > 0 && (
                    <div className="bg-white p-4 rounded border border-purple-100">
                      <p className="text-xs font-bold text-slate-600 mb-2">Onde ir:</p>
                      <ul className="space-y-1">
                        {aiGuide.where_to_go.map((location, idx) => (
                          <li key={idx} className="text-sm text-slate-700">• {location}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="text-xs text-slate-500">
                    Nível de confiança: <span className="font-bold">{aiGuide.confidence_level}</span>
                  </div>
                </div>
              )}
            </div>
          )}

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
                              <>Ocultar guia</>
                            ) : (
                              <>
                                <Lightbulb className="h-3 w-3" />
                                Dica útil
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

          {relatedDoc && (
            <div className="bg-slate-50 rounded-lg p-6 border border-slate-200">
              <h3 className="font-bold text-slate-800 mb-2 flex items-center gap-2">
                <FileText className="h-5 w-5 text-green-600" />
                Documento Necessário: {relatedDoc.name}
              </h3>
              <p className="text-sm text-slate-500 mb-4">
                Após concluir os passos acima, envie a foto ou PDF do documento aqui para validação.
              </p>

              <div className="flex items-center gap-4">
                <div className="flex-1">
                  {relatedDoc.status === 'missing' && (
                    <span className="text-xs bg-slate-200 text-slate-600 px-2 py-1 rounded font-bold">Pendente</span>
                  )}
                  {(relatedDoc.status === 'uploaded' || relatedDoc.status === 'ai_reviewed') && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded font-bold">Enviado</span>
                  )}
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={isUploading || relatedDoc.status !== 'missing'}
                />

                <button
                  onClick={handleUploadClick}
                  disabled={relatedDoc.status !== 'missing' || isUploading}
                  className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {isUploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Enviando...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      {relatedDoc.status === 'missing' ? 'Fazer Upload Agora' : 'Upload Concluído'}
                    </>
                  )}
                </button>
              </div>

              {uploadProgress > 0 && uploadProgress < 100 && (
                <div className="mt-3">
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}

              {uploadError && (
                <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                  {uploadError}
                </div>
              )}

              {relatedDoc.aiNotes && (
                <div className="mt-4 bg-white p-3 rounded border border-green-200 text-xs text-green-800 flex gap-2">
                  <ShieldCheck className="h-4 w-4 shrink-0" />
                  {relatedDoc.aiNotes}
                </div>
              )}
            </div>
          )}

          <div className="mt-10 pt-6 border-t border-slate-100 flex justify-end">
            <button
              onClick={() => onMarkDone(item.id)}
              className={`px-6 py-3 rounded-lg font-bold transition flex items-center gap-2 ${
                item.status === 'done' ? 'bg-green-100 text-green-700' : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              <CheckCircle2 className="h-5 w-5" />
              {item.status === 'done' ? 'Tarefa Concluída' : 'Marcar como Concluído'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
