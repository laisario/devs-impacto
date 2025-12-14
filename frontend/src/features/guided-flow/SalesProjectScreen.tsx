import React, { useState } from 'react';
import { Sparkles, Loader2, CheckCircle2, FileText } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';
import { generateSalesProjectDraft } from '../../services/api/sales-project';
import { ApiClientError } from '../../services/api/client';
import type { SalesProjectResponse } from '../../services/api/sales-project';

interface SalesProjectScreenProps {
  onSave: (project: SalesProjectResponse) => void;
  onBack: () => void;
}

export function SalesProjectScreen({ onSave, onBack }: SalesProjectScreenProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [project, setProject] = useState<SalesProjectResponse | null>(null);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError('');
    setProject(null);

    try {
      const generated = await generateSalesProjectDraft({});
      setProject(generated);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message || 'Erro ao criar projeto. Tente novamente.');
      } else {
        setError('Erro ao criar projeto. Tente novamente.');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  if (!project) {
    return (
      <ScreenWrapper
        title="Criar seu projeto de venda"
        subtitle="Vamos criar um projeto personalizado para você"
        primaryAction={{
          label: isGenerating ? 'Criando projeto...' : 'Criar projeto',
          onClick: handleGenerate,
          disabled: isGenerating,
        }}
        showBack
        onBack={onBack}
      >
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {isGenerating ? (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mb-4"></div>
            <p className="text-slate-600 text-lg">Criando seu projeto...</p>
          </div>
        ) : (
          <div className="flex justify-center mb-8">
            <div className="bg-gradient-to-r from-purple-100 to-blue-100 rounded-full p-8">
              <Sparkles className="h-16 w-16 text-purple-600" />
            </div>
          </div>
        )}
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper
      title="Projeto criado!"
      subtitle={`Valor total: ${formatCurrency(project.total_value)}`}
      primaryAction={{
        label: 'Salvar projeto',
        onClick: () => onSave(project),
      }}
      showBack
      onBack={onBack}
    >
      <div className="flex justify-center mb-6">
        <div className="bg-green-100 rounded-full p-8">
          <CheckCircle2 className="h-16 w-16 text-green-600" />
        </div>
      </div>

      {project.notes && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <p className="text-sm text-blue-800">{project.notes}</p>
        </div>
      )}

      <div className="mb-6">
        <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2 text-lg">
          <FileText className="h-5 w-5" />
          Produtos
        </h3>
        <div className="space-y-3">
          {project.products.map((product, idx) => (
            <div key={idx} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
              <h4 className="font-bold text-slate-800 mb-1">{product.name}</h4>
              <p className="text-sm text-slate-600">
                {product.quantity} {product.unit} × {formatCurrency(product.unit_price)} ={' '}
                <span className="font-bold text-green-600">{formatCurrency(product.total_price)}</span>
              </p>
            </div>
          ))}
        </div>
      </div>
    </ScreenWrapper>
  );
}
