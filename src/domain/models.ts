export type ViewState = 'landing' | 'onboarding' | 'dashboard' | 'escalation';

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

export interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  status: 'todo' | 'doing' | 'done';
  detailedSteps?: ChecklistStep[];
  relatedDocId?: string;
}

export interface Document {
  id: string;
  type: string;
  name: string;
  status: DocStatus;
  aiNotes?: string;
}

export interface UserProfile {
  name: string;
  producerType: string;
  city: string;
  answers: Record<string, string>;
  riskFlags: string[];
  caseType: 'in_natura' | 'needs_human';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  audioPlaying?: boolean;
}

export interface OnboardingQuestion {
  key: string;
  text: string;
  type: 'text' | 'choice';
  placeholder?: string;
  options?: string[];
}
