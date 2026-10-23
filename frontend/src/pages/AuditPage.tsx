import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  RefreshCw,
  Search,
  Filter,
  ArrowRight,
  User,
  Cpu,
} from 'lucide-react';
import { api } from '../services/api';
import type { AuditLogItem } from '../types';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState<string>('ALL');
  const [search, setSearch] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs();
      setLogs(data);
    } catch {
      // Offline fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const actionTypes = [
    'ALL',
    'CANDIDATES_FOUND',
    'CANDIDATE_RANKED',
    'AUTO_REPAIR_SELECTED',
    'AUTO_REPAIRED',
    'HUMAN_REVIEW_REQUIRED',
    'HUMAN_APPROVED',
    'HUMAN_REJECTED',
    'REPAIR_VERIFIED',
    'DOCUMENT_SCAN_COMPLETED',
  ];

  const filteredLogs = logs.filter((l) => {
    const matchesAction = filterAction === 'ALL' || l.action_type === filterAction;
    if (!matchesAction) return false;
    if (!search) return true;
    const term = search.toLowerCase();
    return (
      l.action_type.toLowerCase().includes(term) ||
      (l.reason && l.reason.toLowerCase().includes(term)) ||
      (l.old_url && l.old_url.toLowerCase().includes(term)) ||
      (l.new_url && l.new_url.toLowerCase().includes(term)) ||
      l.actor.toLowerCase().includes(term)
    );
  });

  const getActionBadgeColor = (action: string) => {
    if (action.includes('APPROVED') || action.includes('VERIFIED')) return 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400';
    if (action.includes('REJECTED') || action.includes('FAILED')) return 'bg-rose-500/15 border-rose-500/30 text-rose-400';
    if (action.includes('AUTO_REPAIR')) return 'bg-indigo-500/15 border-indigo-500/30 text-indigo-300';
    if (action.includes('REVIEW_REQUIRED')) return 'bg-amber-500/15 border-amber-500/30 text-amber-400';
    return 'bg-gray-800 border-gray-700 text-gray-300';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <ShieldCheck className="w-7 h-7 text-indigo-400" />
            Immutable Audit Trail & Governance Log
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Complete compliance logging for automated remediation decisions, document backups, and human operator actions.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-300 hover:text-white text-sm transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh Audit Log
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 justify-between items-center">
        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          <Filter className="w-4 h-4 text-gray-500 flex-shrink-0" />
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 font-mono"
          >
            {actionTypes.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>

        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search action, reason, URL or actor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Audit Log Table */}
      {loading ? (
        <div className="py-20 text-center text-gray-400 flex flex-col items-center justify-center space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-400" />
          <p className="text-sm">Retrieving audit event ledger...</p>
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="bg-gray-900/40 border border-gray-800/80 rounded-2xl p-12 text-center text-gray-400">
          <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto mb-3 opacity-60" />
          <h3 className="text-base font-semibold text-white">No Audit Events Found</h3>
          <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
            System actions and operator reviews will record immutable audit events here.
          </p>
        </div>
      ) : (
        <div className="bg-gray-900/80 border border-gray-800 rounded-2xl overflow-hidden shadow-xl shadow-black/20">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="bg-gray-950/80 text-gray-400 uppercase font-mono border-b border-gray-800">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Action Event</th>
                  <th className="py-3 px-4">Hyperlink Context</th>
                  <th className="py-3 px-4">Status / Reason</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Actor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60 font-sans">
                {filteredLogs.map((l) => (
                  <tr key={l.audit_id} className="hover:bg-gray-800/40 transition-colors">
                    <td className="py-3 px-4 text-gray-500 font-mono whitespace-nowrap">
                      {new Date(l.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded text-[11px] font-mono font-semibold border ${getActionBadgeColor(
                          l.action_type
                        )}`}
                      >
                        {l.action_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 max-w-[300px]">
                      {l.old_url ? (
                        <div className="space-y-0.5">
                          <span className="text-[11px] font-mono text-gray-400 truncate block">
                            {l.old_url}
                          </span>
                          {l.new_url && (
                            <div className="flex items-center gap-1 text-[11px] font-mono text-emerald-400">
                              <ArrowRight className="w-3 h-3 text-gray-500 flex-shrink-0" />
                              <span className="truncate">{l.new_url}</span>
                            </div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-500 font-mono text-[11px]">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-gray-300 max-w-[260px] truncate">
                      {l.reason || l.status || 'OK'}
                    </td>
                    <td className="py-3 px-4 font-mono font-semibold text-gray-300">
                      {l.confidence_score !== undefined && l.confidence_score !== null
                        ? `${Math.round(l.confidence_score * 100)}%`
                        : '—'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 font-mono text-xs text-gray-400">
                        {l.actor === 'SYSTEM' ? (
                          <Cpu className="w-3 h-3 text-indigo-400" />
                        ) : (
                          <User className="w-3 h-3 text-cyan-400" />
                        )}
                        {l.actor}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
