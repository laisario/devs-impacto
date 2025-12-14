/**
 * Tests for documents API service
 */

// @ts-expect-error - vitest types may not be available
import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  presignDocument,
  createDocument,
  getDocuments,
  getDocument,
  uploadDocument,
} from '../documents';
import * as client from '../client';

// Mock the API client
vi.mock('../../api/client', async () => {
  const actual = await vi.importActual('../../api/client');
  return {
    ...actual,
    apiRequest: vi.fn(),
    apiRequestFile: vi.fn(),
  };
});

// Mock fetch for upload
(globalThis as any).fetch = vi.fn();

describe('Documents API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('presignDocument', () => {
    it('should request presigned URL', async () => {
      const mockResponse = {
        upload_url: 'https://storage.example.com/upload?signature=...',
        file_url: 'https://storage.example.com/files/user123/test.pdf',
        file_key: 'user123/test_20250115.pdf',
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockResponse);

      const result = await presignDocument({
        filename: 'test.pdf',
        content_type: 'application/pdf',
      });

      expect(client.apiRequest).toHaveBeenCalledWith(
        '/documents/presign',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            filename: 'test.pdf',
            content_type: 'application/pdf',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('createDocument', () => {
    it('should create document metadata', async () => {
      const mockResponse = {
        id: 'doc123',
        user_id: 'user123',
        doc_type: 'dap_caf',
        file_url: 'https://storage.example.com/files/test.pdf',
        file_key: 'user123/test.pdf',
        original_filename: 'test.pdf',
        uploaded_at: '2025-01-15T10:30:00Z',
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockResponse);

      const result = await createDocument({
        doc_type: 'dap_caf',
        file_url: 'https://storage.example.com/files/test.pdf',
        file_key: 'user123/test.pdf',
        original_filename: 'test.pdf',
      });

      expect(client.apiRequest).toHaveBeenCalledWith(
        '/documents',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            doc_type: 'dap_caf',
            file_url: 'https://storage.example.com/files/test.pdf',
            file_key: 'user123/test.pdf',
            original_filename: 'test.pdf',
          }),
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getDocuments', () => {
    it('should fetch documents with pagination', async () => {
      const mockResponse = {
        items: [
          {
            id: 'doc1',
            user_id: 'user123',
            doc_type: 'dap_caf',
            file_url: 'https://storage.example.com/files/test1.pdf',
            file_key: 'user123/test1.pdf',
            original_filename: 'test1.pdf',
            uploaded_at: '2025-01-15T10:30:00Z',
          },
        ],
        total: 1,
        skip: 0,
        limit: 20,
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockResponse);

      const result = await getDocuments(0, 20);

      expect(client.apiRequest).toHaveBeenCalledWith(
        '/documents?skip=0&limit=20'
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getDocument', () => {
    it('should fetch a specific document by ID', async () => {
      const mockResponse = {
        id: 'doc123',
        user_id: 'user123',
        doc_type: 'dap_caf',
        file_url: 'https://storage.example.com/files/test.pdf',
        file_key: 'user123/test.pdf',
        original_filename: 'test.pdf',
        uploaded_at: '2025-01-15T10:30:00Z',
      };
      vi.mocked(client.apiRequest).mockResolvedValue(mockResponse);

      const result = await getDocument('doc123');

      expect(client.apiRequest).toHaveBeenCalledWith('/documents/doc123');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('uploadDocument', () => {
    it('should complete full upload flow', async () => {
      const mockPresignResponse = {
        upload_url: 'https://storage.example.com/upload?signature=...',
        file_url: 'https://storage.example.com/files/test.pdf',
        file_key: 'user123/test.pdf',
      };
      const mockCreateResponse = {
        id: 'doc123',
        user_id: 'user123',
        doc_type: 'dap_caf',
        file_url: 'https://storage.example.com/files/test.pdf',
        file_key: 'user123/test.pdf',
        original_filename: 'test.pdf',
        uploaded_at: '2025-01-15T10:30:00Z',
      };

      vi.mocked(client.apiRequest)
        .mockResolvedValueOnce(mockPresignResponse)
        .mockResolvedValueOnce(mockCreateResponse);
      vi.mocked((globalThis as any).fetch).mockResolvedValue({
        ok: true,
        status: 200,
      } as Response);

      const file = new File(['test content'], 'test.pdf', {
        type: 'application/pdf',
      });

      const result = await uploadDocument(file, 'dap_caf');

      expect(client.apiRequest).toHaveBeenCalledTimes(2);
      expect((globalThis as any).fetch).toHaveBeenCalledWith(
        mockPresignResponse.upload_url,
        expect.objectContaining({
          method: 'PUT',
          body: file,
        })
      );
      expect(result).toEqual(mockCreateResponse);
    });
  });
});
