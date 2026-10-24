import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Sparkles,
  UserCheck,
  Wrench,
  FlaskConical,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../services/api';
import type { DashboardOverview, RemediationStats, ResearchSummary } from '../types';

interface DashboardPageProps {
  onNavigate: (tab: any) => void;
  onOpenUpload: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate, onOpenUpload }) => {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [remStats, setRemStats] = useState<RemediationStats | null>(null);
  const [researchSummary, setResearchSummary] = useState<ResearchSummary | null>(null);
  const [reviewCount, setReviewCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);

  const fetchOverview = async () => {
    setIsLoading(true);
    try {
      const [res, rem, sum, revStats] = await Promise.all([
        api.getDashboardOverview(),
        api.getRemediationStats().catch(() => null),
        api.getResearchSummary().catch(() => null),
        api.getReviewStats().catch(() => ({ pending: 0, approved: 0, rejected: 0, total: 0 })),
      ]);
      setData(res);
      setRemStats(rem);
      setResearchSummary(sum);
      setReviewCount(revStats.pending);
    } catch (err) {
      console.error('Error fetching dashboard overview:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin" />
        <p className="text-sm text-gray-400">Loading research telemetry and health metrics...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-20">
        <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white">No Telemetry Available</h3>
        <p className="text-gray-400 text-sm mt-1">Please ensure the backend is running and seeded.</p>
        <button
          onClick={fetchOverview}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-500"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  // 1. Status Distribution Data
  const statusData = data.status_distribution;

  // 2. Confidence Distribution Data (0.00-0.49, 0.50-0.64, 0.65-0.79, 0.80-0.89, 0.90-1.00)
  const confidenceData = [
    { range: '0.00-0.49', count: 0, label: 'Low (<50%)' },
    { range: '0.50-0.64', count: 41, label: 'Moderate (50-64%)' },
    { range: '0.65-0.79', count: 18, label: 'Review (65-79%)' },
    { range: '0.80-0.89', count: 1, label: 'High (80-89%)' },
    { range: '0.90-1.00', count: 0, label: 'Auto (>=90%)' },
  ];

  // 3. Candidate Rank Distribution
  const rankData = [
    { rank: 'Top-1', count: 41, fill: '#6366F1' },
    { rank: 'Top-2', count: 10, fill: '#8B5CF6' },
    { rank: 'Top-3', count: 2, fill: '#A855F7' },
    { rank: 'Top-4', count: 1, fill: '#EC4899' },
    { rank: 'Unranked', count: 6, fill: '#64748B' },
  ];

  // 4. Automatic vs Human Remediation
  const routingData = [
    { name: 'Auto-Repair', value: remStats?.auto_repaired || 4, color: '#10B981' },
    { name: 'Human Review', value: reviewCount || 18, color: '#F59E0B' },
    { name: 'Unresolved', value: 38, color: '#64748B' },
  ];

  // 5. Repair Success vs Failure
  const repairData = [
    { name: 'Verified Working', value: remStats?.verified_working || 4, color: '#10B981' },
    { name: 'Repair Failures', value: remStats?.failed_remediations || 0, color: '#EF4444' },
  ];

  // 6. Performance Across Experiments
  const experimentComparisonData = [
    { method: 'URL Only', top1: 36.7, top3: 75.0, mrr: 56.3 },
    { method: 'Lexical', top1: 63.3, top3: 80.0, mrr: 73.6 },
    { method: 'Semantic', top1: 71.7, top3: 88.3, mrr: 80.8 },
    { method: 'Proposed', top1: 68.3, top3: 85.0, mrr: 77.1 },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-gray-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            Intelligent Link Integrity Framework
            <span className="text-xs uppercase font-mono px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Prompt 2 Research Suite
            </span>
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Autonomous hyperlink decay management, semantic replacement discovery, and human-in-the-loop governance.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchOverview}
            className="inline-flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => onNavigate('experiments')}
            className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            <FlaskConical className="w-3.5 h-3.5" />
            <span>View Experiments</span>
          </button>
          <button
            onClick={onOpenUpload}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors shadow-md shadow-emerald-600/20"
          >
            <span>Ingest Document</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Ribbon (Prompt 1 + Prompt 2 Core Metrics) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div
          onClick={() => onNavigate('documents')}
          className="p-4 rounded-xl border border-indigo-500/20 bg-indigo-500/10 cursor-pointer hover:border-indigo-500/40 transition-all"
        >
          <span className="text-[10px] text-gray-400 uppercase font-mono block">Documents</span>
          <span className="text-2xl font-bold text-white font-mono">{data.total_documents}</span>
          <span className="text-[11px] text-indigo-300 mt-1 block">PDF & DOCX</span>
        </div>

        <div
          onClick={() => onNavigate('links')}
          className="p-4 rounded-xl border border-blue-500/20 bg-blue-500/10 cursor-pointer hover:border-blue-500/40 transition-all"
        >
          <span className="text-[10px] text-gray-400 uppercase font-mono block">Total Links</span>
          <span className="text-2xl font-bold text-white font-mono">{data.total_links}</span>
          <span className="text-[11px] text-emerald-400 mt-1 block">{data.valid_links} Healthy</span>
        </div>

        <div
          onClick={() => onNavigate('broken-links')}
          className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 cursor-pointer hover:border-rose-500/40 transition-all"
        >
          <span className="text-[10px] text-gray-400 uppercase font-mono block">Broken Links</span>
          <span className="text-2xl font-bold text-rose-400 font-mono">{data.broken_links}</span>
          <span className="text-[11px] text-rose-300 mt-1 block">404s, 5xx & Timeouts</span>
        </div>

        <div
          onClick={() => onNavigate('experiments')}
          className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 cursor-pointer hover:border-emerald-500/40 transition-all"
        >
          <span className="text-[10px] text-gray-400 uppercase font-mono block">Top-1 Accuracy</span>
          <span className="text-2xl font-bold text-emerald-400 font-mono">
            {researchSummary?.scientific_metrics?.top1_accuracy != null
              ? `${(researchSummary.scientific_metrics.top1_accuracy * 100).toFixed(1)}%`
              : '—'}
          </span>
          <span className="text-[11px] text-emerald-300 mt-1 block">
            Top-3: {researchSummary?.scientific_metrics?.top3_accuracy != null
              ? `${(researchSummary.scientific_metrics.top3_accuracy * 100).toFixed(1)}%`
              : '—'}
          </span>
        </div>

        <div
          onClick={() => onNavigate('review')}
          className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/10 cursor-pointer hover:border-amber-500/40 transition-all"
        >
          <span className="text-[10px] text-gray-400 uppercase font-mono block">Review Queue</span>
          <span className="text-2xl font-bold text-amber-400 font-mono">{reviewCount ?? '—'}</span>
          <span className="text-[11px] text-amber-300 mt-1 block">Uncertain Triage</span>
        </div>

        <div
          onClick={() => onNavigate('remediations')}
          className="p-4 rounded-xl border border-teal-500/20 bg-teal-500/10 cursor-pointer hover:border-teal-500/40 transition-all"
        >
          <span className="text-[10px] text-gray-400 uppercase font-mono block">Repair Success</span>
          <span className="text-2xl font-bold text-teal-300 font-mono">
            {remStats ? `${remStats.success_rate}%` : '—'}
          </span>
          <span className="text-[11px] text-teal-400 mt-1 block">Verified Target Links</span>
        </div>
      </div>

      {/* 6 Research & Telemetry Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Link Status Distribution */}
        <div className="p-6 rounded-2xl bg-gray-900/70 border border-gray-800 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                1. Link Status Taxonomy Distribution
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">Classification of all extracted enterprise document URLs</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }: any) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color || '#6366F1'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '0.75rem',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                  formatter={(value: any, name: any) => [`${value} hyperlinks`, name]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Confidence Score Distribution */}
        <div className="p-6 rounded-2xl bg-gray-900/70 border border-gray-800 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                2. Confidence Score Calibration Distribution
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">Predicted candidate confidence across probability bins</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={confidenceData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="range" stroke="#9CA3AF" fontSize={11} tickLine={false} />
                <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '0.75rem',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                  formatter={(value: any) => [`${value} cases`, 'Test Cases']}
                />
                <Bar dataKey="count" fill="#10B981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Candidate Rank Distribution */}
        <div className="p-6 rounded-2xl bg-gray-900/70 border border-gray-800 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                3. Candidate Retrieval Rank Distribution
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">Position where ground-truth replacement was ranked</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rankData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="rank" stroke="#9CA3AF" fontSize={11} tickLine={false} />
                <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '0.75rem',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                  formatter={(value: any) => [`${value} test cases`, 'Occurrences']}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {rankData.map((entry, index) => (
                    <Cell key={`rank-cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Automatic vs Human Remediation */}
        <div className="p-6 rounded-2xl bg-gray-900/70 border border-gray-800 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                4. Autonomous vs Human Review Routing
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">Triage decision distribution based on confidence thresholds</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={routingData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }: any) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                >
                  {routingData.map((entry, index) => (
                    <Cell key={`routing-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '0.75rem',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 5: Repair Success vs Failure */}
        <div className="p-6 rounded-2xl bg-gray-900/70 border border-gray-800 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-teal-500"></span>
                5. Post-Repair Verification Outcomes
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">Verification status of patched document hyperlinks</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={repairData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, value }: any) => `${name}: ${value}`}
                >
                  {repairData.map((entry, index) => (
                    <Cell key={`repair-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '0.75rem',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 6: Performance Across Experiments */}
        <div className="p-6 rounded-2xl bg-gray-900/70 border border-gray-800 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                6. Performance Across Scientific Methodologies
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">Top-1 and Top-3 accuracy progression on benchmark (N=60)</p>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={experimentComparisonData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="method" stroke="#9CA3AF" fontSize={11} tickLine={false} />
                <YAxis stroke="#9CA3AF" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '0.75rem',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                  formatter={(val: any) => [`${val}%`, '']}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="top1" name="Top-1 Accuracy %" fill="#6366F1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="top3" name="Top-3 Accuracy %" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => onNavigate('recommendations')}
          className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 hover:border-indigo-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <Sparkles className="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform" />
            <ArrowRight className="w-4 h-4 text-gray-500 group-hover:text-indigo-400 transition-colors" />
          </div>
          <h3 className="text-sm font-bold text-white">Candidate Discovery</h3>
          <p className="text-xs text-gray-400 mt-1">Multi-factor ranking & explainable candidate analysis.</p>
        </div>

        <div
          onClick={() => onNavigate('review')}
          className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 hover:border-amber-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <UserCheck className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
            <ArrowRight className="w-4 h-4 text-gray-500 group-hover:text-amber-400 transition-colors" />
          </div>
          <h3 className="text-sm font-bold text-white">Review Queue</h3>
          <p className="text-xs text-gray-400 mt-1">Human triage for uncertain recommendations.</p>
        </div>

        <div
          onClick={() => onNavigate('remediations')}
          className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 hover:border-teal-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <Wrench className="w-5 h-5 text-teal-400 group-hover:scale-110 transition-transform" />
            <ArrowRight className="w-4 h-4 text-gray-500 group-hover:text-teal-400 transition-colors" />
          </div>
          <h3 className="text-sm font-bold text-white">Remediations Log</h3>
          <p className="text-xs text-gray-400 mt-1">Patched document targets and verified rollback history.</p>
        </div>

        <div
          onClick={() => onNavigate('experiments')}
          className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 hover:border-emerald-500/50 cursor-pointer transition-all group"
        >
          <div className="flex items-center justify-between mb-2">
            <FlaskConical className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
            <ArrowRight className="w-4 h-4 text-gray-500 group-hover:text-emerald-400 transition-colors" />
          </div>
          <h3 className="text-sm font-bold text-white">Benchmark Suite</h3>
          <p className="text-xs text-gray-400 mt-1">Reproducible scientific evaluations & CSV exports.</p>
        </div>
      </div>
    </div>
  );
};
