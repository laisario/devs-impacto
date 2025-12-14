/**
 * Formalization API service
 */

import { apiRequest } from './client';
import { API_ENDPOINTS } from './config';
import type {
  FormalizationStatusResponse,
  FormalizationTaskResponse,
  FormalizationTaskUserResponse,
  TaskStatus,
} from './types';

export async function getFormalizationStatus(): Promise<FormalizationStatusResponse> {
  return apiRequest<FormalizationStatusResponse>(API_ENDPOINTS.formalization.status);
}

export async function getFormalizationTasks(): Promise<FormalizationTaskUserResponse[]> {
  return apiRequest<FormalizationTaskUserResponse[]>(API_ENDPOINTS.formalization.tasks);
}

export async function regenerateFormalizationTasks(): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(API_ENDPOINTS.formalization.regenerateTasks, {
    method: 'POST',
  });
}

export async function updateTaskStatus(
  taskCode: string,
  status: TaskStatus
): Promise<FormalizationTaskUserResponse> {
  return apiRequest<FormalizationTaskUserResponse>(
    API_ENDPOINTS.formalization.updateTaskStatus(taskCode),
    {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }
  );
}

// Legacy function (kept for backward compatibility)
export async function updateTaskCompletion(
  taskId: string,
  completed: boolean
): Promise<FormalizationTaskResponse> {
  return apiRequest<FormalizationTaskResponse>(
    API_ENDPOINTS.formalization.updateTaskCompletion(taskId),
    {
      method: 'PATCH',
      body: JSON.stringify({ completed }),
    }
  );
}
