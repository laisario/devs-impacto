import { Info, ShieldCheck, Sparkles } from 'lucide-react';
import type { FormalizationGuideResponse } from '../../../services/api/types';
import { GuideStepCard } from './GuideStepCard';
import { getConfidenceLabel, getConfidenceBadgeClass } from '../utils/confidence';

interface GuideDisplayProps {
  guide: FormalizationGuideResponse;
  onRegenerate: () => void;
  isLoading: boolean;
}

export function GuideDisplay({ guide, onRegenerate, isLoading }: GuideDisplayProps) {
  return (
    <div className="bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 rounded-xl border-2 border-purple-300 shadow-lg overflow-hidden">
      {/* Header destacado com badge de IA */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-white/20 backdrop-blur-sm p-2 rounded-lg">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <h3 className="font-bold text-lg flex items-center gap-2">
                Guia Personalizado
                <span className="bg-white/30 text-white text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wide">
                  Gerado por IA
                </span>
              </h3>
              <p className="text-xs text-white/90 mt-0.5">
                Adaptado especialmente para você
              </p>
            </div>
          </div>
          <button
            onClick={onRegenerate}
            disabled={isLoading}
            className="bg-white/20 hover:bg-white/30 text-white px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition backdrop-blur-sm"
            title="Regenerar guia"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
            ) : (
              <Sparkles className="h-3 w-3" />
            )}
            Regenerar
          </button>
        </div>
      </div>

      <div className="p-6 space-y-5">
        {/* Resumo destacado */}
        <div className="bg-white/80 backdrop-blur-sm p-4 rounded-lg border border-purple-200 shadow-sm">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-purple-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-800 leading-relaxed">{guide.summary}</p>
            </div>
          </div>
        </div>

        {/* Passos do guia */}
        <div>
          <h4 className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
            <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded text-xs">PASSO A PASSO</span>
          </h4>
          <div className="space-y-3">
            {guide.steps.map((step) => (
              <GuideStepCard key={step.step} step={step} />
            ))}
          </div>
        </div>

        {/* Informações adicionais em grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="bg-white/80 backdrop-blur-sm p-4 rounded-lg border border-purple-200 shadow-sm">
            <p className="text-xs font-bold text-slate-600 mb-1.5 flex items-center gap-2">
              <span className="text-purple-600">⏱️</span>
              Tempo Estimado
            </p>
            <p className="text-base font-bold text-slate-800">{guide.estimated_time_days} dias</p>
          </div>

          {guide.where_to_go.length > 0 && (
            <div className="bg-white/80 backdrop-blur-sm p-4 rounded-lg border border-purple-200 shadow-sm">
              <p className="text-xs font-bold text-slate-600 mb-2 flex items-center gap-2">
                <span className="text-blue-600">📍</span>
                Onde ir
              </p>
              <ul className="space-y-1.5">
                {guide.where_to_go.map((location, idx) => (
                  <li key={idx} className="text-sm text-slate-700 flex items-start gap-2">
                    <span className="text-purple-500 mt-1">•</span>
                    <span>{location}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Nível de confiança */}
        <div className="flex items-center justify-between pt-3 border-t border-purple-200">
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <ShieldCheck className="h-4 w-4 text-purple-600" />
            <span>Nível de confiança da IA:</span>
            <span className={`font-bold px-2 py-0.5 rounded ${getConfidenceBadgeClass(guide.confidence_level)}`}>
              {getConfidenceLabel(guide.confidence_level)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
