import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import type { NavTab } from './components/Navbar';
import { UploadModal } from './components/UploadModal';
import { DashboardPage } from './pages/DashboardPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { LinksPage } from './pages/LinksPage';
import { BrokenLinksPage } from './pages/BrokenLinksPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { RemediationsPage } from './pages/RemediationsPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { AuditPage } from './pages/AuditPage';
import { api } from './services/api';
import type { DocumentItem } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('dashboard');
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | undefined>(undefined);
  const [brokenCount, setBrokenCount] = useState<number>(0);
  const [reviewCount, setReviewCount] = useState<number>(0);

  const fetchBadges = async () => {
    try {
      const [overview, revStats] = await Promise.all([
        api.getDashboardOverview().catch(() => null),
        api.getReviewStats().catch(() => ({ pending: 0 })),
      ]);
      if (overview) setBrokenCount(overview.broken_links);
      if (revStats) setReviewCount(revStats.pending);
    } catch {
      // Ignore if offline
    }
  };

  useEffect(() => {
    fetchBadges();
  }, [activeTab]);

  const handleDocumentSelectForLinks = (docId: string) => {
    setSelectedDocId(docId);
    setActiveTab('links');
  };

  const handleUploadSuccess = (_newDoc: DocumentItem) => {
    fetchBadges();
    setActiveTab('documents');
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          if (tab !== 'links') setSelectedDocId(undefined);
          setActiveTab(tab);
        }}
        onOpenUpload={() => setIsUploadOpen(true)}
        brokenCount={brokenCount}
        reviewCount={reviewCount}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <DashboardPage
            onNavigate={(tab) => setActiveTab(tab)}
            onOpenUpload={() => setIsUploadOpen(true)}
          />
        )}

        {activeTab === 'documents' && (
          <DocumentsPage
            onOpenUpload={() => setIsUploadOpen(true)}
            onSelectDocumentForLinks={handleDocumentSelectForLinks}
          />
        )}

        {activeTab === 'links' && (
          <LinksPage
            selectedDocId={selectedDocId}
            onClearDocFilter={() => setSelectedDocId(undefined)}
          />
        )}

        {activeTab === 'broken-links' && <BrokenLinksPage />}

        {activeTab === 'recommendations' && <RecommendationsPage />}

        {activeTab === 'review' && <ReviewQueuePage />}

        {activeTab === 'remediations' && <RemediationsPage />}

        {activeTab === 'experiments' && <ExperimentsPage />}

        {activeTab === 'audit' && <AuditPage />}
      </main>

      {/* Upload Document Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={handleUploadSuccess}
      />

      {/* Footer */}
      <footer className="border-t border-gray-800/80 bg-gray-950/60 py-6 text-xs text-gray-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-semibold text-gray-400">
              Intelligent Link Integrity Management Framework
            </span>{' '}
            • Autonomous Remediation & Governance (Design Project)
          </div>
          <div className="flex items-center space-x-4">
            <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              FastAPI + SQLite WAL Engine
            </span>
            <span className="text-gray-600">|</span>
            <span className="text-indigo-400 font-mono">Prompt 2 Research Suite Active</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
