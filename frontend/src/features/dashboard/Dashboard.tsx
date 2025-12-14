import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  FileText,
  Leaf,
  ShieldCheck,
  Upload,
  User,
} from 'lucide-react';
import type { ChecklistItem, Document, UserProfile } from '../../domain/models';
import { ChatWidget } from '../chat/ChatWidget';
import { ChecklistItemDetails } from './components/ChecklistItemDetails';
import { getFormalizationTasks, getFormalizationStatus } from '../../services/api/formalization';
import { getDocuments } from '../../services/api/documents';
import { getProducerProfile } from '../../services/api/producer';
import { ApiClientError } from '../../services/api/client';
import type { FormalizationTaskResponse, DocumentResponse } from '../../services/api/types';

export function Dashboard({
  user,
  checklist,
  documents,
  setChecklist,
  setDocuments,
  onEscalate,
  onLogout,
}: {
  user: UserProfile | null;
  checklist: ChecklistItem[];
  documents: Document[];
  setChecklist: React.Dispatch<React.SetStateAction<ChecklistItem[]>>;
  setDocuments: React.Dispatch<React.SetStateAction<Document[]>>;
  onEscalate: () => void;
  onLogout: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'checklist' | 'docs'>('checklist');
  const [selectedItem, setSelectedItem] = useState<ChecklistItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [formalizationStatus, setFormalizationStatus] = useState<{ isEligible: boolean; score: number; eligibilityLevel: string } | null>(null);

  // Map backend task to frontend checklist item
  const mapTaskToChecklistItem = (task: FormalizationTaskResponse): ChecklistItem => ({
    id: task.id,
    title: task.title,
    description: task.description,
    priority: task.priority,
    status: task.completed ? 'done' : 'todo',
    taskId: task.task_id,
    category: task.category,
    requirementId: task.requirement_id || undefined,
  });

  // Map backend document to frontend document
  const mapDocumentResponse = (doc: DocumentResponse): Document => ({
    id: doc.id,
    type: doc.doc_type,
    name: doc.original_filename,
    status: 'uploaded', // Documents from API are already uploaded
    fileUrl: doc.file_url,
    uploadedAt: doc.uploaded_at,
  });

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError('');

      try {
        // Load tasks
        const tasks = await getFormalizationTasks();
        const mappedTasks = tasks.map(mapTaskToChecklistItem);
        setChecklist(mappedTasks);

        // Load documents
        const docsResponse = await getDocuments();
        const mappedDocs = docsResponse.items.map(mapDocumentResponse);
        setDocuments(mappedDocs);

        // Load formalization status
        try {
          const status = await getFormalizationStatus();
          setFormalizationStatus({
            isEligible: status.is_eligible,
            score: status.score,
            eligibilityLevel: status.eligibility_level,
          });
        } catch (err) {
          // Status might not be available yet
          console.warn('Could not load formalization status:', err);
        }

        // Load producer profile if user is not set
        if (!user) {
          try {
            const profile = await getProducerProfile();
            if (profile) {
              // Profile will be handled by parent component
            }
          } catch (err) {
            // Profile might not exist yet
            console.warn('Could not load producer profile:', err);
          }
        }
      } catch (err) {
        if (err instanceof ApiClientError) {
          setError(err.message || 'Erro ao carregar dados. Tente novamente.');
        } else {
          setError('Erro ao carregar dados. Tente novamente.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  const toggleItem = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setChecklist((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: item.status === 'done' ? 'todo' : 'done' } : item))
    );
    // TODO: Update task completion status in backend when endpoint is available
  };

  const uploadDoc = (id: string) => {
    // This will be handled by ChecklistItemDetails with real upload
    setDocuments((prev) => prev.map((doc) => (doc.id === id ? { ...doc, status: 'uploaded' } : doc)));
  };

  const progress = checklist.length
    ? Math.round((checklist.filter((i) => i.status === 'done').length / checklist.length) * 100)
    : 0;
  const isRisky = user?.caseType === 'needs_human' || formalizationStatus?.eligibilityLevel === 'not_eligible';

  const openDetails = (item: ChecklistItem) => {
    setSelectedItem(item);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Carregando dados...</p>
        </div>
      </div>
    );
  }

  if (selectedItem) {
    return (
      <>
        <ChecklistItemDetails
          item={selectedItem}
          documents={documents}
          onBack={() => setSelectedItem(null)}
          onUploadDoc={uploadDoc}
          onMarkDone={(id) => {
            if (selectedItem.status !== 'done') toggleItem(id);
            setSelectedItem(null);
          }}
        />
        <ChatWidget userName={user?.name || 'Usuário'} />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 font-sans relative">
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="bg-green-600 rounded-full p-1.5">
              <Leaf className="text-white h-4 w-4" />
            </div>
            <span className="font-bold text-slate-800 hidden sm:inline">CertificaFácil</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-bold text-slate-800">{user?.name || 'Usuário'}</p>
              <p className="text-xs text-slate-500">{user?.city || ''}</p>
            </div>
            <div className="h-8 w-8 bg-slate-200 rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-slate-500" />
            </div>
            <button onClick={onLogout} className="text-xs text-slate-400 hover:text-red-500">
              Sair
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto p-4 md:p-8 pb-24">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
            {error}
          </div>
        )}

        {formalizationStatus && (
          <div className={`mb-6 p-4 rounded-xl border ${
            formalizationStatus.isEligible
              ? 'bg-green-50 border-green-200'
              : formalizationStatus.eligibilityLevel === 'partially_eligible'
              ? 'bg-yellow-50 border-yellow-200'
              : 'bg-orange-50 border-orange-200'
          }`}>
            <div className="flex items-start gap-4">
              {formalizationStatus.isEligible ? (
                <CheckCircle2 className="text-green-600 h-6 w-6 shrink-0 mt-1" />
              ) : (
                <AlertTriangle className="text-orange-600 h-6 w-6 shrink-0 mt-1" />
              )}
              <div>
                <h3 className={`font-bold ${
                  formalizationStatus.isEligible ? 'text-green-800' : 'text-orange-800'
                }`}>
                  {formalizationStatus.isEligible
                    ? 'Você está elegível para vender em programas públicos!'
                    : `Elegibilidade: ${formalizationStatus.eligibilityLevel === 'partially_eligible' ? 'Parcial' : 'Não elegível'}`}
                </h3>
                <p className={`text-sm mt-1 ${
                  formalizationStatus.isEligible ? 'text-green-700' : 'text-orange-700'
                }`}>
                  Pontuação: {formalizationStatus.score}/100
                </p>
              </div>
            </div>
          </div>
        )}

        {isRisky && (
          <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 mb-6 flex items-start gap-4">
            <AlertTriangle className="text-orange-600 h-6 w-6 shrink-0 mt-1" />
            <div>
              <h3 className="font-bold text-orange-800">Atenção: Seu caso possui complexidade</h3>
              <p className="text-sm text-orange-700 mt-1">
                {user?.riskFlags && user.riskFlags.length > 0 ? (
                  <>
                    Detectamos <strong>{user.riskFlags.join(', ')}</strong>. Isso geralmente exige RT (Responsável
                    Técnico) ou aprovação sanitária específica.
                  </>
                ) : (
                  'Seu caso pode exigir atenção especial. Consulte um especialista.'
                )}
              </p>
              <button
                onClick={onEscalate}
                className="mt-3 text-sm bg-orange-100 text-orange-800 font-bold px-3 py-1.5 rounded hover:bg-orange-200 transition"
              >
                Ver Consultores Recomendados
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-xs font-bold text-slate-400 uppercase mb-1">Status Geral</p>
            <div className="flex items-center gap-2">
              <div className={`h-3 w-3 rounded-full ${progress === 100 ? 'bg-green-500' : 'bg-yellow-500'}`} />
              <span className="text-xl font-bold text-slate-800">
                {progress === 100 ? 'Pronto para Venda' : 'Em Preparação'}
              </span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-xs font-bold text-slate-400 uppercase mb-1">Seu Progresso</p>
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold text-slate-800">{progress}%</span>
              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-green-500 transition-all duration-1000" style={{ width: `${progress}%` }} />
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm">
            <p className="text-xs font-bold text-slate-400 uppercase mb-1">Próxima Ação</p>
            <p className="text-sm font-medium text-slate-700 truncate">
              {checklist.find((i) => i.status !== 'done')?.title || 'Tudo completo!'}
            </p>
          </div>
        </div>

        <div className="flex gap-6 mb-4 border-b border-slate-200">
          <button
            onClick={() => setActiveTab('checklist')}
            className={`pb-3 text-sm font-bold transition ${
              activeTab === 'checklist' ? 'text-green-600 border-b-2 border-green-600' : 'text-slate-500'
            }`}
          >
            Checklist de Tarefas
          </button>
          <button
            onClick={() => setActiveTab('docs')}
            className={`pb-3 text-sm font-bold transition ${
              activeTab === 'docs' ? 'text-green-600 border-b-2 border-green-600' : 'text-slate-500'
            }`}
          >
            Meus Documentos
          </button>
        </div>

        {activeTab === 'checklist' && (
          <div className="space-y-3">
            {checklist.map((item) => (
              <div
                key={item.id}
                onClick={() => openDetails(item)}
                className={`group bg-white p-4 rounded-lg border shadow-sm transition-all hover:shadow-md hover:border-green-300 cursor-pointer flex items-start gap-4 ${
                  item.status === 'done' ? 'border-green-200 bg-green-50/30' : 'border-slate-100'
                }`}
              >
                <div
                  onClick={(e) => toggleItem(item.id, e)}
                  className={`mt-1 h-6 w-6 rounded border-2 flex items-center justify-center transition-colors z-10 ${
                    item.status === 'done'
                      ? 'bg-green-500 border-green-500 text-white'
                      : 'border-slate-300 text-transparent hover:border-green-400'
                  }`}
                >
                  <CheckCircle2 className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <h4 className={`font-bold text-slate-800 ${item.status === 'done' ? 'line-through text-slate-400' : ''}`}>
                      {item.title}
                    </h4>
                    {item.priority === 'high' && item.status !== 'done' && (
                      <span className="text-[10px] font-bold bg-red-100 text-red-600 px-2 py-0.5 rounded-full uppercase">
                        Alta Prioridade
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-500 mt-1">{item.description}</p>

                  <div className="mt-3 flex items-center text-xs text-green-600 font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                    Ver passo a passo <ChevronRight className="h-3 w-3 ml-1" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'docs' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documents.map((doc) => (
              <div key={doc.id} className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-2">
                    <FileText className="text-slate-400 h-5 w-5" />
                    <span className="font-bold text-slate-700">{doc.name}</span>
                  </div>
                  {doc.status === 'missing' && (
                    <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded">Pendente</span>
                  )}
                  {(doc.status === 'uploaded' || doc.status === 'ai_reviewed') && (
                    <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">Enviado</span>
                  )}
                </div>

                {doc.aiNotes && (
                  <div className="mb-4 bg-green-50 p-3 rounded text-xs text-green-800 flex gap-2">
                    <ShieldCheck className="h-4 w-4 shrink-0" />
                    {doc.aiNotes}
                  </div>
                )}

                <button
                  onClick={() => uploadDoc(doc.id)}
                  disabled={doc.status !== 'missing'}
                  className="w-full border-2 border-dashed border-slate-300 rounded-lg p-3 text-slate-500 text-sm font-medium hover:border-green-500 hover:text-green-600 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Upload className="h-4 w-4" />
                  {doc.status === 'missing' ? 'Fazer Upload' : 'Documento Enviado'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <ChatWidget userName={user?.name || 'Usuário'} />
    </div>
  );
}
