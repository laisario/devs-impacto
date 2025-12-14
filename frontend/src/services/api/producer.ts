/**
 * Producer profile API service
 */

import { apiRequest, ApiClientError } from './client';
import { API_ENDPOINTS } from './config';
import type { ProducerProfileCreate, ProducerProfileResponse } from './types';

export async function getProducerProfile(): Promise<ProducerProfileResponse | null> {
  try {
    return await apiRequest<ProducerProfileResponse>(API_ENDPOINTS.producer.profile);
  } catch (error) {
    // Return null if profile doesn't exist (404), otherwise rethrow
    if (error instanceof ApiClientError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function createOrUpdateProducerProfile(
  data: ProducerProfileCreate
): Promise<ProducerProfileResponse> {
  return apiRequest<ProducerProfileResponse>(API_ENDPOINTS.producer.profile, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}
