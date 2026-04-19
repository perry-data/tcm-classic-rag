export type AnswerMode = "strong" | "weak_with_review_notice" | "refuse";

export interface EvidenceItem {
  record_id: string;
  record_type: string;
  display_role: "primary" | "secondary" | "review" | string;
  title: string;
  evidence_level: string;
  chapter_id: string | null;
  chapter_title: string | null;
  snippet: string;
  risk_flags: string[];
}

export interface IndexedEvidenceItem extends EvidenceItem {
  eId: string;
}

export interface CitationItem {
  citation_id: string;
  record_id: string;
  record_type: string;
  title: string;
  evidence_level: string;
  snippet: string;
  chapter_id: string | null;
  chapter_title: string | null;
  citation_role: "primary" | "secondary" | "review" | string;
}

export interface DisplaySection {
  section_id: string;
  title: string;
  section_type: string;
  visible: boolean;
  field: string;
}

export interface CommentarialItem {
  unit_id: string;
  commentator: string;
  source_id: string;
  work_title: string | null;
  title: string;
  summary_text: string;
  quoted_original_text: string;
  display_text: string;
  anchor_type: string;
  anchor_priority_mode: string;
  theme_display_tier: string | null;
  primary_anchor_candidates: string[];
  supporting_anchor_candidates: string[];
  resolved_primary_anchor_passage_ids: string[];
  resolved_supporting_anchor_passage_ids: string[];
  unresolved_anchor_keys: string[];
  never_use_in_primary: boolean;
  use_for_confidence_gate: boolean;
  needs_manual_anchor_review: boolean;
  needs_manual_content_review: boolean;
  low_confidence_commentarial_unit: boolean;
  score: number;
}

export interface CommentarialSection {
  section_id: string;
  title: string;
  commentator?: string;
  view_mode: string;
  layout: string;
  collapsed_by_default: boolean;
  items: CommentarialItem[];
}

export interface CommentarialPayload {
  route: string;
  source_aware: boolean;
  lead_note: string;
  sections: CommentarialSection[];
}

export interface AnswerPayload {
  query: string;
  answer_mode: AnswerMode;
  answer_text: string;
  primary_evidence: EvidenceItem[];
  secondary_evidence: EvidenceItem[];
  review_materials: EvidenceItem[];
  disclaimer: string | null;
  review_notice: string | null;
  refuse_reason: string | null;
  suggested_followup_questions: string[];
  citations: CitationItem[];
  commentarial?: CommentarialPayload | null;
  display_sections: DisplaySection[];
}

export interface ConversationSummary {
  id: string;
  title: string;
  title_source: string;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
  message_count: number;
  preview_text: string;
}

export interface ConversationMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  position: number;
  answer_payload: AnswerPayload | null;
}

export interface ConversationDetail {
  conversation: ConversationSummary;
  messages: ConversationMessage[];
}

export interface ConversationListResponse {
  items: ConversationSummary[];
  search: string;
}

export interface ConversationCreateResponse {
  conversation: ConversationSummary;
}

export interface ConversationMessageResponse {
  conversation: ConversationSummary;
  messages: ConversationMessage[];
}

export interface ConversationClearResponse {
  deleted: boolean;
  deleted_count: number;
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
  };
}

export interface PendingTurn {
  role: "user";
  content: string;
  created_at: string;
}
