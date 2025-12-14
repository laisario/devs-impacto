/**
 * Core HTTP client with authentication headers
 */

import { API_BASE_URL } from './config';

export interface ApiError {
  message: string;
  status: number;
  detail?: string | Record<string, unknown>;
}

export class ApiClientError extends Error {
  status: number;
  detail?: string | Record<string, unknown>;

  constructor(message: string, status: number, detail?: string | Record<string, unknown>) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Get stored auth token
 */
export function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

/**
 * Store auth token
 */
export function setAuthToken(token: string): void {
  localStorage.setItem('auth_token', token);
}

/**
 * Remove auth token
 */
export function removeAuthToken(): void {
  localStorage.removeItem('auth_token');
}

/**
 * Make authenticated API request
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle empty responses (204 No Content)
  if (response.status === 204) {
    return null as T;
  }

  let data: unknown;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = text ? { message: text } : null;
  }

  if (!response.ok) {
    const errorData = data as { detail?: string | Record<string, unknown>; message?: string };
    const message =
      errorData?.message ||
      errorData?.detail ||
      `Request failed with status ${response.status}`;
    throw new ApiClientError(
      typeof message === 'string' ? message : JSON.stringify(message),
      response.status,
      errorData?.detail
    );
  }

  return data as T;
}

/**
 * Make API request with file upload
 */
export async function apiRequestFile<T>(
  endpoint: string,
  file: File,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiClientError(
      errorText || `Upload failed with status ${response.status}`,
      response.status
    );
  }

  // Some presigned URLs might return empty responses
  if (response.status === 200 || response.status === 204) {
    try {
      const data = await response.json();
      return data as T;
    } catch {
      return null as T;
    }
  }

  return null as T;
}
