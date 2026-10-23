import React from 'react';
import {
  LayoutDashboard,
  FileText,
  Link2,
  AlertTriangle,
  Upload,
  Layers,
  Sparkles,
  UserCheck,
  Wrench,
  FlaskConical,
  ShieldCheck,
} from 'lucide-react';

export type NavTab =
  | 'dashboard'
  | 'documents'
  | 'links'
  | 'broken-links'
  | 'recommendations'
  | 'review'
  | 'remediations'
  | 'experiments'
  | 'audit';

interface NavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  onOpenUpload: () => void;
  brokenCount?: number;
  reviewCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onOpenUpload,
  brokenCount = 0,
  reviewCount = 0,
}) => {
  const navItems: Array<{ id: NavTab; label: string; icon: any; badge?: number }> = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'links', label: 'Links', icon: Link2 },
    {
      id: 'broken-links',
      label: 'Broken',
      icon: AlertTriangle,
      badge: brokenCount > 0 ? brokenCount : undefined,
    },
    { id: 'recommendations', label: 'Candidates', icon: Sparkles },
    {
      id: 'review',
      label: 'Review Queue',
      icon: UserCheck,
      badge: reviewCount > 0 ? reviewCount : undefined,
    },
    { id: 'remediations', label: 'Remediations', icon: Wrench },
    { id: 'experiments', label: 'Experiments', icon: FlaskConical },
    { id: 'audit', label: 'Audit', icon: ShieldCheck },
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-gray-800 bg-[#0B0F19]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-emerald-400 p-0.5 shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-[#0B0F19] rounded-[10px] flex items-center justify-center">
                <Layers className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white tracking-tight text-base sm:text-lg">
                  LinkIntegrity<span className="text-indigo-400">.ai</span>
                </span>
                <span className="px-1.5 py-0.5 text-[10px] uppercase font-semibold tracking-wider bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/30">
                  Research Platform
                </span>
              </div>
              <p className="text-xs text-gray-400 hidden sm:block">
                Autonomous Remediation Framework
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-sm shadow-indigo-500/10'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                  {item.badge !== undefined && (
                    <span className="ml-1 px-1.5 py-0.2 text-[10px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Action / Upload Button */}
          <div className="flex items-center space-x-2">
            <button
              onClick={onOpenUpload}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-md shadow-indigo-600/25 transition-all transform active:scale-95"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Upload Document</span>
            </button>
          </div>
        </div>

        {/* Mobile/Compact Sub-navigation */}
        <div className="lg:hidden flex items-center space-x-1 overflow-x-auto py-2 border-t border-gray-800/60 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{item.label}</span>
                {item.badge !== undefined && (
                  <span className="ml-0.5 px-1 text-[9px] font-semibold bg-rose-500/20 text-rose-400 rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
