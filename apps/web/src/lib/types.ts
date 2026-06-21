export type InterviewPhase =
  | "phase_1_intro"
  | "phase_2_deep_dive"
  | "phase_3_breadth"
  | "phase_4_factual"
  | "phase_5_behavioral"
  | "complete";

export interface ParsedResume {
  candidate_name: string;
  headline: string;
  summary: string;
  skills: string[];
  projects: string[];
  experience: string[];
  education: string[];
  inferred_domains: string[];
  notes: string[];
}

export interface InterviewMessage {
  id: string;
  role: "interviewer" | "candidate";
  phase: InterviewPhase;
  text: string;
  hint_used: boolean;
  hint_recovery: boolean;
  empathy_used: boolean;
  created_at: string;
}

export interface PhaseScores {
  phase_2: number | null;
  phase_3: number | null;
  phase_4: number | null;
  phase_5: number | null;
  overall: number | null;
}

export interface PhaseEvaluation {
  phase: InterviewPhase;
  label: string;
  score: number | null;
  dimensions: Record<string, number>;
  evidence: string[];
  strengths: string[];
  weaknesses: string[];
  suggestion: string;
  confidence: number | null;
}

export interface FinalFeedback {
  overall_score: number | null;
  overall_summary: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  role_alignment: string[];
  integrity_notes: string[];
}

export interface ProctoringSummary {
  tab_switch_count: number;
  window_blur_count: number;
  paste_count: number;
  transcript_retry_count: number;
  suspicious_flags: string[];
}

export interface InterviewSession {
  id: string;
  current_phase: InterviewPhase;
  target_company: string;
  target_role: string;
  resume: ParsedResume;
  candidate_id?: string | null;
  resume_id?: string | null;
  messages: InterviewMessage[];
  scores: PhaseScores;
  phase_evaluations: Record<string, PhaseEvaluation>;
  final_feedback?: FinalFeedback | null;
  hint_count: number;
  hint_recovery_count: number;
  empathy_prompt_count: number;
  factual_question_count: number;
  realtime_mode_enabled: boolean;
  video_mode_enabled: boolean;
  proctoring: ProctoringSummary;
}

export interface BootstrapResponse {
  resume: ParsedResume;
  session: InterviewSession;
}

export interface ParsedResumeHistoryEntry {
  id: string;
  fingerprint: string;
  label: string;
  parsed_at: string;
  candidate_id?: string | null;
  resume_id?: string | null;
  resume: ParsedResume;
}

export interface InterviewTurnResponse {
  session: InterviewSession;
  latest_reply: InterviewMessage;
}

export interface TranscriptResponse {
  transcript: string;
}

export interface TurnMetadata {
  source: "text" | "audio" | "realtime";
  answer_duration_seconds?: number | null;
  transcript_retry_count: number;
  tab_switch_count: number;
  window_blur_count: number;
  used_paste: boolean;
  camera_enabled: boolean;
  realtime_enabled: boolean;
}
