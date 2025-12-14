/**
 * TypeScript types matching backend schemas
 */

export type OnboardingStatus = 'not_started' | 'in_progress' | 'completed';

export type EligibilityLevel = 'eligible' | 'partially_eligible' | 'not_eligible';

export type TaskPriority = 'high' | 'medium' | 'low';

export type TaskCategory = 'document' | 'registration' | 'preparation';

export type DocumentType =
  | 'dap_caf'
  | 'cpf'
  | 'cnpj'
  | 'proof_address'
  | 'bank_statement'
  | 'statute'
  | 'minutes'
  | 'other';

export type ProducerType = 'formal' | 'informal' | 'individual';

export type QuestionType = 'boolean' | 'choice' | 'text';

export type ConfidenceLevel = 'high' | 'medium' | 'low';

// Auth types
export interface LoginRequest {
  cpf: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  cpf: string;
  created_at: string;
  updated_at: string;
}

// Producer types
export interface Member {
  name: string;
  cpf: string;
  dap_caf_number?: string;
}

export interface ProducerProfileCreate {
  producer_type: ProducerType;
  name: string;
  address: string;
  city: string;
  state: string;
  dap_caf_number: string;
  cnpj?: string;
  cpf?: string;
  members?: Member[];
  bank_name?: string;
  bank_agency?: string;
  bank_account?: string;
}

export interface ProducerProfileResponse extends ProducerProfileCreate {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  onboarding_status?: OnboardingStatus | null;
  onboarding_completed_at?: string | null;
}

// Document types
export interface PresignRequest {
  filename: string;
  content_type?: string;
}

export interface PresignResponse {
  upload_url: string;
  file_url: string;
  file_key: string;
}

export interface DocumentCreate {
  doc_type: DocumentType;
  file_url: string;
  file_key: string;
  original_filename: string;
}

export interface DocumentResponse {
  id: string;
  user_id: string;
  doc_type: DocumentType;
  file_url: string;
  file_key: string;
  original_filename: string;
  uploaded_at: string;
  ai_notes?: string | null;
  ai_validated?: boolean;
  ai_confidence?: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// Onboarding types
export interface OnboardingAnswerCreate {
  question_id: string;
  answer: boolean | string | number | string[]; // string[] for multi-select
}

export interface OnboardingAnswerResponse {
  id: string;
  user_id: string;
  question_id: string;
  answer: boolean | string | number;
  answered_at: string;
}

export interface OnboardingQuestion {
  question_id: string;
  question_text: string;
  question_type: QuestionType;
  options?: string[] | null;
  order: number;
  required: boolean;
  requirement_id?: string | null;
  allow_multiple?: boolean;
}

export interface OnboardingStatusResponse {
  status: OnboardingStatus;
  progress_percentage: number;
  total_questions: number;
  answered_questions: number;
  next_question?: OnboardingQuestion | null;
  completed_at?: string | null;
}

export interface ProducerOnboardingSummary {
  user_id: string;
  onboarding_status?: OnboardingStatus | null;
  onboarding_completed_at?: string | null;
  onboarding_progress: number;
  formalization_eligible?: boolean | null;
  formalization_score?: number | null;
  has_profile: boolean;
  total_answers: number;
  total_tasks: number;
  completed_tasks: number;
}

// Formalization types
export interface FormalizationStatusResponse {
  is_eligible: boolean;
  eligibility_level: EligibilityLevel;
  score: number;
  requirements_met: string[];
  requirements_missing: string[];
  recommendations: string[];
  diagnosed_at: string;
}

export interface FormalizationTaskResponse {
  id: string;
  user_id: string;
  task_id: string;
  title: string;
  description: string;
  category: TaskCategory;
  priority: TaskPriority;
  completed: boolean;
  completed_at?: string | null;
  created_at: string;
  requirement_id?: string | null;
  need_upload?: boolean;
}

// AI Guide types
export interface GuideGenerationRequest {
  requirement_id: string;
}

export interface GuideStep {
  step: number;
  title: string;
  description: string;
}

export interface FormalizationGuideResponse {
  summary: string;
  steps: GuideStep[];
  estimated_time_days: number;
  where_to_go: string[];
  confidence_level: ConfidenceLevel;
}
