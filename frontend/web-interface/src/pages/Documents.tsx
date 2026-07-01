/**
 * Documents — upload, list, and delete documents in the knowledge base.
 *
 * Uploads go to the ai-engine ingestion pipeline (/api/documents/upload):
 * the file is chunked, embedded locally, and stored in Qdrant, making it
 * immediately searchable from Search and Chat.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Upload, FileText, Trash2, Loader2, Sparkles } from 'lucide-react';
import { api, type DocumentSummary, type RelatedDocument } from '../lib/api-client';

interface RelatedState {
  open: boolean;
  loading: boolean;
  items: RelatedDocument[];
}

const ACCEPTED = '.txt,.md,.markdown,.csv,.json,.text';

export default function Documents() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [related, setRelated] = useState<Record<string, RelatedState>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const toggleRelated = async (id: string) => {
    const cur = related[id];
    if (cur?.open) {
      setRelated((r) => ({ ...r, [id]: { ...cur, open: false } }));
      return;
    }
    if (cur?.items) {
      setRelated((r) => ({ ...r, [id]: { ...cur, open: true } }));
      return;
    }
    setRelated((r) => ({ ...r, [id]: { open: true, loading: true, items: [] } }));
    try {
      const items = await api.getRelated(id, 4);
      setRelated((r) => ({ ...r, [id]: { open: true, loading: false, items } }));
    } catch {
      setRelated((r) => ({ ...r, [id]: { open: true, loading: false, items: [] } }));
    }
  };

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDocs(await api.listDocuments());
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        await api.uploadDocument(file, file.name);
      }
      await refresh();
    } catch (err) {
      setError(extractError(err));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteDocument(id);
      setDocs((d) => d.filter((doc) => doc.document_id !== id));
    } catch (err) {
      setError(extractError(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Documents</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Upload text and markdown files to your knowledge base
          </p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="px-4 py-2 bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
        >
          {uploading ? 'Uploading…' : 'Upload Document'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED}
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
          isDragging
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
            : 'border-gray-300 dark:border-gray-600'
        }`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
      >
        {uploading ? (
          <Loader2 className="w-12 h-12 mx-auto text-primary-500 mb-4 animate-spin" />
        ) : (
          <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        )}
        <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Drop files here to upload
        </p>
        <p className="text-gray-500 dark:text-gray-400">
          or click to browse — supports .txt, .md, .csv, .json
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Your Documents{docs.length > 0 && ` (${docs.length})`}
            </h2>
            <button
              onClick={refresh}
              className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading…
            </div>
          ) : docs.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400">
              No documents yet. Upload your first document to get started!
            </p>
          ) : (
            <ul className="divide-y divide-gray-100 dark:divide-gray-700">
              {docs.map((doc) => {
                const rel = related[doc.document_id];
                return (
                <li key={doc.document_id} className="py-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <FileText className="w-5 h-5 text-primary-500 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 dark:text-white truncate">
                          {doc.title}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {doc.chunk_count} chunk{doc.chunk_count === 1 ? '' : 's'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        onClick={() => toggleRelated(doc.document_id)}
                        className={`p-2 rounded-lg transition-colors ${
                          rel?.open
                            ? 'text-primary-600 bg-primary-50 dark:bg-primary-900/20'
                            : 'text-gray-400 hover:text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20'
                        }`}
                        title="Show related documents"
                        aria-label={`Related to ${doc.title}`}
                      >
                        <Sparkles className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.document_id)}
                        className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        aria-label={`Delete ${doc.title}`}
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>

                  {rel?.open && (
                    <div className="mt-2 ml-8 pl-4 border-l-2 border-primary-200 dark:border-primary-800">
                      {rel.loading ? (
                        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 py-1">
                          <Loader2 className="w-4 h-4 animate-spin" /> Finding related…
                        </div>
                      ) : rel.items.length === 0 ? (
                        <p className="text-sm text-gray-500 dark:text-gray-400 py-1">
                          No related documents found.
                        </p>
                      ) : (
                        <ul className="space-y-1 py-1">
                          <li className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide">
                            Related documents
                          </li>
                          {rel.items.map((r) => (
                            <li
                              key={r.document_id}
                              className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300"
                            >
                              <Sparkles className="w-3.5 h-3.5 text-primary-400 flex-shrink-0" />
                              <span className="truncate">{r.title}</span>
                              <span className="ml-auto text-xs text-gray-400 dark:text-gray-500">
                                {Math.max(0, r.score * 100).toFixed(0)}% match
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

function extractError(err: unknown): string {
  const e = err as { data?: { detail?: string }; message?: string };
  return e?.data?.detail || e?.message || 'Something went wrong';
}
