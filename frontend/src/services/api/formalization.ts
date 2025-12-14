/**
 * Formalization API service
 */

import { apiRequest } from './client';
import { API_ENDPOINTS } from './config';
import type { FormalizationStatusResponse, FormalizationTaskResponse } from './types';

export async function getFormalizationStatus(): Promise<FormalizationStatusResponse> {
  return apiRequest<FormalizationStatusResponse>(API_ENDPOINTS.formalization.status);
}

export async function getFormalizationTasks(): Promise<FormalizationTaskResponse[]> {
  return apiRequest<FormalizationTaskResponse[]>(API_ENDPOINTS.formalization.tasks);
}
