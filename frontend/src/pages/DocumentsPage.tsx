import React, { useState, useEffect } from 'react';
import {
  FileText,
  FileCode,
  Play,
  Trash2,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from 'lucide-react';
import { api } from '../services/api';
import type { DocumentItem } from '../types';

interface DocumentsPageProps {
  onOpenUpload: () => void;
  onSelectDocumentForLinks: (docId: string) => void;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({
  onOpenUpload,
  onSelectDocumentForLinks,
}) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [scanningDocId, setScanningDocId] = useState<string | null>(null);

  const fetchDocs = async () => {
    setIsLoading(true);
    try {
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleScan = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setScanningDocId(docId);
    try {
      await api.scanDocument(docId);
      await fetchDocs();
    } catch (err: any) {
      alert(`Scanning failed: ${err.message || err}`);
    } finally {
      setScanningDocId(null);
    }
  };

  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this document and all its link records?')) {
      return;
    }
    try {
      await api.deleteDocument(docId);
      setDocuments(documents.filter((d) => d.document_id !== docId));
    } catch (err: any) {
      alert(`Delete failed: ${err.message || err}`);
    }
  };

  const filteredDocs = documents.filter(
    (d) =>
      d.filename.toLowerCase().includes(search.toLowerCase()) ||
      (d.document_title && d.document_title.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Enterprise Documents Repository
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Catalog of ingested PDF and DOCX documentation, parsing status, and validation runs.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDocs}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors border border-gray-800"
            title="Refresh List"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={onOpenUpload}
            className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            Upload Document
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center space-x-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by filename or title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-gray-900/70 border border-gray-800 rounded-2xl overflow-hidden backdrop-blur-sm shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-800/50 text-[11px] uppercase tracking-wider text-gray-400 border-b border-gray-800 font-semibold">
              <tr>
                <th className="py-3 px-4">Document Details</th>
                <th className="py-3 px-4">Format</th>
                <th className="py-3 px-4">Upload Date</th>
                <th className="py-3 px-4">Total Links</th>
                <th className="py-3 px-4">Integrity Breakdown</th>
                <th className="py-3 px-4">Last Scan</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60">
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-500">
                    No matching documents found.
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => {
                  const isPdf = doc.file_type.toLowerCase() === 'pdf';
                  const isScanning = scanningDocId === doc.document_id;

                  return (
                    <tr
                      key={doc.document_id}
                      className="hover:bg-gray-800/40 transition-colors cursor-pointer group"
                      onClick={() => onSelectDocumentForLinks(doc.document_id)}
                    >
                      <td className="py-3.5 px-4">
                        <div className="flex items-center space-x-3">
                          <div
                            className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                              isPdf
                                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                                : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                            }`}
                          >
                            {isPdf ? <FileText className="w-5 h-5" /> : <FileCode className="w-5 h-5" />}
                          </div>
                          <div className="min-w-0">
                            <p className="font-semibold text-white truncate max-w-xs sm:max-w-md group-hover:text-indigo-400 transition-colors">
                              {doc.document_title || doc.filename}
                            </p>
                            <p className="text-[11px] text-gray-500 font-mono truncate">{doc.filename}</p>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            isPdf
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          }`}
                        >
                          {doc.file_type.toUpperCase()}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-gray-400 whitespace-nowrap">
                        {new Date(doc.upload_timestamp).toLocaleDateString()}
                      </td>

                      <td className="py-3.5 px-4 font-semibold text-white whitespace-nowrap">
                        {doc.links_count} links
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          <span className="flex items-center text-emerald-400 font-medium text-xs">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                            {doc.valid_links_count}
                          </span>
                          <span className="text-gray-600">/</span>
                          <span className="flex items-center text-rose-400 font-medium text-xs">
                            <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                            {doc.broken_links_count}
                          </span>
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-gray-400 whitespace-nowrap">
                        {doc.last_scanned_at ? (
                          <span className="flex items-center space-x-1 text-gray-300">
                            <Clock className="w-3 h-3 text-gray-500" />
                            <span>{new Date(doc.last_scanned_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          </span>
                        ) : (
                          <span className="text-gray-500 italic">Not scanned</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={(e) => handleScan(doc.document_id, e)}
                            disabled={isScanning}
                            className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600 hover:text-white border border-indigo-500/30 transition-all disabled:opacity-50"
                            title="Run automated validation scan"
                          >
                            <Play className={`w-3 h-3 ${isScanning ? 'animate-spin' : ''}`} />
                            <span>{isScanning ? 'Scanning...' : 'Scan'}</span>
                          </button>

                          <button
                            onClick={(e) => handleDelete(doc.document_id, e)}
                            className="p-1.5 rounded-lg text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                            title="Delete Document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
