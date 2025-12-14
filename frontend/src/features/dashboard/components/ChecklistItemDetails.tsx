import { useMemo, useState } from 'react';
import { CheckCircle2, ChevronLeft, FileText, Info, Lightbulb, ShieldCheck, Upload } from 'lucide-react';
import type { ChecklistItem, Document } from '../../../domain/models';

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

  const relatedDoc = useMemo(
    () => (item.relatedDocId ? documents.find((d) => d.id === item.relatedDocId) : undefined),
    [documents, item.relatedDocId]
  );

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

                <button
                  onClick={() => onUploadDoc(relatedDoc.id)}
                  disabled={relatedDoc.status !== 'missing'}
                  className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <Upload className="h-4 w-4" />
                  {relatedDoc.status === 'missing' ? 'Fazer Upload Agora' : 'Upload Concluído'}
                </button>
              </div>

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
