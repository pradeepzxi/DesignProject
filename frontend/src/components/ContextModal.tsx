import React, { useState } from 'react';
import {
  X,
  ExternalLink,
  RefreshCw,
  Tag,
  Compass,
  FileText,
  Globe,
  Terminal,
} from 'lucide-react';
import type { LinkItem } from '../types';
import { StatusBadge } from './StatusBadge';
import { api } from '../services/api';

interface ContextModalProps {
  link: LinkItem | null;
  onClose: () => void;
  onLinkUpdated?: (updatedLink: LinkItem) => void;
}

export const ContextModal: React.FC<ContextModalProps> = ({
  link,
  onClose,
  onLinkUpdated,
}) => {
  const [isValidating, setIsValidating] = useState(false);
  const [currentLink, setCurrentLink] = useState<LinkItem | null>(link);

  if (!currentLink) return null;

  const ctx = currentLink.context;

  const handleRevalidate = async () => {
    setIsValidating(true);
    try {
      const updated = await api.revalidateLink(currentLink.link_id);
      setCurrentLink(updated);
      if (onLinkUpdated) onLinkUpdated(updated);
    } catch (err) {
      alert(`Re-validation error: ${err}`);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-gray-900 border border-gray-700/80 rounded-2xl shadow-2xl p-6 sm:p-8">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-gray-800">
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <span className="text-xs uppercase tracking-wider font-semibold text-indigo-400">
                Link Context & Research Features
              </span>
              <StatusBadge status={currentLink.status} statusCode={currentLink.status_code} />
            </div>
            <h3 className="text-lg font-bold text-white break-all flex items-center gap-2">
              <a
                href={currentLink.original_url}
                target="_blank"
                rel="noreferrer"
                className="hover:text-indigo-300 transition-colors flex items-center gap-1.5"
              >
                {currentLink.original_url}
                <ExternalLink className="w-4 h-4 text-gray-500 hover:text-indigo-400" />
              </a>
            </h3>
            {currentLink.final_url && currentLink.final_url !== currentLink.original_url && (
              <p className="text-xs text-blue-400 mt-1 font-mono">
                ↳ Redirects to: {currentLink.final_url}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="mt-6 space-y-6">
          {/* Metadata Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-3.5">
              <div className="flex items-center space-x-2 text-gray-400 text-xs mb-1">
                <FileText className="w-3.5 h-3.5" />
                <span>Document Origin</span>
              </div>
              <p className="text-sm font-semibold text-white truncate" title={currentLink.document_title || currentLink.document_filename}>
                {currentLink.document_title || currentLink.document_filename || 'Unknown Document'}
              </p>
            </div>

            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-3.5">
              <div className="flex items-center space-x-2 text-gray-400 text-xs mb-1">
                <Compass className="w-3.5 h-3.5" />
                <span>Structural Location</span>
              </div>
              <p className="text-sm font-semibold text-indigo-300 truncate" title={currentLink.location_description}>
                {currentLink.location_description || 'Body Text'}
              </p>
            </div>

            <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-3.5">
              <div className="flex items-center space-x-2 text-gray-400 text-xs mb-1">
                <Globe className="w-3.5 h-3.5" />
                <span>Latency & Headers</span>
              </div>
              <p className="text-sm font-semibold text-white">
                {currentLink.response_time_ms ? `${currentLink.response_time_ms} ms` : 'N/A'}{' '}
                <span className="text-xs text-gray-400 font-normal">
                  ({currentLink.content_type || 'no content-type'})
                </span>
              </p>
            </div>
          </div>

          {/* Anchor and Section Heading */}
          <div className="bg-gray-800/30 border border-gray-800 rounded-xl p-4 space-y-4">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Anchor / Display Text
              </label>
              <div className="mt-1 font-medium text-emerald-400 bg-emerald-950/20 border border-emerald-800/30 rounded-lg px-3 py-2 text-sm">
                "{ctx?.anchor_text || 'No explicit anchor text'}"
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Enclosing Section Heading
              </label>
              <p className="mt-1 text-sm text-gray-200 font-medium">
                {ctx?.section_heading || 'General Document Section'}
              </p>
            </div>

            {/* Extracted Sentence */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Sentence Containing Link
              </label>
              <blockquote className="mt-1 text-sm text-gray-300 border-l-2 border-indigo-500 pl-3 italic bg-indigo-950/10 py-1.5 rounded-r">
                "{ctx?.surrounding_text || 'No surrounding sentence extracted'}"
              </blockquote>
            </div>

            {/* Surrounding Paragraph */}
            {ctx?.paragraph_text && (
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Full Paragraph Context
                </label>
                <div className="mt-1 text-xs text-gray-300 leading-relaxed bg-gray-900/60 p-3 rounded-lg border border-gray-800 max-h-32 overflow-y-auto">
                  {ctx.paragraph_text}
                </div>
              </div>
            )}
          </div>

          {/* Keywords & Tokens for Downstream Semantic Matching */}
          <div className="bg-gray-800/30 border border-gray-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
              <Tag className="w-3.5 h-3.5 text-indigo-400" />
              <span>Extracted Salient Domain Keywords</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {ctx?.keywords && ctx.keywords.length > 0 ? (
                ctx.keywords.map((kw, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-0.5 text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 rounded-md"
                  >
                    #{kw}
                  </span>
                ))
              ) : (
                <span className="text-xs text-gray-500">No domain keywords generated</span>
              )}
            </div>

            {/* URL Tokens Breakdown */}
            {ctx?.url_tokens && (
              <div className="mt-3 pt-3 border-t border-gray-800">
                <div className="flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
                  <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Syntactic URL Tokens</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono">
                  <div className="bg-gray-900/80 p-2 rounded border border-gray-800">
                    <span className="text-gray-500 block">Domain:</span>
                    <span className="text-white truncate block">{ctx.url_tokens.domain}</span>
                  </div>
                  <div className="bg-gray-900/80 p-2 rounded border border-gray-800">
                    <span className="text-gray-500 block">Filename:</span>
                    <span className="text-white truncate block">
                      {ctx.url_tokens.filename || '(root/none)'}
                    </span>
                  </div>
                  <div className="bg-gray-900/80 p-2 rounded border border-gray-800">
                    <span className="text-gray-500 block">Path Segments:</span>
                    <span className="text-indigo-400 truncate block">
                      {ctx.url_tokens.path_segments?.join(' / ') || '/'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {currentLink.error_message && (
            <div className="bg-rose-950/20 border border-rose-800/30 rounded-xl p-3.5 text-rose-300 text-xs">
              <span className="font-semibold block mb-0.5">Error Diagnostic:</span>
              {currentLink.error_message}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="mt-6 pt-4 border-t border-gray-800 flex items-center justify-between">
          <span className="text-xs text-gray-400">
            Last checked: {currentLink.last_checked ? new Date(currentLink.last_checked).toLocaleString() : 'Never'}
          </span>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleRevalidate}
              disabled={isValidating}
              className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-white border border-gray-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isValidating ? 'animate-spin' : ''}`} />
              <span>{isValidating ? 'Probing...' : 'Re-Validate Now'}</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
