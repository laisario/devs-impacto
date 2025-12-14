/**
 * AI Chat API service
 */

import { apiRequest } from './client';
import { API_ENDPOINTS } from './config';

// Legacy types (kept for backward compatibility)
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

// New types for state-driven chatbot
export type ChatState = 'idle' | 'explaining_task' | 'waiting_confirmation' | 'task_completed' | 'error';

export type MessageType = 'info' | 'question' | 'action' | 'error';

export type InputType = 'text' | 'audio';

export type ActionType = 'mark_task_done' | 'go_to_screen' | 'open_guide';

export interface ClientCapabilities {
  can_play_audio: boolean;
  prefers_audio: boolean;
}

export interface SuggestedAction {
  type: ActionType;
  task_code?: string | null;
  screen?: string | null;
  requirement_id?: string | null;
}

export interface ConversationState {
  current_goal: string | null;
  current_task_code: string | null;
  chat_state: ChatState;
}

export interface ChatMessageRequest {
  conversation_id?: string | null;
  input_type: InputType;
  text?: string | null;
  audio_url?: string | null;
  locale?: string;
  client_capabilities?: ClientCapabilities;
}

export interface ChatMessageResponseNew {
  conversation_id: string;
  message_id: string;
  message_type: MessageType;
  text: string;
  audio_url?: string | null;
  suggested_actions: SuggestedAction[];
  conversation_state: ConversationState;
}

// Legacy function (kept for backward compatibility)
export async function sendChatMessage(
  data: ChatMessageCreate
): Promise<ChatMessageResponse> {
  return apiRequest<ChatMessageResponse>(API_ENDPOINTS.ai.chat, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// New function for state-driven chatbot
export async function sendChatMessageV2(
  data: ChatMessageRequest
): Promise<ChatMessageResponseNew> {
  return apiRequest<ChatMessageResponseNew>(API_ENDPOINTS.ai.chatV2, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Audio transcription
export async function transcribeAudio(audioUrl: string): Promise<{ text: string }> {
  return apiRequest<{ text: string }>(API_ENDPOINTS.ai.transcribeAudio, {
    method: 'POST',
    body: JSON.stringify({ audio_url: audioUrl }),
  });
}

// Text to speech
export async function synthesizeSpeech(
  text: string,
  locale: string = 'pt-BR'
): Promise<{ audio_url: string | null }> {
  return apiRequest<{ audio_url: string | null }>(API_ENDPOINTS.ai.synthesizeSpeech, {
    method: 'POST',
    body: JSON.stringify({ text, locale }),
  });
}

