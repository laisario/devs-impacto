/**
 * Tests for auth API service
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { login, getCurrentUser, logout } from '../auth';
import { setAuthToken, removeAuthToken, getAuthToken } from '../client';
import * as client from '../client';

// Mock the API client
vi.mock('../../api/client', async () => {
  const actual = await vi.importActual('../../api/client');
  return {
    ...actual,
    apiRequest: vi.fn(),
  };
});

describe('Auth API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    removeAuthToken();
  });

  afterEach(() => {
    removeAuthToken();
  });

  describe('login', () => {
    it('should call API and store token', async () => {
      const mockResponse = {
        access_token: 'test-token-123',
        token_type: 'bearer',
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockResponse);

      const result = await login({
        cpf: '12345678900',
      });

      expect(client.apiRequest).toHaveBeenCalledWith(
        '/auth/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            cpf: '12345678900',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
      expect(getAuthToken()).toBe('test-token-123');
    });
  });

  describe('getCurrentUser', () => {
    it('should fetch current user with auth token', async () => {
      setAuthToken('test-token');
      const mockUser = {
        id: 'user123',
        cpf: '12345678900',
        created_at: '2025-01-15T10:30:00Z',
        updated_at: '2025-01-15T10:30:00Z',
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockUser);

      const result = await getCurrentUser();

      expect(client.apiRequest).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockUser);
    });
  });

  describe('logout', () => {
    it('should remove auth token', () => {
      setAuthToken('test-token');
      expect(getAuthToken()).toBe('test-token');

      logout();

      expect(getAuthToken()).toBeNull();
    });
  });
});
