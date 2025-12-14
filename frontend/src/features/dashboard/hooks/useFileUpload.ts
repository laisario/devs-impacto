import { useState, useRef } from 'react';
import { uploadDocument } from '../../../services/api/documents';
import { ApiClientError } from '../../../services/api/client';
import type { DocumentType, DocumentResponse } from '../../../services/api/types';
import type { Document } from '../../../domain/models';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
const UPLOAD_PROGRESS_RESET_DELAY_MS = 2000; // Delay before hiding progress bar after upload completes

const validateFile = (file: File): string | null => {
  if (file.size > MAX_FILE_SIZE) {
    return ERROR_MESSAGES.FILE_TOO_LARGE;
  }
  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return ERROR_MESSAGES.INVALID_FILE_TYPE;
  }
  return null;
};

const isValidDocumentType = (type: string): type is DocumentType => {
  return ['dap_caf', 'cpf', 'cnpj', 'proof_address', 'bank_statement', 'statute', 'minutes', 'other'].includes(type);
};

const determineDocumentType = (relatedDoc?: Document, needUpload?: boolean): DocumentType => {
  if (relatedDoc?.type && isValidDocumentType(relatedDoc.type)) {
    return relatedDoc.type;
  }
  return 'other';
};

interface UseFileUploadOptions {
  relatedDoc?: Document;
  needUpload?: boolean;
  onSuccess?: (doc: DocumentResponse) => void;
  onUploadDoc?: (docId: string) => void;
}

export function useFileUpload({
  relatedDoc,
  needUpload,
  onSuccess,
  onUploadDoc,
}: UseFileUploadOptions = {}) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file before processing
    const validationError = validateFile(file);
    if (validationError) {
      setUploadError(validationError);
      return;
    }

    setIsUploading(true);
    setUploadError('');
    setUploadProgress(0);

    try {
      const docType = determineDocumentType(relatedDoc, needUpload);
      const doc = await uploadDocument(file, docType);
      
      setUploadProgress(100);
      onSuccess?.(doc);
      
      // Update document status if there's a related doc
      if (relatedDoc) {
        onUploadDoc?.(relatedDoc.id);
      }
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setUploadError(err.message || ERROR_MESSAGES.UPLOAD_ERROR);
      } else {
        setUploadError(ERROR_MESSAGES.UPLOAD_ERROR);
      }
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), UPLOAD_PROGRESS_RESET_DELAY_MS);
    }
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return {
    isUploading,
    uploadError,
    uploadProgress,
    fileInputRef,
    handleFileSelect,
    handleUploadClick,
  };
}
