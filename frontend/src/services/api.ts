import type {
  DocumentItem,
  LinkItem,
  ScanRun,
  AuditLogItem,
  DashboardOverview,
  RecommendationResult,
  CandidateItem,
  ReviewQueueItem,
  RemediationItem,
  RemediationStats,
  ExperimentRunItem,
  ResearchSummary,
  ComparativeBenchmark,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Accept': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.error || errorDetail;
    } catch {
      errorDetail = await response.text() || response.statusText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Statistics / Dashboard
  getDashboardOverview: (): Promise<DashboardOverview> => {
    return fetchJson<DashboardOverview>('/stats/overview');
  },

  // Documents
  getDocuments: (): Promise<DocumentItem[]> => {
    return fetchJson<DocumentItem[]>('/documents');
  },

  getDocumentById: (id: string): Promise<DocumentItem & { links: LinkItem[]; latest_scan?: ScanRun }> => {
    return fetchJson<DocumentItem & { links: LinkItem[]; latest_scan?: ScanRun }>(`/documents/${id}`);
  },

  uploadDocument: async (file: File): Promise<DocumentItem> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }

    return response.json();
  },

  scanDocument: (id: string): Promise<ScanRun> => {
    return fetchJson<ScanRun>(`/documents/${id}/scan`, {
      method: 'POST',
    });
  },

  deleteDocument: async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete document');
    }
  },

  // Links
  getLinks: (params?: {
    document_id?: string;
    status?: string;
    broken_only?: boolean;
    search?: string;
    limit?: number;
  }): Promise<LinkItem[]> => {
    const query = new URLSearchParams();
    if (params?.document_id) query.append('document_id', params.document_id);
    if (params?.status) query.append('status', params.status);
    if (params?.broken_only) query.append('broken_only', 'true');
    if (params?.search) query.append('search', params.search);
    if (params?.limit) query.append('limit', params.limit.toString());

    const qs = query.toString() ? `?${query.toString()}` : '';
    return fetchJson<LinkItem[]>(`/links${qs}`);
  },

  getLinkById: (id: string): Promise<LinkItem> => {
    return fetchJson<LinkItem>(`/links/${id}`);
  },

  revalidateLink: (id: string): Promise<LinkItem> => {
    return fetchJson<LinkItem>(`/links/${id}/validate`, {
      method: 'POST',
    });
  },

  // Audit Logs
  getAuditLogs: (documentId?: string): Promise<AuditLogItem[]> => {
    const qs = documentId ? `?document_id=${documentId}` : '';
    return fetchJson<AuditLogItem[]>(`/audit-logs${qs}`);
  },

  // Prompt 2: Candidate Discovery & Recommendations
  discoverCandidatesForLink: (linkId: string, autoRemediate: boolean = false): Promise<RecommendationResult> => {
    return fetchJson<RecommendationResult>(`/links/${linkId}/discover-candidates?auto_remediate=${autoRemediate}`, {
      method: 'POST',
    });
  },

  getCandidatesForLink: (linkId: string): Promise<CandidateItem[]> => {
    return fetchJson<CandidateItem[]>(`/links/${linkId}/candidates`);
  },

  recommendReplacement: (linkId: string, autoRemediate: boolean = true): Promise<RecommendationResult> => {
    return fetchJson<RecommendationResult>(`/links/${linkId}/recommend?auto_remediate=${autoRemediate}`, {
      method: 'POST',
    });
  },

  repairLink: (
    linkId: string,
    req?: { candidate_url?: string; dry_run?: boolean; reviewer?: string }
  ): Promise<any> => {
    return fetchJson<any>(`/links/${linkId}/repair`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req || {}),
    });
  },

  // Prompt 2: Human Review Queue
  getReviewQueue: (status?: string): Promise<ReviewQueueItem[]> => {
    const qs = status ? `?status=${status}` : '';
    return fetchJson<ReviewQueueItem[]>(`/reviews${qs}`);
  },

  getReviewStats: (): Promise<{ pending: number; approved: number; rejected: number; total: number }> => {
    return fetchJson<{ pending: number; approved: number; rejected: number; total: number }>('/reviews/stats');
  },

  approveReview: (reviewId: string, reviewer: string = 'HUMAN_OPERATOR', comment?: string): Promise<any> => {
    const query = new URLSearchParams({ reviewer });
    if (comment) query.append('comment', comment);
    return fetchJson<any>(`/reviews/${reviewId}/approve?${query.toString()}`, {
      method: 'POST',
    });
  },

  rejectReview: (reviewId: string, reviewer: string = 'HUMAN_OPERATOR', comment?: string): Promise<any> => {
    const query = new URLSearchParams({ reviewer });
    if (comment) query.append('comment', comment);
    return fetchJson<any>(`/reviews/${reviewId}/reject?${query.toString()}`, {
      method: 'POST',
    });
  },

  submitReviewDecision: (
    reviewId: string,
    req: { decision: string; replacement_url?: string; comment?: string; reviewer?: string }
  ): Promise<any> => {
    return fetchJson<any>(`/reviews/${reviewId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
  },

  // Prompt 2: Autonomous Remediations
  getRemediations: (skip: number = 0, limit: number = 100): Promise<RemediationItem[]> => {
    return fetchJson<RemediationItem[]>(`/remediations?skip=${skip}&limit=${limit}`);
  },

  getRemediationStats: (): Promise<RemediationStats> => {
    return fetchJson<RemediationStats>('/remediations/stats');
  },

  // Prompt 2: Research Experiments & Benchmarks
  getExperiments: (): Promise<ExperimentRunItem[]> => {
    return fetchJson<ExperimentRunItem[]>('/experiments');
  },

  runExperiment: (req: {
    experiment_name?: string;
    method: string;
    dataset_version?: string;
    weights?: Record<string, number>;
    disabled_features?: string[];
  }): Promise<ExperimentRunItem> => {
    return fetchJson<ExperimentRunItem>('/experiments/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
  },

  runComparativeBenchmark: (): Promise<ComparativeBenchmark> => {
    return fetchJson<ComparativeBenchmark>('/experiments/compare');
  },

  // Prompt 2: Research Summary & Exports
  getResearchSummary: (): Promise<ResearchSummary> => {
    return fetchJson<ResearchSummary>('/research/summary');
  },

  getExportUrl: (format: 'json' | 'csv' = 'json', datasetType: string = 'all'): string => {
    return `${API_BASE_URL}/research/export?format=${format}&dataset_type=${datasetType}`;
  },
};
