/**
 * Authentication API service
 */

import { apiRequest, setAuthToken, removeAuthToken } from './client';
import { API_ENDPOINTS } from './config';
import type {
  LoginRequest,
  TokenResponse,
  UserResponse,
} from './types';

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await apiRequest<TokenResponse>(API_ENDPOINTS.auth.login, {
    method: 'POST',
    body: JSON.stringify(data),
  });

  // Store token after successful login
  if (response.access_token) {
    setAuthToken(response.access_token);
  }

  return response;
}

export async function getCurrentUser(): Promise<UserResponse> {
  return apiRequest<UserResponse>(API_ENDPOINTS.auth.me);
}

export function logout(): void {
  removeAuthToken();
}
