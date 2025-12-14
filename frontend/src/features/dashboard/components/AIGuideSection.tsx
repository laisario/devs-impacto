import type { FormalizationGuideResponse } from '../../../services/api/types';
import { GuidePrompt } from './GuidePrompt';
import { GuideDisplay } from './GuideDisplay';
import { ERROR_MESSAGES } from '../constants/messages';

interface AIGuideSectionProps {
  requirementId?: string;
  guide: FormalizationGuideResponse | null;
  isLoading: boolean;
  error: string;
  onGenerate: () => void;
}

export function AIGuideSection({
  requirementId,
  guide,
  isLoading,
  error,
  onGenerate,
}: AIGuideSectionProps) {
  if (!requirementId) return null;

  return (
    <div className="mb-6">
      {!guide ? (
        <GuidePrompt onGenerate={onGenerate} isLoading={isLoading} />
      ) : (
        <GuideDisplay guide={guide} onRegenerate={onGenerate} isLoading={isLoading} />
      )}
      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
          {error || ERROR_MESSAGES.GUIDE_GENERATION_ERROR}
        </div>
      )}
    </div>
  );
}
