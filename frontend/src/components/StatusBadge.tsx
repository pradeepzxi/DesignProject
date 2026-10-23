import React from 'react';
import {
  CheckCircle2,
  AlertCircle,
  Clock,
  ExternalLink,
  ShieldAlert,
  HelpCircle,
  WifiOff,
  ServerCrash,
} from 'lucide-react';

interface StatusBadgeProps {
  status: string;
  statusCode?: number | null;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, statusCode, size = 'sm' }) => {
  const getBadgeConfig = () => {
    switch (status) {
      case 'VALID':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
          icon: <CheckCircle2 className="w-3.5 h-3.5 mr-1" />,
          label: statusCode ? `Valid (${statusCode})` : 'Valid',
        };
      case 'REDIRECT':
        return {
          bg: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
          icon: <ExternalLink className="w-3.5 h-3.5 mr-1" />,
          label: statusCode ? `Redirect (${statusCode})` : 'Redirect',
        };
      case 'BROKEN_404':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
          icon: <AlertCircle className="w-3.5 h-3.5 mr-1" />,
          label: '404 Not Found',
        };
      case 'BROKEN_4XX':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
          icon: <AlertCircle className="w-3.5 h-3.5 mr-1" />,
          label: statusCode ? `Client Error (${statusCode})` : 'Broken (4xx)',
        };
      case 'SERVER_ERROR_5XX':
        return {
          bg: 'bg-red-500/10 text-red-400 border-red-500/20',
          icon: <ServerCrash className="w-3.5 h-3.5 mr-1" />,
          label: statusCode ? `Server Error (${statusCode})` : 'Server Error (5xx)',
        };
      case 'TIMEOUT':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
          icon: <Clock className="w-3.5 h-3.5 mr-1" />,
          label: 'Timeout',
        };
      case 'DNS_ERROR':
        return {
          bg: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
          icon: <WifiOff className="w-3.5 h-3.5 mr-1" />,
          label: 'DNS Resolution Failed',
        };
      case 'CONNECTION_ERROR':
        return {
          bg: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
          icon: <WifiOff className="w-3.5 h-3.5 mr-1" />,
          label: 'Connection Error',
        };
      case 'FORBIDDEN':
        return {
          bg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
          icon: <ShieldAlert className="w-3.5 h-3.5 mr-1" />,
          label: '403 Forbidden',
        };
      case 'UNAUTHORIZED':
        return {
          bg: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
          icon: <ShieldAlert className="w-3.5 h-3.5 mr-1" />,
          label: '401 Unauthorized',
        };
      case 'INVALID_URL':
        return {
          bg: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
          icon: <AlertCircle className="w-3.5 h-3.5 mr-1" />,
          label: 'Invalid URL / Blocked',
        };
      case 'PENDING':
        return {
          bg: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
          icon: <Clock className="w-3.5 h-3.5 mr-1 animate-spin" />,
          label: 'Pending Scan',
        };
      default:
        return {
          bg: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
          icon: <HelpCircle className="w-3.5 h-3.5 mr-1" />,
          label: status,
        };
    }
  };

  const { bg, icon, label } = getBadgeConfig();
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${bg} ${padding} transition-colors`}
    >
      {icon}
      {label}
    </span>
  );
};
