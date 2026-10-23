import React, { useState, useEffect } from 'react';
import {
  CheckCircle,
  XCircle,
  Edit3,
  ExternalLink,
  ShieldAlert,
  HelpCircle,
  UserCheck,
  RefreshCw,
  Sparkles,
  Search,
  Check,
} from 'lucide-react';
import { api } from '../services/api';
import type { ReviewQueueItem } from '../types';

export const ReviewQueuePage: React.FC = () => {
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'PENDING' | 'APPROVED' | 'REJECTED' | 'ALL'>('PENDING');
  const [search, setSearch] = useState('');
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [customUrl, setCustomUrl] = useState('');
  const [reviewerComment, setReviewerComment] = useState('');
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchItems = async () => {
    setLoading(true);
    try {
      const statusParam = filter === 'ALL' ? undefined : filter;
      const data = await api.getReviewQueue(statusParam);
      setItems(data);
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to load review queue' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [filter]);

  const handleApprove = async (reviewId: string) => {
    setActionInProgress(reviewId);
    try {
      await api.approveReview(reviewId, 'HUMAN_OPERATOR', reviewerComment || 'Approved in review triage');
      setNotification({ type: 'success', message: 'Candidate approved and document patched successfully!' });
      setReviewerComment('');
      fetchItems();
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Approval failed' });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async (reviewId: string) => {
    setActionInProgress(reviewId);
    try {
      await api.rejectReview(reviewId, 'HUMAN_OPERATOR', reviewerComment || 'Candidate rejected by operator');
      setNotification({ type: 'success', message: 'Candidate rejected. Recorded negative sample in research feedback dataset.' });
      setReviewerComment('');
      fetchItems();
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Rejection failed' });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleCustomSubmit = async (reviewId: string) => {
    if (!customUrl.trim()) return;
    setActionInProgress(reviewId);
    try {
      await api.submitReviewDecision(reviewId, {
        decision: 'EDIT',
        replacement_url: customUrl.trim(),
        comment: reviewerComment || 'Manual replacement URL assigned',
        reviewer: 'HUMAN_OPERATOR',
      });
      setNotification({ type: 'success', message: 'Custom URL applied and verified successfully!' });
      setEditingId(null);
      setCustomUrl('');
      setReviewerComment('');
      fetchItems();
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Custom repair failed' });
    } finally {
      setActionInProgress(null);
    }
  };

  const handleNoReplacement = async (reviewId: string) => {
    setActionInProgress(reviewId);
    try {
      await api.submitReviewDecision(reviewId, {
        decision: 'NO_REPLACEMENT',
        comment: reviewerComment || 'Marked as unresolvable dead link',
        reviewer: 'HUMAN_OPERATOR',
      });
      setNotification({ type: 'success', message: 'Item marked as unresolvable dead link.' });
      setReviewerComment('');
      fetchItems();
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Action failed' });
    } finally {
      setActionInProgress(null);
    }
  };

  const filteredItems = items.filter((it) => {
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      (it.broken_url && it.broken_url.toLowerCase().includes(term)) ||
      (it.document_title && it.document_title.toLowerCase().includes(term)) ||
      (it.candidate?.candidate_url && it.candidate.candidate_url.toLowerCase().includes(term)) ||
      (it.anchor_text && it.anchor_text.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <UserCheck className="w-7 h-7 text-indigo-400" />
            Human-in-the-Loop Review Queue
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Review uncertain candidates (Confidence: 65% – 89%), verify replacements, and persist supervised learning feedback.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchItems}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-300 hover:text-white text-sm transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {notification && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-sm ${
            notification.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
              : 'bg-rose-950/40 border-rose-500/40 text-rose-300'
          }`}
        >
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)} className="hover:opacity-75 font-bold">
            ×
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 flex flex-col sm:flex-row gap-4 justify-between items-center">
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {(['PENDING', 'APPROVED', 'REJECTED', 'ALL'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                filter === tab
                  ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/20'
                  : 'bg-gray-800/80 text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search URLs, anchors, titles..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Queue Items */}
      {loading ? (
        <div className="py-20 text-center text-gray-400 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
          <p className="text-sm">Loading review items from repository database...</p>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-gray-900/40 border border-gray-800/80 rounded-2xl p-12 text-center text-gray-400">
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-3 opacity-80" />
          <h3 className="text-base font-semibold text-white">Review Queue Clear</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            No items currently matching the '{filter}' filter. Candidates requiring triage will appear here automatically.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item) => {
            const cand = item.candidate;
            const score = cand?.score;
            const isPending = item.review_status === 'PENDING';
            const isEditing = editingId === item.review_id;

            return (
              <div
                key={item.review_id}
                className="bg-gray-900/80 border border-gray-800/90 hover:border-gray-700/80 rounded-2xl p-6 transition-all shadow-lg shadow-black/20"
              >
                {/* Top Bar: Source Document & Status */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-800/80 pb-4 mb-4">
                  <div className="flex items-center gap-3">
                    <span className="px-2.5 py-1 text-xs font-semibold rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                      {item.document_title || 'Enterprise Document'}
                    </span>
                    {item.section_heading && (
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        § <span className="text-gray-300">{item.section_heading}</span>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2.5 py-1 text-xs font-bold uppercase rounded-md border ${
                        item.review_status === 'APPROVED'
                          ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
                          : item.review_status === 'REJECTED'
                          ? 'bg-rose-500/15 border-rose-500/30 text-rose-400'
                          : item.review_status === 'EDITED'
                          ? 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400'
                          : 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                      }`}
                    >
                      {item.review_status}
                    </span>

                    <span className="text-xs font-mono text-gray-500">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Broken Link Details vs Candidate Replacement */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left Column: Broken Link Context */}
                  <div className="space-y-3 bg-gray-950/60 p-4 rounded-xl border border-rose-950/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5" />
                        Broken Link Reference
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono">
                        {item.failure_type || 'HTTP 404'}
                      </span>
                    </div>

                    <div>
                      <span className="text-[11px] text-gray-500 uppercase font-mono block mb-1">Target URL</span>
                      <a
                        href={item.broken_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-mono text-rose-300 break-all hover:underline flex items-start gap-1"
                      >
                        {item.broken_url}
                        <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5 text-gray-500" />
                      </a>
                    </div>

                    {item.anchor_text && (
                      <div>
                        <span className="text-[11px] text-gray-500 uppercase font-mono block mb-1">Anchor Text</span>
                        <span className="text-xs font-medium text-gray-200 bg-gray-900 px-2 py-1 rounded border border-gray-800 inline-block">
                          "{item.anchor_text}"
                        </span>
                      </div>
                    )}

                    {item.surrounding_context && (
                      <div>
                        <span className="text-[11px] text-gray-500 uppercase font-mono block mb-1">Surrounding Context</span>
                        <p className="text-xs text-gray-400 italic bg-gray-900/80 p-2.5 rounded-lg border border-gray-800/80 leading-relaxed">
                          "{item.surrounding_context}"
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Right Column: AI Discovered Candidate */}
                  <div className="space-y-3 bg-gray-950/60 p-4 rounded-xl border border-indigo-950/30">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" />
                        Top Ranked Candidate
                      </span>
                      {score && (
                        <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                          {Math.round(score.overall_score * 100)}% Confidence
                        </span>
                      )}
                    </div>

                    {cand ? (
                      <>
                        <div>
                          <span className="text-[11px] text-gray-500 uppercase font-mono block mb-1">Candidate Title</span>
                          <span className="text-xs font-semibold text-white block">
                            {cand.title}
                          </span>
                        </div>

                        <div>
                          <span className="text-[11px] text-gray-500 uppercase font-mono block mb-1">Candidate URL</span>
                          <a
                            href={cand.candidate_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-mono text-emerald-400 break-all hover:underline flex items-start gap-1"
                          >
                            {cand.candidate_url}
                            <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5 text-gray-500" />
                          </a>
                        </div>

                        {/* Multi-Factor Radar Scores */}
                        {score && (
                          <div className="pt-2 border-t border-gray-800/80">
                            <span className="text-[11px] text-gray-400 uppercase font-mono block mb-2 font-semibold">
                              Feature Breakdown
                            </span>
                            <div className="grid grid-cols-3 gap-2">
                              <div className="bg-gray-900 p-2 rounded border border-gray-800 text-center">
                                <span className="text-[10px] text-gray-500 block">Semantic</span>
                                <span className="text-xs font-bold text-indigo-300">
                                  {Math.round(score.semantic_similarity * 100)}%
                                </span>
                              </div>
                              <div className="bg-gray-900 p-2 rounded border border-gray-800 text-center">
                                <span className="text-[10px] text-gray-500 block">Title</span>
                                <span className="text-xs font-bold text-cyan-300">
                                  {Math.round(score.title_similarity * 100)}%
                                </span>
                              </div>
                              <div className="bg-gray-900 p-2 rounded border border-gray-800 text-center">
                                <span className="text-[10px] text-gray-500 block">URL Path</span>
                                <span className="text-xs font-bold text-teal-300">
                                  {Math.round(score.url_similarity * 100)}%
                                </span>
                              </div>
                              <div className="bg-gray-900 p-2 rounded border border-gray-800 text-center">
                                <span className="text-[10px] text-gray-500 block">Keywords</span>
                                <span className="text-xs font-bold text-amber-300">
                                  {Math.round(score.keyword_overlap * 100)}%
                                </span>
                              </div>
                              <div className="bg-gray-900 p-2 rounded border border-gray-800 text-center">
                                <span className="text-[10px] text-gray-500 block">Domain</span>
                                <span className="text-xs font-bold text-emerald-300">
                                  {Math.round(score.domain_score * 100)}%
                                </span>
                              </div>
                              <div className="bg-gray-900 p-2 rounded border border-gray-800 text-center">
                                <span className="text-[10px] text-gray-500 block">Quality</span>
                                <span className="text-xs font-bold text-purple-300">
                                  {Math.round(score.content_quality_score * 100)}%
                                </span>
                              </div>
                            </div>
                          </div>
                        )}

                        {score?.explanation && (
                          <div className="p-2.5 rounded bg-indigo-950/20 border border-indigo-900/30 text-xs text-indigo-200/90 leading-relaxed">
                            <span className="font-semibold text-indigo-300">Explanation: </span>
                            {score.explanation}
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="text-xs text-gray-500 py-6 text-center">
                        No candidate replacement discovered.
                      </div>
                    )}
                  </div>
                </div>

                {/* Edit URL Input Area */}
                {isEditing && (
                  <div className="mt-4 p-4 rounded-xl bg-gray-950 border border-cyan-500/30 space-y-3">
                    <span className="text-xs font-semibold text-cyan-400 block">Specify Custom Verified URL:</span>
                    <input
                      type="url"
                      placeholder="https://intranet.corp/..."
                      value={customUrl}
                      onChange={(e) => setCustomUrl(e.target.value)}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-400"
                    />
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleCustomSubmit(item.review_id)}
                        disabled={actionInProgress === item.review_id || !customUrl.trim()}
                        className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold"
                      >
                        Confirm & Patch Document
                      </button>
                    </div>
                  </div>
                )}

                {/* Operator Actions Bar */}
                {isPending && (
                  <div className="mt-5 pt-4 border-t border-gray-800 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex-1 max-w-md">
                      <input
                        type="text"
                        placeholder="Optional operator comment / justification..."
                        value={reviewerComment}
                        onChange={(e) => setReviewerComment(e.target.value)}
                        className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-xs text-gray-300 placeholder-gray-600 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        onClick={() => handleApprove(item.review_id)}
                        disabled={actionInProgress === item.review_id || !cand}
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md shadow-emerald-900/30 disabled:opacity-50"
                      >
                        <Check className="w-3.5 h-3.5" />
                        Approve & Remediate
                      </button>

                      <button
                        onClick={() => handleReject(item.review_id)}
                        disabled={actionInProgress === item.review_id}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-rose-950/60 hover:bg-rose-900/60 border border-rose-800/50 text-rose-300 text-xs font-semibold transition-all disabled:opacity-50"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        Reject
                      </button>

                      <button
                        onClick={() => {
                          setEditingId(item.review_id);
                          setCustomUrl(cand?.candidate_url || '');
                        }}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold transition-all"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        Edit URL
                      </button>

                      <button
                        onClick={() => handleNoReplacement(item.review_id)}
                        disabled={actionInProgress === item.review_id}
                        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-gray-900 hover:bg-gray-800 text-gray-400 hover:text-gray-300 text-xs transition-all"
                      >
                        <HelpCircle className="w-3.5 h-3.5" />
                        No Replacement
                      </button>
                    </div>
                  </div>
                )}

                {/* Audit details if resolved */}
                {!isPending && (
                  <div className="mt-4 pt-3 border-t border-gray-800/60 text-xs text-gray-500 flex items-center justify-between">
                    <span>
                      Reviewed by: <strong className="text-gray-400">{item.reviewer || 'HUMAN_OPERATOR'}</strong>
                      {item.reviewer_comment && ` — "${item.reviewer_comment}"`}
                    </span>
                    <span>{item.reviewed_at ? new Date(item.reviewed_at).toLocaleString() : ''}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
