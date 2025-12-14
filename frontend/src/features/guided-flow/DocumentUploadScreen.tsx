import React, { useState, useRef } from 'react';
import { Upload, CheckCircle2, FileText } from 'lucide-react';
import { ScreenWrapper } from '../shared/ScreenWrapper';
import { uploadDocument } from '../../services/api/documents';
import { ApiClientError } from '../../services/api/client';
import type { DocumentType } from '../../services/api/types';

interface DocumentUploadScreenProps {
  taskTitle: string;
  taskNumber: number;
  totalTasks: number;
  docType?: DocumentType;
  onUploadComplete: () => void;
  onBack: () => void;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];

export function DocumentUploadScreen({
  taskTitle,
  taskNumber,
  totalTasks,
  docType = 'other',
  onUploadComplete,
  onBack,
}: DocumentUploadScreenProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      setUploadError('Arquivo muito grande. Tamanho máximo: 10MB');
      return;
    }

    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setUploadError('Tipo de arquivo não permitido. Use PDF ou imagem (JPG, PNG)');
      return;
    }

    setSelectedFile(file);
    setUploadError('');
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError('');

    try {
      await uploadDocument(selectedFile, docType);
      setUploadSuccess(true);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setUploadError(err.message || 'Erro ao enviar documento. Tente novamente.');
      } else {
        setUploadError('Erro ao enviar documento. Tente novamente.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleChooseFile = () => {
    fileInputRef.current?.click();
  };

  if (uploadSuccess) {
    return (
      <ScreenWrapper
        title="Documento enviado!"
        subtitle="Seu documento foi enviado com sucesso"
        primaryAction={{
          label: 'Continuar',
          onClick: onUploadComplete,
        }}
        showBack={false}
        progress={{
          current: taskNumber,
          total: totalTasks,
          label: `Tarefa ${taskNumber} de ${totalTasks}`,
        }}
      >
        <div className="flex justify-center mb-8">
          <div className="bg-green-100 rounded-full p-8">
            <CheckCircle2 className="h-16 w-16 text-green-600" />
          </div>
        </div>
        {selectedFile && (
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center gap-3">
              <FileText className="h-6 w-6 text-green-600" />
              <p className="font-medium text-slate-800">{selectedFile.name}</p>
            </div>
          </div>
        )}
      </ScreenWrapper>
    );
  }

  return (
    <ScreenWrapper
      title="Enviar seu documento"
      subtitle="Escolha o arquivo do seu celular"
      primaryAction={{
        label: selectedFile ? (isUploading ? 'Enviando...' : 'Enviar documento') : 'Escolher arquivo',
        onClick: selectedFile ? handleUpload : handleChooseFile,
        disabled: isUploading || (selectedFile === null && false),
      }}
      showBack
      onBack={onBack}
      progress={{
        current: taskNumber,
        total: totalTasks,
        label: `Tarefa ${taskNumber} de ${totalTasks}`,
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={handleFileSelect}
        className="hidden"
      />

      {uploadError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {uploadError}
        </div>
      )}

      <div className="mb-6 p-8 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 text-center">
        <div className="flex justify-center mb-4">
          <div className="bg-green-100 rounded-full p-6">
            <Upload className="h-12 w-12 text-green-600" />
          </div>
        </div>
        {selectedFile ? (
          <div>
            <p className="font-medium text-slate-800 mb-2">{selectedFile.name}</p>
            <p className="text-sm text-slate-600">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div>
            <p className="text-slate-600 mb-2">Nenhum arquivo escolhido</p>
            <p className="text-sm text-slate-500">
              Clique em "Escolher arquivo" para selecionar
            </p>
          </div>
        )}
      </div>

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
        <p className="text-sm text-blue-800">
          <strong>Dica:</strong> Você pode enviar uma foto ou um arquivo PDF. Tamanho máximo: 10MB
        </p>
      </div>
    </ScreenWrapper>
  );
}
