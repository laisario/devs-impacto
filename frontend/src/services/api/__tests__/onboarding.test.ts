/**
 * Tests for onboarding API service
 */

// @ts-expect-error - vitest types may not be available
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  submitOnboardingAnswer,
  getOnboardingStatus,
  getOnboardingSummary,
} from '../onboarding';
import * as client from '../client';

// Mock the API client
vi.mock('../../api/client', async () => {
  const actual = await vi.importActual('../../api/client');
  return {
    ...actual,
    apiRequest: vi.fn(),
  };
});

describe('Onboarding API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('submitOnboardingAnswer', () => {
    it('should submit answer with correct payload', async () => {
      const mockResponse = {
        id: 'answer123',
        user_id: 'user123',
        question_id: 'has_dap_caf',
        answer: true,
        answered_at: '2025-01-15T10:30:00Z',
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockResponse);

      const result = await submitOnboardingAnswer({
        question_id: 'has_dap_caf',
        answer: true,
      });

      expect(client.apiRequest).toHaveBeenCalledWith(
        '/onboarding/answer',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            question_id: 'has_dap_caf',
            answer: true,
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle string answers', async () => {
      const mockResponse = {
        id: 'answer123',
        user_id: 'user123',
        question_id: 'name',
        answer: 'João Silva',
        answered_at: '2025-01-15T10:30:00Z',
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockResponse);

      await submitOnboardingAnswer({
        question_id: 'name',
        answer: 'João Silva',
      });

      expect(client.apiRequest).toHaveBeenCalledWith(
        '/onboarding/answer',
        expect.objectContaining({
          body: JSON.stringify({
            question_id: 'name',
            answer: 'João Silva',
          }),
        })
      );
    });
  });

  describe('getOnboardingStatus', () => {
    it('should fetch onboarding status', async () => {
      const mockStatus = {
        status: 'in_progress',
        progress_percentage: 45.5,
        total_questions: 20,
        answered_questions: 9,
        next_question: {
          question_id: 'has_cnpj',
          question_text: 'Você possui CNPJ?',
          question_type: 'boolean',
          options: null,
          order: 10,
          required: true,
          requirement_id: 'cnpj_registration',
        },
        completed_at: null,
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockStatus);

      const result = await getOnboardingStatus();

      expect(client.apiRequest).toHaveBeenCalledWith('/onboarding/status');
      expect(result).toEqual(mockStatus);
    });
  });

  describe('getOnboardingSummary', () => {
    it('should fetch onboarding summary', async () => {
      const mockSummary = {
        user_id: 'user123',
        onboarding_status: 'in_progress',
        onboarding_completed_at: null,
        onboarding_progress: 45.5,
        formalization_eligible: false,
        formalization_score: 35,
        has_profile: true,
        total_answers: 9,
        total_tasks: 5,
        completed_tasks: 2,
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockSummary);

      const result = await getOnboardingSummary();

      expect(client.apiRequest).toHaveBeenCalledWith('/onboarding/summary');
      expect(result).toEqual(mockSummary);
    });
  });
});
