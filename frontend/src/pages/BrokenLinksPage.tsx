import React, { useState, useEffect } from 'react';
import {
  ExternalLink,
  RefreshCw,
  Eye,
  Search,
  Compass,
} from 'lucide-react';
import { api } from '../services/api';
import type { LinkItem } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ContextModal } from '../components/ContextModal';

export const BrokenLinksPage: React.FC = () => {
  const [brokenLinks, setBrokenLinks] = useState<LinkItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedLinkForContext, setSelectedLinkForContext] = useState<LinkItem | null>(null);
  const [validatingLinkId, setValidatingLinkId] = useState<string | null>(null);

  const fetchBroken = async () => {
    setIsLoading(true);
    try {
      const data = await api.getLinks({ broken_only: true, limit: 300 });
      setBrokenLinks(data);
    } catch (err) {
      console.error('Failed to load broken links:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBroken();
  }, []);

  const handleRevalidate = async (linkId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setValidatingLinkId(linkId);
    try {
      const updated = await api.revalidateLink(linkId);
      if (updated.status === 'VALID' || updated.status === 'REDIRECT') {
        // Removed from broken list
        setBrokenLinks(brokenLinks.filter((l) => l.link_id !== linkId));
      } else {
        setBrokenLinks(brokenLinks.map((l) => (l.link_id === linkId ? updated : l)));
      }
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

  const filteredLinks = brokenLinks.filter(
    (l) =>
      l.original_url.toLowerCase().includes(search.toLowerCase()) ||
      (l.document_title && l.document_title.toLowerCase().includes(search.toLowerCase())) ||
      (l.context?.anchor_text && l.context.anchor_text.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-800">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Broken & Decayed Hyperlinks Queue
            </h1>
            <span className="px-2 py-0.5 text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-full">
              {brokenLinks.length} Active
            </span>
          </div>
          <p className="text-xs sm:text-sm text-gray-400 mt-1">
            Target queue for Prompt 2 autonomous candidate discovery, similarity ranking, and remediation.
          </p>
        </div>
        <button
          onClick={fetchBroken}
          className="self-start sm:self-auto p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors border border-gray-800"
          title="Refresh Queue"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 transform -translate-y-1/2" />
        <input
          type="text"
          placeholder="Filter by broken URL, anchor text, or document title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-900 border border-gray-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors"
        />
      </div>

      {/* Broken Links Table */}
      <div className="bg-gray-900/70 border border-gray-800 rounded-2xl overflow-hidden backdrop-blur-sm shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-800/50 text-[11px] uppercase tracking-wider text-gray-400 border-b border-gray-800 font-semibold">
              <tr>
                <th className="py-3 px-4">Broken Destination URL</th>
                <th className="py-3 px-4">Document Source</th>
                <th className="py-3 px-4">Failure Mode</th>
                <th className="py-3 px-4">Anchor / Display Text</th>
                <th className="py-3 px-4">Last Checked</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-mono">
              {filteredLinks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-500 font-sans">
                    {isLoading ? 'Scanning repository...' : 'No broken hyperlinks detected! All links healthy.'}
                  </td>
                </tr>
              ) : (
                filteredLinks.map((link) => {
                  const isValidating = validatingLinkId === link.link_id;
                  return (
                    <tr
                      key={link.link_id}
                      className="hover:bg-gray-800/40 transition-colors group cursor-pointer"
                      onClick={() => handleInspect(link)}
                    >
                      <td className="py-3.5 px-4 max-w-sm sm:max-w-md">
                        <div className="flex items-center space-x-2">
                          <a
                            href={link.original_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-rose-300 hover:text-rose-200 transition-colors truncate font-sans font-medium"
                            title={link.original_url}
                          >
                            {link.original_url}
                          </a>
                          <ExternalLink className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />
                        </div>
                        {link.error_message && (
                          <p className="text-[11px] text-gray-400 truncate mt-0.5 font-sans" title={link.error_message}>
                            Diagnostic: {link.error_message}
                          </p>
                        )}
                      </td>

                      <td className="py-3.5 px-4 font-sans text-gray-300 max-w-xs">
                        <p className="truncate font-medium text-gray-200">
                          {link.document_title || link.document_filename}
                        </p>
                        <p className="text-[10px] text-gray-500 truncate flex items-center gap-1 mt-0.5">
                          <Compass className="w-3 h-3" />
                          {link.location_description || 'Body text'}
                        </p>
                      </td>

                      <td className="py-3.5 px-4 whitespace-nowrap font-sans">
                        <StatusBadge status={link.status} statusCode={link.status_code} />
                      </td>

                      <td className="py-3.5 px-4 font-sans text-gray-300 max-w-xs">
                        <span className="font-medium text-emerald-400/90 truncate block" title={link.context?.anchor_text}>
                          "{link.context?.anchor_text || '(raw URL)'}"
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-gray-500 whitespace-nowrap font-sans text-[11px]">
                        {link.last_checked ? new Date(link.last_checked).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Never'}
                      </td>

                      <td className="py-3.5 px-4 text-right whitespace-nowrap font-sans">
                        <div className="flex items-center justify-end space-x-1.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleInspect(link);
                            }}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-medium text-indigo-300 bg-indigo-950/40 hover:bg-indigo-900/60 border border-indigo-800/40 transition-colors"
                            title="Inspect Context & Linguistic Features"
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
            if (updated.status === 'VALID' || updated.status === 'REDIRECT') {
              setBrokenLinks(brokenLinks.filter((l) => l.link_id !== updated.link_id));
              setSelectedLinkForContext(null);
            } else {
              setBrokenLinks(brokenLinks.map((l) => (l.link_id === updated.link_id ? updated : l)));
              setSelectedLinkForContext(updated);
            }
          }}
        />
      )}
    </div>
  );
};
