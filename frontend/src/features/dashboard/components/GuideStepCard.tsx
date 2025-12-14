import { FileText } from 'lucide-react';
import type { GuideStep } from '../../../services/api/types';

interface GuideStepCardProps {
  step: GuideStep;
}

export function GuideStepCard({ step }: GuideStepCardProps) {
  return (
    <div className="bg-white/90 backdrop-blur-sm p-4 rounded-lg border border-purple-200 shadow-sm hover:shadow-md transition">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 h-8 w-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 text-white font-bold flex items-center justify-center text-sm shadow-md">
          {step.step}
        </div>
        <div className="flex-1 space-y-2">
          <h5 className="font-bold text-sm text-slate-800">{step.title}</h5>
          <p className="text-sm text-slate-600 leading-relaxed">{step.description}</p>
          
          {/* Documents Checklist */}
          {step.documents_checklist && step.documents_checklist.length > 0 && (
            <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-xs font-bold text-blue-800 mb-2 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Documentos necessários para este passo:
              </p>
              <ul className="space-y-1">
                {step.documents_checklist.map((doc, docIdx) => (
                  <li key={docIdx} className="text-xs text-blue-700 flex items-start gap-2">
                    <span className="text-blue-500 mt-1">✓</span>
                    <span>{doc}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Address and Map Link */}
          {step.address && (
            <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
              <p className="text-xs font-bold text-green-800 mb-2 flex items-center gap-2">
                <span className="text-green-600">📍</span>
                Endereço:
              </p>
              <p className="text-sm text-green-700 mb-2">{step.address}</p>
              {step.map_link && (
                <a
                  href={step.map_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-xs font-medium text-green-700 hover:text-green-800 underline"
                >
                  <span>🗺️</span>
                  Ver no Google Maps
                </a>
              )}
              {step.phone && (
                <p className="text-xs text-green-700 mt-2">
                  <span className="font-medium">Telefone:</span> {step.phone}
                </p>
              )}
              {step.opening_hours && (
                <p className="text-xs text-green-700 mt-1">
                  <span className="font-medium">Horário:</span> {step.opening_hours}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
