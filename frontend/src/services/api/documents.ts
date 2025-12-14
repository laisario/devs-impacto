/**
 * Documents API service
 */

import { apiRequest, apiRequestFile, normalizeUploadUrl } from './client';
import { API_ENDPOINTS } from './config';
import type {
  DocumentCreate,
  DocumentResponse,
  DocumentType,
  PaginatedResponse,
  PresignRequest,
  PresignResponse,
} from './types';

export async function presignDocument(data: PresignRequest): Promise<PresignResponse> {
  return apiRequest<PresignResponse>(API_ENDPOINTS.documents.presign, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function uploadFileToPresignedUrl(
  uploadUrl: string,
  file: File
): Promise<void> {
  const normalizedUrl = normalizeUploadUrl(uploadUrl);
  const response = await fetch(normalizedUrl, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type || 'application/octet-stream',
    },
  });
  if (!response.ok) {
    throw new Error(`Upload failed with status ${response.status}`);
  }
}

export async function createDocument(data: DocumentCreate): Promise<DocumentResponse> {
  return apiRequest<DocumentResponse>(API_ENDPOINTS.documents.create, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getDocuments(
  skip = 0,
  limit = 20
): Promise<PaginatedResponse<DocumentResponse>> {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
  });
  return apiRequest<PaginatedResponse<DocumentResponse>>(
    `${API_ENDPOINTS.documents.list}?${params.toString()}`
  );
}

export async function getDocument(id: string): Promise<DocumentResponse> {
  return apiRequest<DocumentResponse>(API_ENDPOINTS.documents.get(id));
}

/**
 * Complete document upload flow: presign → upload → register
 */
export async function uploadDocument(
  file: File,
  docType: DocumentType
): Promise<DocumentResponse> {
  // Step 1: Get presigned URL
  const presignResponse = await presignDocument({
    filename: file.name,
    content_type: file.type || 'application/octet-stream',
  });

  // Step 2: Upload file to presigned URL (normalize to handle internal Docker URLs)
  const normalizedUploadUrl = normalizeUploadUrl(presignResponse.upload_url);
  await fetch(normalizedUploadUrl, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type || 'application/octet-stream',
    },
  });

  // Step 3: Register document metadata
  return createDocument({
    doc_type: docType,
    file_url: presignResponse.file_url,
    file_key: presignResponse.file_key,
    original_filename: file.name,
  });
}
