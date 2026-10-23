import React, { useState, useRef } from 'react';
import { X, Upload, FileUp, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import type { DocumentItem } from '../types';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newDoc: DocumentItem) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      setError('Only PDF (.pdf) and Word (.docx) files are supported.');
      setSelectedFile(null);
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError('File size must not exceed 50 MB.');
      setSelectedFile(null);
      return;
    }
    setError(null);
    setSelectedFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const doc = await api.uploadDocument(selectedFile);
      onSuccess(doc);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="relative w-full max-w-lg bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl p-6 sm:p-8">
        <div className="flex items-center justify-between pb-4 border-b border-gray-800">
          <div>
            <h3 className="text-lg font-bold text-white">Ingest Enterprise Document</h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Upload PDF or DOCX for parsing, hyperlink extraction, and integrity analysis
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={handleChange}
          />

          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-gray-700 hover:border-gray-600 bg-gray-800/30'
            }`}
          >
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              <FileUp className="w-6 h-6" />
            </div>

            {selectedFile ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-white break-all">{selectedFile.name}</p>
                <p className="text-xs text-gray-400">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Ready to upload
                </p>
                <span className="inline-block mt-2 text-xs text-indigo-400 hover:underline">
                  Click to choose a different file
                </span>
              </div>
            ) : (
              <div>
                <p className="text-sm font-medium text-gray-200">
                  Drag and drop your document here, or <span className="text-indigo-400">browse</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">Supports PDF and Word DOCX (up to 50MB)</p>
              </div>
            )}
          </div>

          {error && (
            <div className="flex items-center space-x-2 p-3 text-xs bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!selectedFile || isUploading}
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 disabled:opacity-50 transition-all active:scale-95"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Ingesting & Parsing...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>Upload & Analyze</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
