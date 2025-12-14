/**
 * Onboarding API service
 */

import { apiRequest } from './client';
import { API_ENDPOINTS } from './config';
import type {
  OnboardingAnswerCreate,
  OnboardingAnswerResponse,
  OnboardingStatusResponse,
  ProducerOnboardingSummary,
} from './types';

export async function submitOnboardingAnswer(
  data: OnboardingAnswerCreate
): Promise<OnboardingAnswerResponse> {
  return apiRequest<OnboardingAnswerResponse>(API_ENDPOINTS.onboarding.answer, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getOnboardingStatus(): Promise<OnboardingStatusResponse> {
  return apiRequest<OnboardingStatusResponse>(API_ENDPOINTS.onboarding.status);
}

export async function getOnboardingSummary(): Promise<ProducerOnboardingSummary> {
  return apiRequest<ProducerOnboardingSummary>(API_ENDPOINTS.onboarding.summary);
}

export async function updateProfileField(
  field: string,
  value: string
): Promise<{ message: string }> {
  const params = new URLSearchParams({
    field,
    value,
  });
  return apiRequest<{ message: string }>(
    `${API_ENDPOINTS.onboarding.updateProfileField}?${params.toString()}`,
    {
      method: 'POST',
    }
  );
}
