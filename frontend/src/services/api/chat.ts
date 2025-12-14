/**
 * AI Chat API service
 */

import { apiRequest } from './client';
import { API_ENDPOINTS } from './config';

export interface ChatMessageCreate {
  message: string;
  conversation_id?: string | null;
}

export interface ChatMessageResponse {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  conversation_id: string;
}

export async function sendChatMessage(
  data: ChatMessageCreate
): Promise<ChatMessageResponse> {
  return apiRequest<ChatMessageResponse>(API_ENDPOINTS.ai.chat, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

