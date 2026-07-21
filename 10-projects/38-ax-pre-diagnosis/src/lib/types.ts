export type QuestionType = 'select' | 'free' | 'select_with_detail';

export interface QuestionOption {
  value: string;
  label: string;
}

export interface Question {
  id: string;
  title: string;
  description?: string;
  type: QuestionType;
  options?: QuestionOption[];
  detailPrompt?: string;       // select_with_detail일 때 추가 입력 안내
  detailRequired?: boolean;
  referenceExamples?: string[]; // 자유입력 시 참고 예시
  maxSelect?: number;           // 복수 선택 시
}

export interface Answer {
  questionId: string;
  rawAnswer: string;
  selectedOptions: string[];
  isFollowUp: boolean;
}

export interface InterviewSession {
  id: string;
  educationId: string;
  token: string;
  participantName: string | null;
  status: 'started' | 'in_progress' | 'completed';
  currentQuestion: number;
  consentGiven: boolean;
}

export interface AnalysisResult {
  ai_familiarity_level: number;
  participation_reason: string;
  primary_expectation: string;
  secondary_expectations: string[];
  target_task: string;
  pain_point: string;
  desired_ai_role: string;
  expected_completion_level: number;
  success_criteria: string[];
  first_action: string;
  expectation_clarity_score: number;
  recommended_difficulty: string;
  recommended_topics: string[];
  recommended_practice: string;
  needs_expectation_adjustment: boolean;
  participant_summary?: string;
}

export interface ChatMessage {
  role: 'assistant' | 'user';
  content: string;
  options?: QuestionOption[];
  type?: 'welcome' | 'question' | 'summary' | 'followup';
  questionId?: string;
  referenceExamples?: string[];
  detailPrompt?: string;
  maxSelect?: number;
}
