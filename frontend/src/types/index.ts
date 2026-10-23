export interface DocumentItem {
  document_id: string;
  filename: string;
  file_type: 'pdf' | 'docx' | string;
  file_size: number;
  upload_timestamp: string;
  version: number;
  processing_status: 'PENDING' | 'PARSED' | 'SCANNING' | 'COMPLETED' | 'FAILED';
  document_title?: string;
  storage_path: string;
  links_count: number;
  valid_links_count: number;
  broken_links_count: number;
  last_scanned_at?: string;
}

export interface LinkItem {
  link_id: string;
  document_id: string;
  original_url: string;
  normalized_url: string;
  status:
    | 'VALID'
    | 'BROKEN_404'
    | 'BROKEN_4XX'
    | 'SERVER_ERROR_5XX'
    | 'TIMEOUT'
    | 'DNS_ERROR'
    | 'CONNECTION_ERROR'
    | 'REDIRECT'
    | 'FORBIDDEN'
    | 'UNAUTHORIZED'
    | 'INVALID_URL'
    | 'PENDING'
    | 'UNKNOWN';
  status_code?: number;
  final_url?: string;
  response_time_ms?: number;
  content_type?: string;
  last_checked?: string;
  error_message?: string;
  page_number?: number;
  location_description?: string;
  document_title?: string;
  document_filename?: string;
  context?: LinkContext;
}

export interface LinkContext {
  context_id: string;
  link_id: string;
  anchor_text?: string;
  surrounding_text?: string;
  paragraph_text?: string;
  section_heading?: string;
  document_title?: string;
  url_tokens?: {
    domain?: string;
    path?: string;
    filename?: string;
    path_segments?: string[];
    query_keys?: string[];
    terms?: string[];
  };
  keywords?: string[];
}

export interface ScanRun {
  scan_id: string;
  document_id: string;
  started_at: string;
  completed_at?: string;
  total_links: number;
  valid_links: number;
  broken_links: number;
  redirected_links: number;
  failed_links: number;
  scan_status: string;
}

export interface AuditLogItem {
  audit_id: string;
  timestamp: string;
  document_id?: string;
  link_id?: string;
  action_type: string;
  old_url?: string;
  new_url?: string;
  status?: string;
  reason?: string;
  confidence_score?: number;
  actor: string;
}

export interface DistributionItem {
  name: string;
  value: number;
  percentage: number;
  color?: string;
}

export interface DashboardOverview {
  total_documents: number;
  scanned_documents: number;
  total_links: number;
  valid_links: number;
  broken_links: number;
  redirected_links: number;
  failed_links: number;
  pending_links: number;
  status_distribution: DistributionItem[];
  failure_distribution: DistributionItem[];
  recent_activity: any[];
}

export interface CandidateScore {
  score_id: string;
  candidate_id: string;
  semantic_similarity: number;
  title_similarity: number;
  url_similarity: number;
  keyword_overlap: number;
  domain_score: number;
  content_quality_score: number;
  overall_score: number;
  rank: number;
  explanation: string;
}

export interface CandidateItem {
  candidate_id: string;
  link_id: string;
  candidate_url: string;
  title: string;
  snippet?: string;
  content_text?: string;
  domain: string;
  source: string;
  retrieved_at: string;
  score?: CandidateScore;
}

export interface RecommendationResult {
  link_id: string;
  broken_url: string;
  decision: 'AUTO_REPAIR' | 'HUMAN_REVIEW' | 'NO_REPLACEMENT';
  confidence_score: number;
  decision_reason: string;
  top_candidate?: CandidateItem;
  ranked_candidates: CandidateItem[];
  remediation_result?: any;
}

export interface ReviewQueueItem {
  review_id: string;
  link_id: string;
  candidate_id?: string;
  confidence_score?: number;
  review_status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EDITED';
  reviewer?: string;
  reviewer_comment?: string;
  created_at: string;
  reviewed_at?: string;
  document_id?: string;
  document_title?: string;
  broken_url?: string;
  failure_type?: string;
  anchor_text?: string;
  surrounding_context?: string;
  section_heading?: string;
  candidate?: CandidateItem;
}

export interface RemediationItem {
  remediation_id: string;
  link_id: string;
  old_url: string;
  new_url: string;
  confidence_score?: number;
  action: 'AUTO_REPAIRED' | 'MANUAL_APPROVED' | 'RECOMMENDATION_ONLY';
  validation_result?: 'VERIFIED_WORKING' | 'FAILED' | 'PENDING';
  actor: string;
  status: string;
  created_at: string;
  completed_at?: string;
  document_id?: string;
  document_filename?: string;
}

export interface RemediationStats {
  total_remediations: number;
  auto_repaired: number;
  manual_approved: number;
  verified_working: number;
  failed_remediations: number;
  success_rate: number;
}

export interface ExperimentRunItem {
  experiment_id: string;
  experiment_name: string;
  configuration: Record<string, any>;
  dataset_version: string;
  status: string;
  started_at: string;
  completed_at?: string;
  results?: any;
}

export interface ResearchSummary {
  dataset_statistics: {
    documents: number;
    links: number;
    broken_links: number;
    candidates_evaluated: number;
    remediations_executed: number;
    human_reviews_logged: number;
  };
  scientific_metrics: {
    detection_precision: number;
    detection_recall: number;
    detection_f1: number;
    top1_accuracy: number;
    top3_accuracy: number;
    mrr: number;
    automatic_repair_precision: number;
    automatic_repair_rate: number;
    false_repair_rate: number;
    human_review_rate: number;
  };
  latest_experiment_id?: string;
  latest_experiment_name?: string;
}

export interface ComparativeBenchmark {
  timestamp: string;
  comparison_table: Array<{
    method: string;
    precision: number;
    recall: number;
    f1: number;
    top1: number;
    top3: number;
    mrr: number;
    repair_precision: number;
    repair_rate: number;
  }>;
  runs: Record<string, any>;
}
