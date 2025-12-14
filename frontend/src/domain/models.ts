// Re-export types from API for convenience
export type {
  OnboardingStatus,
  EligibilityLevel,
  TaskPriority,
  TaskCategory,
  DocumentType,
  ProducerType,
  QuestionType,
  ConfidenceLevel,
} from '../services/api/types';

export type ViewState = 'landing' | 'login' | 'register' | 'onboarding' | 'profile' | 'dashboard' | 'escalation';

export type DocStatus = 'missing' | 'uploaded' | 'ai_reviewed' | 'accepted';

export interface ChecklistStepHelp {
  type: 'tip';
  title: string;
  description: string;
}

export interface ChecklistStep {
  text: string;
  helpContent?: ChecklistStepHelp;
}

/**
 * Frontend checklist item - maps from FormalizationTaskResponse
 * status: 'todo' = !completed, 'done' = completed
 */
export interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  priority: TaskPriority;
  status: 'todo' | 'doing' | 'done';
  detailedSteps?: ChecklistStep[];
  relatedDocId?: string;
  taskId?: string; // Backend task_id
  category?: TaskCategory;
  requirementId?: string; // For AI guide generation
  needUpload?: boolean; // If this task requires document upload
}

/**
 * Frontend document - maps from DocumentResponse
 */
export interface Document {
  id: string;
  type: DocumentType;
  name: string; // original_filename
  status: DocStatus;
  aiNotes?: string;
  fileUrl?: string;
  uploadedAt?: string;
}

/**
 * Frontend user profile - combines ProducerProfileResponse with additional UI state
 */
export interface UserProfile {
  id?: string;
  name: string;
  producerType: ProducerType;
  city: string;
  state?: string;
  address?: string;
  answers?: Record<string, string>;
  riskFlags?: string[];
  caseType?: 'in_natura' | 'needs_human';
  eligibilityLevel?: EligibilityLevel;
  formalizationScore?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  audioPlaying?: boolean;
}

/**
 * Frontend onboarding question - maps from OnboardingQuestion
 */
export interface OnboardingQuestion {
  key: string; // question_id
  text: string; // question_text
  type: QuestionType;
  placeholder?: string;
  options?: string[];
  required?: boolean;
  requirementId?: string;
}
