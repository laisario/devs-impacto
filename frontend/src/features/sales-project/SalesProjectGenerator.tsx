import { useState } from 'react';
import { CheckCircle2, FileText, Loader2, Sparkles, X } from 'lucide-react';
import { generateSalesProjectDraft } from '../../services/api/sales-project';
import { ApiClientError } from '../../services/api/client';
import type { SalesProjectResponse, ProductItem } from '../../services/api/sales-project';

export function SalesProjectGenerator({
  onBack,
  onSave,
}: {
  onBack: () => void;
  onSave?: (project: SalesProjectResponse) => void;
}) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [project, setProject] = useState<SalesProjectResponse | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError('');
    setProject(null);

    try {
      const generated = await generateSalesProjectDraft({});
      setProject(generated);
      setIsEditing(false);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao gerar projeto. Tente novamente.');
      } else {
        setError('Erro ao gerar projeto. Tente novamente.');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = () => {
    if (project && onSave) {
      onSave(project);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const formatMonth = (month: string) => {
    const months: Record<string, string> = {
      february: 'Fevereiro',
      march: 'Março',
      april: 'Abril',
      may: 'Maio',
      june: 'Junho',
      july: 'Julho',
      august: 'Agosto',
      september: 'Setembro',
      october: 'Outubro',
      november: 'Novembro',
    };
    return months[month] || month;
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans flex flex-col relative">
      <header className="bg-white shadow-sm p-4 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto w-full">
          <button
            onClick={onBack}
            className="flex items-center text-slate-500 hover:text-slate-800 text-sm font-medium"
          >
            <X className="h-5 w-5 mr-1" />
            Voltar
          </button>
        </div>
      </header>

      <div className="flex-1 max-w-4xl mx-auto w-full p-6 pb-24">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Projeto de Venda para PNAE</h2>
            <p className="text-slate-600">
              Gere automaticamente um projeto de venda baseado no seu perfil e produtos. Você pode editar após a
              geração.
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {!project && (
            <div className="text-center py-12">
              <div className="mb-6">
                <div className="bg-gradient-to-r from-purple-100 to-blue-100 rounded-full p-6 inline-block mb-4">
                  <Sparkles className="h-12 w-12 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-800 mb-2">Gerar Projeto de Venda com IA</h3>
                <p className="text-slate-600 max-w-md mx-auto">
                  Nossa IA analisará seu perfil, produtos e capacidade de produção para criar um projeto de venda
                  personalizado para o PNAE.
                </p>
              </div>
              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-4 rounded-xl font-bold flex items-center gap-3 mx-auto disabled:opacity-50 disabled:cursor-not-allowed transition"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Gerando projeto...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-5 w-5" />
                    <span>Gerar Projeto com IA</span>
                  </>
                )}
              </button>
            </div>
          )}

          {project && (
            <div className="space-y-6">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-xl font-bold text-slate-800">Projeto Gerado</h3>
                    {project.ai_generated && (
                      <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full text-xs font-bold">
                        Gerado por IA
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-600">
                    Valor total: <span className="font-bold text-green-600">{formatCurrency(project.total_value)}</span>
                  </p>
                </div>
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className="text-sm text-purple-600 hover:text-purple-700 font-medium"
                >
                  {isEditing ? 'Visualizar' : 'Editar'}
                </button>
              </div>

              {project.notes && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">{project.notes}</p>
                </div>
              )}

              <div>
                <h4 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Produtos
                </h4>
                <div className="space-y-3">
                  {project.products.map((product: ProductItem, idx: number) => (
                    <div
                      key={idx}
                      className="bg-slate-50 rounded-lg p-4 border border-slate-200"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h5 className="font-bold text-slate-800">{product.name}</h5>
                          <p className="text-sm text-slate-600">
                            {product.quantity} {product.unit} × {formatCurrency(product.unit_price)} ={' '}
                            <span className="font-bold text-green-600">{formatCurrency(product.total_price)}</span>
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-500">Frequência: {product.delivery_frequency}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-bold text-slate-800 mb-4">Cronograma de Entrega</h4>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  {Object.entries(project.delivery_schedule).map(([month, data]) => {
                    if (!data || typeof data !== 'object') return null;
                    const monthData = data as { products?: string[]; quantity?: number };
                    return (
                      <div key={month} className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                        <p className="text-xs font-bold text-slate-600 mb-1">{formatMonth(month)}</p>
                        {monthData.products && monthData.products.length > 0 && (
                          <p className="text-xs text-slate-700">
                            {monthData.products.join(', ')}
                            {monthData.quantity && ` (${monthData.quantity})`}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="flex gap-4 pt-4 border-t border-slate-200">
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-800 px-6 py-3 rounded-lg font-bold transition disabled:opacity-50"
                >
                  Regenerar
                </button>
                {onSave && (
                  <button
                    onClick={handleSave}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-bold flex items-center justify-center gap-2 transition"
                  >
                    <CheckCircle2 className="h-5 w-5" />
                    Salvar Projeto
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

