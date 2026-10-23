import React, { useState, useEffect } from 'react';
import {
  Wrench,
  CheckCircle,
  XCircle,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  Search,
  ArrowRight,
  User,
  Cpu,
} from 'lucide-react';
import { api } from '../services/api';
import type { RemediationItem, RemediationStats } from '../types';

export const RemediationsPage: React.FC = () => {
  const [remediations, setRemediations] = useState<RemediationItem[]>([]);
  const [stats, setStats] = useState<RemediationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [rems, st] = await Promise.all([
        api.getRemediations(0, 100),
        api.getRemediationStats(),
      ]);
      setRemediations(rems);
      setStats(st);
    } catch {
      // Offline fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filtered = remediations.filter((r) => {
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      r.old_url.toLowerCase().includes(term) ||
      r.new_url.toLowerCase().includes(term) ||
      (r.document_filename && r.document_filename.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Wrench className="w-7 h-7 text-indigo-400" />
            Autonomous & Manual Remediations
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Historical document patching audit, physical document backups, and post-repair verification probes.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-300 hover:text-white text-sm transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-4">
          <span className="text-xs text-gray-500 uppercase font-mono block mb-1">Total Remediated</span>
          <span className="text-2xl font-bold text-white font-mono">{stats?.total_remediations || 0}</span>
        </div>

        <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-4">
          <span className="text-xs text-indigo-400 uppercase font-mono block mb-1">Autonomous</span>
          <span className="text-2xl font-bold text-indigo-300 font-mono">{stats?.auto_repaired || 0}</span>
        </div>

        <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-4">
          <span className="text-xs text-cyan-400 uppercase font-mono block mb-1">Manual Approved</span>
          <span className="text-2xl font-bold text-cyan-300 font-mono">{stats?.manual_approved || 0}</span>
        </div>

        <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-4">
          <span className="text-xs text-emerald-400 uppercase font-mono block mb-1">Verified Working</span>
          <span className="text-2xl font-bold text-emerald-300 font-mono">{stats?.verified_working || 0}</span>
        </div>

        <div className="bg-gray-900/70 border border-gray-800 rounded-xl p-4">
          <span className="text-xs text-emerald-400 uppercase font-mono block mb-1">Success Rate</span>
          <span className="text-2xl font-bold text-emerald-400 font-mono">
            {stats ? `${stats.success_rate}%` : '100%'}
          </span>
        </div>
      </div>

      {/* Search Input */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search URLs or document filenames..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 font-sans"
          />
        </div>

        <span className="text-xs text-gray-500 font-mono hidden sm:inline">
          Showing {filtered.length} of {remediations.length} events
        </span>
      </div>

      {/* Remediation Events Table */}
      {loading ? (
        <div className="py-20 text-center text-gray-400 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
          <p className="text-sm">Loading remediation history...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-gray-900/40 border border-gray-800/80 rounded-2xl p-12 text-center text-gray-400">
          <ShieldCheck className="w-12 h-12 text-indigo-400 mx-auto mb-3 opacity-60" />
          <h3 className="text-base font-semibold text-white">No Remediations Logged Yet</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            Autonomous repairs and human approvals will record full rollback backups and live verification logs here.
          </p>
        </div>
      ) : (
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl overflow-hidden shadow-xl shadow-black/20">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-950/80 text-gray-400 uppercase font-mono border-b border-gray-800">
                <tr>
                  <th className="py-3 px-4">Document</th>
                  <th className="py-3 px-4">Hyperlink Replacement</th>
                  <th className="py-3 px-4">Action Mode</th>
                  <th className="py-3 px-4">Post-Repair Status</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60 font-sans">
                {filtered.map((r) => {
                  const isAuto = r.action === 'AUTO_REPAIRED';
                  const isVerified = r.validation_result === 'VERIFIED_WORKING';

                  return (
                    <tr key={r.remediation_id} className="hover:bg-gray-800/40 transition-colors">
                      <td className="py-3.5 px-4 font-medium text-white max-w-[180px] truncate">
                        {r.document_filename || 'policy_document.docx'}
                      </td>
                      <td className="py-3.5 px-4 max-w-[320px]">
                        <div className="space-y-1">
                          <span className="text-[11px] font-mono text-rose-400 line-through truncate block">
                            {r.old_url}
                          </span>
                          <div className="flex items-center gap-1.5 text-emerald-400 font-mono text-xs">
                            <ArrowRight className="w-3 h-3 text-gray-500 flex-shrink-0" />
                            <a
                              href={r.new_url}
                              target="_blank"
                              rel="noreferrer"
                              className="truncate hover:underline flex items-center gap-1"
                            >
                              {r.new_url}
                              <ExternalLink className="w-3 h-3 text-gray-500 flex-shrink-0" />
                            </a>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-semibold text-[11px] border ${
                            isAuto
                              ? 'bg-indigo-500/15 border-indigo-500/30 text-indigo-300'
                              : 'bg-cyan-500/15 border-cyan-500/30 text-cyan-300'
                          }`}
                        >
                          {isAuto ? <Cpu className="w-3 h-3" /> : <User className="w-3 h-3" />}
                          {r.action}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold ${
                            isVerified
                              ? 'bg-emerald-500/15 text-emerald-400'
                              : 'bg-rose-500/15 text-rose-400'
                          }`}
                        >
                          {isVerified ? (
                            <CheckCircle className="w-3 h-3" />
                          ) : (
                            <XCircle className="w-3 h-3" />
                          )}
                          {r.validation_result || 'VERIFIED'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono font-semibold text-gray-200">
                        {r.confidence_score ? `${Math.round(r.confidence_score * 100)}%` : '100%'}
                      </td>
                      <td className="py-3.5 px-4 text-gray-400 font-mono">{r.actor}</td>
                      <td className="py-3.5 px-4 text-gray-500 font-mono whitespace-nowrap">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
