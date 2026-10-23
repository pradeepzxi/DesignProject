import React, { useState, useEffect } from 'react';
import {
  Search,
  ExternalLink,
  RefreshCw,
  Eye,
  Compass,
} from 'lucide-react';
import { api } from '../services/api';
import type { LinkItem, DocumentItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ContextModal } from '../components/ContextModal';

interface LinksPageProps {
  selectedDocId?: string;
  onClearDocFilter?: () => void;
}

export const LinksPage: React.FC<LinksPageProps> = ({
  selectedDocId,
  onClearDocFilter,
}) => {
  const [links, setLinks] = useState<LinkItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [docFilter, setDocFilter] = useState<string>(selectedDocId || 'ALL');
  const [selectedLinkForContext, setSelectedLinkForContext] = useState<LinkItem | null>(null);
  const [validatingLinkId, setValidatingLinkId] = useState<string | null>(null);

  useEffect(() => {
    if (selectedDocId) {
      setDocFilter(selectedDocId);
    }
  }, [selectedDocId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [linksData, docsData] = await Promise.all([
        api.getLinks({
          document_id: docFilter !== 'ALL' ? docFilter : undefined,
          status: statusFilter !== 'ALL' ? statusFilter : undefined,
          search: search || undefined,
          limit: 300,
        }),
        api.getDocuments(),
      ]);
      setLinks(linksData);
      setDocuments(docsData);
    } catch (err) {
      console.error('Failed to load links:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [docFilter, statusFilter]);

  const handleRevalidate = async (linkId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setValidatingLinkId(linkId);
    try {
      const updated = await api.revalidateLink(linkId);
      setLinks(links.map((l) => (l.link_id === linkId ? updated : l)));
    } catch (err: any) {
      alert(`Re-validation error: ${err.message || err}`);
    } finally {
      setValidatingLinkId(null);
    }
  };

  const handleInspect = async (link: LinkItem) => {
    try {
      const detail = await api.getLinkById(link.link_id);
      setSelectedLinkForContext(detail);
    } catch {
      setSelectedLinkForContext(link);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-800">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">
            Repository Hyperlinks Explorer
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Examine URL normalization, response latency, HTTP headers, and deep linguistic context.
          </p>
        </div>
        <button
          onClick={loadData}
          className="self-start sm:self-auto p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors border border-gray-800"
          title="Refresh Table"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filter and Search Controls */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by URL or location description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </form>

        <div className="flex items-center space-x-2">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-gray-900 border border-gray-800 rounded-xl px-3 py-2 text-xs text-gray-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="VALID">Valid (200 OK)</option>
            <option value="REDIRECT">Redirects (3xx)</option>
            <option value="BROKEN_404">404 Not Found</option>
            <option value="BROKEN_4XX">Client Error (4xx)</option>
            <option value="SERVER_ERROR_5XX">Server Error (5xx)</option>
            <option value="TIMEOUT">Timeout</option>
            <option value="DNS_ERROR">DNS Error</option>
            <option value="FORBIDDEN">Forbidden (403)</option>
            <option value="UNAUTHORIZED">Unauthorized (401)</option>
          </select>

          {/* Document Filter */}
          <select
            value={docFilter}
            onChange={(e) => {
              setDocFilter(e.target.value);
              if (e.target.value === 'ALL' && onClearDocFilter) onClearDocFilter();
            }}
            className="bg-gray-900 border border-gray-800 rounded-xl px-3 py-2 text-xs text-gray-300 focus:outline-none focus:border-indigo-500 max-w-xs truncate"
          >
            <option value="ALL">All Documents</option>
            {documents.map((d) => (
              <option key={d.document_id} value={d.document_id}>
                {d.filename}
              </option>
            ))}
          </select>
        </div>
      </div>

      {docFilter !== 'ALL' && (
        <div className="flex items-center space-x-2 text-xs bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-3 py-1.5 rounded-lg w-fit">
          <span>Filtering by specific document</span>
          <button
            onClick={() => {
              setDocFilter('ALL');
              if (onClearDocFilter) onClearDocFilter();
            }}
            className="text-white hover:text-rose-400 font-bold ml-1"
          >
            × Clear
          </button>
        </div>
      )}

      {/* Links Table */}
      <div className="bg-gray-900/70 border border-gray-800 rounded-2xl overflow-hidden backdrop-blur-sm shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-800/50 text-[11px] uppercase tracking-wider text-gray-400 border-b border-gray-800 font-semibold">
              <tr>
                <th className="py-3 px-4">Hyperlink Target</th>
                <th className="py-3 px-4">Document & Origin</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">HTTP Code</th>
                <th className="py-3 px-4">Response Time</th>
                <th className="py-3 px-4">Last Checked</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-mono">
              {links.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-500 font-sans">
                    No links match the chosen filters.
                  </td>
                </tr>
              ) : (
                links.map((link) => {
                  const isValidating = validatingLinkId === link.link_id;
                  return (
                    <tr
                      key={link.link_id}
                      className="hover:bg-gray-800/40 transition-colors group cursor-pointer"
                      onClick={() => handleInspect(link)}
                    >
                      <td className="py-3 px-4 max-w-sm sm:max-w-md">
                        <div className="flex items-center space-x-2">
                          <a
                            href={link.original_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-white hover:text-indigo-400 transition-colors truncate font-sans font-medium"
                            title={link.original_url}
                          >
                            {link.original_url}
                          </a>
                          <ExternalLink className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
                        </div>
                        {link.final_url && link.final_url !== link.original_url && (
                          <p className="text-[10px] text-blue-400 truncate mt-0.5" title={link.final_url}>
                            ↳ {link.final_url}
                          </p>
                        )}
                      </td>

                      <td className="py-3 px-4 font-sans text-gray-300 max-w-xs">
                        <p className="truncate font-medium text-gray-200">
                          {link.document_title || link.document_filename}
                        </p>
                        <p className="text-[10px] text-gray-500 truncate flex items-center gap-1 mt-0.5">
                          <Compass className="w-3 h-3" />
                          {link.location_description || 'General text'}
                        </p>
                      </td>

                      <td className="py-3 px-4 whitespace-nowrap font-sans">
                        <StatusBadge status={link.status} statusCode={link.status_code} />
                      </td>

                      <td className="py-3 px-4 text-gray-300 font-mono">
                        {link.status_code ? (
                          <span className="font-semibold">{link.status_code}</span>
                        ) : (
                          <span className="text-gray-600">-</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-gray-400 whitespace-nowrap">
                        {link.response_time_ms ? `${link.response_time_ms} ms` : '-'}
                      </td>

                      <td className="py-3 px-4 text-gray-500 whitespace-nowrap font-sans text-[11px]">
                        {link.last_checked ? new Date(link.last_checked).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}
                      </td>

                      <td className="py-3 px-4 text-right whitespace-nowrap font-sans">
                        <div className="flex items-center justify-end space-x-1.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleInspect(link);
                            }}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 transition-colors"
                            title="Inspect Context"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Context</span>
                          </button>

                          <button
                            onClick={(e) => handleRevalidate(link.link_id, e)}
                            disabled={isValidating}
                            className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 transition-colors disabled:opacity-50"
                            title="Re-validate URL now"
                          >
                            <RefreshCw className={`w-3.5 h-3.5 ${isValidating ? 'animate-spin' : ''}`} />
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

      {/* Context Modal */}
      {selectedLinkForContext && (
        <ContextModal
          link={selectedLinkForContext}
          onClose={() => setSelectedLinkForContext(null)}
          onLinkUpdated={(updated) => {
            setLinks(links.map((l) => (l.link_id === updated.link_id ? updated : l)));
            setSelectedLinkForContext(updated);
          }}
        />
      )}
    </div>
  );
};
