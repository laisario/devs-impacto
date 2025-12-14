/**
 * AI Formalization Guide API service
 */

import { apiRequest } from './client';
import { API_ENDPOINTS } from './config';
import type {
  FormalizationGuideResponse,
  GuideGenerationRequest,
} from './types';

export async function generateFormalizationGuide(
  data: GuideGenerationRequest
): Promise<FormalizationGuideResponse> {
  return apiRequest<FormalizationGuideResponse>(API_ENDPOINTS.ai.guide, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
