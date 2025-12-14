import type { ConfidenceLevel } from '../../../services/api/types';

export const CONFIDENCE_LABELS: Record<ConfidenceLevel, string> = {
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
};

export const getConfidenceLabel = (level: ConfidenceLevel): string => {
  return CONFIDENCE_LABELS[level];
};

export const getConfidenceBadgeClass = (level: ConfidenceLevel): string => {
  switch (level) {
    case 'high':
      return 'bg-green-100 text-green-700';
    case 'medium':
      return 'bg-yellow-100 text-yellow-700';
    case 'low':
      return 'bg-orange-100 text-orange-700';
  }
};
