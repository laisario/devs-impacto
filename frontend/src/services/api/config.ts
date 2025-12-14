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
    updateProfileField: '/onboarding/update-profile-field',
  },
  formalization: {
    status: '/formalization/status',
    tasks: '/formalization/tasks',
  },
  ai: {
    guide: '/ai/formalization/guide',
  },
} as const;
