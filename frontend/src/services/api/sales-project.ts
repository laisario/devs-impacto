/**
 * Sales Project API service
 */

import { apiRequest } from './client';
import { API_ENDPOINTS } from './config';

export interface SalesProjectDraftRequest {
  edital_id?: string | null;
  custom_requirements?: Record<string, unknown> | null;
}

export interface ProductItem {
  name: string;
  unit: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  delivery_frequency: string;
}

export interface SalesProjectResponse {
  id: string;
  user_id: string;
  edital_id?: string | null;
  products: ProductItem[];
  delivery_schedule: Record<string, unknown>;
  total_value: number;
  ai_generated: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export async function generateSalesProjectDraft(
  data: SalesProjectDraftRequest
): Promise<SalesProjectResponse> {
  return apiRequest<SalesProjectResponse>(API_ENDPOINTS.salesProject.draft, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function listSalesProjects(): Promise<SalesProjectResponse[]> {
  return apiRequest<SalesProjectResponse[]>(API_ENDPOINTS.salesProject.list, {
    method: 'GET',
  });
}

export async function getSalesProject(id: string): Promise<SalesProjectResponse> {
  return apiRequest<SalesProjectResponse>(API_ENDPOINTS.salesProject.get(id), {
    method: 'GET',
  });
}

