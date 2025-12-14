import { Sparkles } from 'lucide-react';

interface GuidePromptProps {
  onGenerate: () => void;
  isLoading: boolean;
}

export function GuidePrompt({ onGenerate, isLoading }: GuidePromptProps) {
  return (
    <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-bold text-purple-800 flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Guia Personalizado de Formalização
            </h3>
          </div>
          <p className="text-sm text-purple-700">
            Obtenha um guia passo a passo personalizado gerado por IA para completar este requisito.
            <span className="block mt-1 text-xs text-purple-600">
              O guia será adaptado ao seu perfil, localização e situação atual.
            </span>
          </p>
        </div>
        <button
          onClick={onGenerate}
          disabled={isLoading}
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition whitespace-nowrap shadow-md"
        >
          {isLoading ? (
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
    </div>
  );
}
