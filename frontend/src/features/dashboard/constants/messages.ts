/**
 * Error and UI messages for the dashboard feature.
 * 
 * Currently in Portuguese. This structure enables future i18n support.
 */

export const ERROR_MESSAGES = {
  FILE_TOO_LARGE: 'Arquivo muito grande. Tamanho máximo: 10MB',
  INVALID_FILE_TYPE: 'Tipo de arquivo não permitido. Use PDF, JPG ou PNG',
  UPLOAD_ERROR: 'Erro ao fazer upload. Tente novamente.',
  GUIDE_GENERATION_ERROR: 'Erro ao gerar guia. Tente novamente.',
  NO_GUIDE_AVAILABLE: 'Este item não possui um guia de formalização disponível.',
} as const;

export const UI_MESSAGES = {
  BACK_TO_CHECKLIST: 'Voltar ao Checklist',
  IMPORTANT: 'Importante',
  GENERATE_GUIDE: 'Gerar Guia',
  GENERATING: 'Gerando...',
  REGENERATE: 'Regenerar',
  UPLOAD_NOW: 'Fazer Upload Agora',
  UPLOAD_COMPLETE: 'Upload Concluído',
  UPLOADING: 'Enviando...',
  TASK_COMPLETE: 'Tarefa Concluída',
  MARK_AS_COMPLETE: 'Marcar como Concluído',
  STEP_BY_STEP: 'Passo a Passo',
  HIDE_GUIDE: 'Ocultar guia',
  USEFUL_TIP: 'Dica útil',
  REQUIRED_DOCUMENT: 'Documento Necessário',
  SEND_DOCUMENT: 'Enviar Documento',
  PENDING: 'Pendente',
  SENT: 'Enviado',
} as const;
