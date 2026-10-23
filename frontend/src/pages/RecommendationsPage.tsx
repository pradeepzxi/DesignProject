import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Search,
  ExternalLink,
  Wrench,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Award,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import type { LinkItem, RecommendationResult } from '../types';

export const RecommendationsPage: React.FC = () => {
  const [brokenLinks, setBrokenLinks] = useState<LinkItem[]>([]);
  const [selectedLinkId, setSelectedLinkId] = useState<string>('');
  const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [linksLoading, setLinksLoading] = useState(true);
  const [repairing, setRepairing] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    fetchBrokenLinks();
  }, []);

  const fetchBrokenLinks = async () => {
    setLinksLoading(true);
    try {
      const data = await api.getLinks({ broken_only: true, limit: 100 });
      setBrokenLinks(data);
      if (data.length > 0) {
        setSelectedLinkId(data[0].link_id);
      }
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to fetch broken links' });
    } finally {
      setLinksLoading(false);
    }
  };

  const handleGenerateRecommendation = async (linkId: string) => {
    if (!linkId) return;
    setLoading(true);
    setRecommendation(null);
    try {
      const res = await api.recommendReplacement(linkId, false);
      setRecommendation(res);
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to discover candidates' });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyRepair = async (candidateUrl?: string) => {
    if (!selectedLinkId) return;
    setRepairing(true);
    try {
      const res = await api.repairLink(selectedLinkId, {
        candidate_url: candidateUrl,
        reviewer: 'HUMAN_OPERATOR',
      });
      if (res.success) {
        setNotification({
          type: 'success',
          message: `Autonomous repair successful! Replaced target with ${res.remediation.new_url} and verified working.`,
        });
        fetchBrokenLinks();
      } else {
        setNotification({
          type: 'error',
          message: `Repair failed: ${res.detail || 'Could not verify target'}`,
        });
      }
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Repair execution failed' });
    } finally {
      setRepairing(false);
    }
  };

  const selectedLink = brokenLinks.find((l) => l.link_id === selectedLinkId);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Sparkles className="w-7 h-7 text-indigo-400" />
            Candidate Discovery & Ranking
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Contextual semantic replacement discovery, multi-factor scoring, and explainable AI recommendations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => handleGenerateRecommendation(selectedLinkId)}
            disabled={loading || !selectedLinkId}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-md shadow-indigo-600/25 disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Discover & Rank Candidates
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

      {/* Broken Link Selector Card */}
      <div className="bg-gray-900/70 border border-gray-800 rounded-2xl p-6">
        <label className="text-xs font-mono uppercase text-gray-400 font-semibold block mb-2">
          Select Broken Hyperlink to Remediate:
        </label>
        {linksLoading ? (
          <div className="text-xs text-gray-500 py-3">Loading links...</div>
        ) : brokenLinks.length === 0 ? (
          <div className="text-sm text-emerald-400 py-2">
            No broken links found! All documents are healthy or upload documents to test.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
            <div className="md:col-span-2">
              <select
                value={selectedLinkId}
                onChange={(e) => {
                  setSelectedLinkId(e.target.value);
                  setRecommendation(null);
                }}
                className="w-full bg-gray-950 border border-gray-700 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              >
                {brokenLinks.map((l) => (
                  <option key={l.link_id} value={l.link_id}>
                    [{l.status}] {l.original_url} ({l.document_title || 'Doc'})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => handleGenerateRecommendation(selectedLinkId)}
              disabled={loading || !selectedLinkId}
              className="px-4 py-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold transition-all border border-gray-700 flex items-center justify-center gap-2"
            >
              {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              Analyze & Score Candidates
            </button>
          </div>
        )}

        {/* Selected Link Context Card */}
        {selectedLink && (
          <div className="mt-4 pt-4 border-t border-gray-800/80 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-gray-500 block mb-1">Source Document</span>
              <span className="text-white font-medium">{selectedLink.document_title || 'Enterprise Policy'}</span>
            </div>
            <div>
              <span className="text-gray-500 block mb-1">Failure Mode</span>
              <span className="text-rose-400 font-mono font-semibold">{selectedLink.status}</span>
            </div>
            <div>
              <span className="text-gray-500 block mb-1">Anchor Text</span>
              <span className="text-gray-300 italic">"{selectedLink.context?.anchor_text || 'Link'}"</span>
            </div>
            <div>
              <span className="text-gray-500 block mb-1">Section Heading</span>
              <span className="text-gray-300">{selectedLink.context?.section_heading || 'General'}</span>
            </div>
          </div>
        )}
      </div>

      {/* Recommendation Results */}
      {loading ? (
        <div className="py-20 text-center text-gray-400 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
          <p className="text-sm">Running multi-factor candidate discovery & cosine semantic vectorization...</p>
        </div>
      ) : recommendation ? (
        <div className="space-y-6">
          {/* Engine Routing Decision Banner */}
          <div
            className={`p-6 rounded-2xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${
              recommendation.decision === 'AUTO_REPAIR'
                ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
                : recommendation.decision === 'HUMAN_REVIEW'
                ? 'bg-amber-950/30 border-amber-500/40 text-amber-200'
                : 'bg-rose-950/30 border-rose-500/40 text-rose-200'
            }`}
          >
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-gray-950/80 border border-current">
                {recommendation.decision === 'AUTO_REPAIR' ? (
                  <ShieldCheck className="w-6 h-6 text-emerald-400" />
                ) : recommendation.decision === 'HUMAN_REVIEW' ? (
                  <AlertTriangle className="w-6 h-6 text-amber-400" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-rose-400" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold tracking-wider uppercase">
                    Decision: {recommendation.decision}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-black/40">
                    Confidence: {Math.round(recommendation.confidence_score * 100)}%
                  </span>
                </div>
                <p className="text-xs text-gray-300 mt-1">{recommendation.decision_reason}</p>
              </div>
            </div>

            {recommendation.top_candidate && (
              <button
                onClick={() => handleApplyRepair(recommendation.top_candidate?.candidate_url)}
                disabled={repairing}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-900/30 flex items-center gap-2 whitespace-nowrap"
              >
                {repairing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Wrench className="w-4 h-4" />}
                Apply Autonomous Repair
              </button>
            )}
          </div>

          {/* Ranked Candidates Table */}
          <div className="bg-gray-900/80 border border-gray-800 rounded-2xl p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-indigo-400" />
              Ranked Replacement Candidates ({recommendation.ranked_candidates.length})
            </h3>

            {recommendation.ranked_candidates.length === 0 ? (
              <p className="text-xs text-gray-500 py-6 text-center">
                No candidates satisfied candidate discovery filters.
              </p>
            ) : (
              <div className="space-y-4">
                {recommendation.ranked_candidates.map((cand, idx) => {
                  const s = cand.score;
                  return (
                    <div
                      key={cand.candidate_id || idx}
                      className={`p-5 rounded-xl border transition-all ${
                        idx === 0
                          ? 'bg-indigo-950/20 border-indigo-500/40 shadow-md shadow-indigo-950/20'
                          : 'bg-gray-950/50 border-gray-800 hover:border-gray-700'
                      }`}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2.5">
                          <span
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                              idx === 0
                                ? 'bg-indigo-600 text-white'
                                : 'bg-gray-800 text-gray-400'
                            }`}
                          >
                            {idx + 1}
                          </span>
                          <div>
                            <span className="text-sm font-semibold text-white block">
                              {cand.title}
                            </span>
                            <a
                              href={cand.candidate_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs font-mono text-emerald-400 hover:underline flex items-center gap-1 mt-0.5"
                            >
                              {cand.candidate_url}
                              <ExternalLink className="w-3 h-3 text-gray-500" />
                            </a>
                          </div>
                        </div>

                        {s && (
                          <div className="text-right">
                            <span className="text-base font-bold text-indigo-400 block font-mono">
                              {Math.round(s.overall_score * 100)}%
                            </span>
                            <span className="text-[10px] text-gray-500 uppercase font-mono">
                              Overall Score
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Multi-Factor Feature Grid */}
                      {s && (
                        <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 my-3 pt-3 border-t border-gray-800/80">
                          <div className="bg-gray-900/90 p-2 rounded text-center">
                            <span className="text-[10px] text-gray-500 block">Semantic</span>
                            <span className="text-xs font-mono font-bold text-indigo-300">
                              {Math.round(s.semantic_similarity * 100)}%
                            </span>
                          </div>
                          <div className="bg-gray-900/90 p-2 rounded text-center">
                            <span className="text-[10px] text-gray-500 block">Title</span>
                            <span className="text-xs font-mono font-bold text-cyan-300">
                              {Math.round(s.title_similarity * 100)}%
                            </span>
                          </div>
                          <div className="bg-gray-900/90 p-2 rounded text-center">
                            <span className="text-[10px] text-gray-500 block">URL Path</span>
                            <span className="text-xs font-mono font-bold text-teal-300">
                              {Math.round(s.url_similarity * 100)}%
                            </span>
                          </div>
                          <div className="bg-gray-900/90 p-2 rounded text-center">
                            <span className="text-[10px] text-gray-500 block">Keywords</span>
                            <span className="text-xs font-mono font-bold text-amber-300">
                              {Math.round(s.keyword_overlap * 100)}%
                            </span>
                          </div>
                          <div className="bg-gray-900/90 p-2 rounded text-center">
                            <span className="text-[10px] text-gray-500 block">Domain</span>
                            <span className="text-xs font-mono font-bold text-emerald-300">
                              {Math.round(s.domain_score * 100)}%
                            </span>
                          </div>
                          <div className="bg-gray-900/90 p-2 rounded text-center">
                            <span className="text-[10px] text-gray-500 block">Quality</span>
                            <span className="text-xs font-mono font-bold text-purple-300">
                              {Math.round(s.content_quality_score * 100)}%
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Explanation */}
                      {s?.explanation && (
                        <div className="mt-3 p-3 rounded-lg bg-gray-950/80 border border-gray-800/80 text-xs text-gray-300 flex items-start gap-2">
                          <span className="font-semibold text-indigo-400 whitespace-nowrap">Explanation:</span>
                          <span className="text-gray-300 leading-relaxed">{s.explanation}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-gray-900/40 border border-gray-800/80 rounded-2xl p-12 text-center text-gray-400">
          <Layers className="w-12 h-12 text-indigo-400 mx-auto mb-3 opacity-60" />
          <h3 className="text-base font-semibold text-white">Ready for Candidate Discovery</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            Choose a broken hyperlink above and click "Discover & Rank Candidates" to extract contextual features and evaluate replacements.
          </p>
        </div>
      )}
    </div>
  );
};
