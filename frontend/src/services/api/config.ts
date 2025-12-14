/**
 * API configuration
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://devs-impacto.onrender.com';

export const API_ENDPOINTS = {
  auth: {
    login: '/auth/login',
    me: '/auth/me',
  },
  producer: {
    profile: '/producer-profile',
  },
  documents: {
    presign: '/documents/presign',
    list: '/documents',
    create: '/documents',
    get: (id: string) => `/documents/${id}`,
  },
  onboarding: {
    answer: '/onboarding/answer',
    status: '/onboarding/status',
    summary: '/onboarding/summary',
    preference: '/onboarding/preference',
    updateProfileField: '/onboarding/update-profile-field',
  },
  formalization: {
    status: '/formalization/status',
    tasks: '/formalization/tasks',
    regenerateTasks: '/formalization/tasks/regenerate',
    updateTaskStatus: (taskCode: string) => `/formalization/tasks/${taskCode}`,
    // Legacy endpoint (kept for backward compatibility)
    updateTaskCompletion: (taskId: string) => `/formalization/tasks/${taskId}/complete`,
  },
  ai: {
    guide: '/ai/formalization/guide',
    chat: '/ai/chat/message',
    chatV2: '/ai/chat/message/v2',
    transcribeAudio: '/ai/chat/audio/transcribe',
    synthesizeSpeech: '/ai/chat/audio/speak',
  },
  salesProject: {
    draft: '/sales-project/draft',
    list: '/sales-project',
    get: (id: string) => `/sales-project/${id}`,
  },
} as const;
