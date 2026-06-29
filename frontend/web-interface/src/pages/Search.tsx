/**
 * Search — semantic search over the knowledge base.
 *
 * Runs a RAG query (/api/rag/query) and shows the generated answer alongside
 * the source passages that grounded it.
 */

import { useState } from 'react';
import { Search as SearchIcon, FileText, Loader2 } from 'lucide-react';
import { api, type RagQueryResponse } from '../lib/api-client';

export default function Search() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<RagQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    const q = query.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.ragQuery({ query: q }));
    } catch (err) {
      const e = err as { data?: { detail?: string }; message?: string };
      setError(e?.data?.detail || e?.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Search</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Ask a question and get an answer grounded in your documents
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="max-w-2xl mx-auto">
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && run()}
              placeholder="Search for anything..."
              className="w-full pl-11 pr-28 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white text-lg"
            />
            <button
              onClick={run}
              disabled={loading || !query.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-primary-500 hover:bg-primary-600 disabled:opacity-40 text-white rounded-md font-medium transition-colors"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search'}
            </button>
          </div>
          {!result && !error && !loading && (
            <p className="text-gray-500 dark:text-gray-400 mt-4 text-center">
              Enter a question to search through your documents
            </p>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
              Answer
            </h2>
            <p className="text-gray-900 dark:text-white whitespace-pre-wrap leading-relaxed">
              {result.answer}
            </p>
            <p className="mt-3 text-xs text-gray-400 dark:text-gray-500">
              via {result.model} · {result.tokens_used} tokens
            </p>
          </div>

          {result.citations.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                Sources ({result.citations.length})
              </h2>
              <ul className="space-y-3">
                {result.citations.map((c, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <FileText className="w-5 h-5 mt-0.5 text-primary-500 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {c.document_title}
                      </p>
                      {c.excerpt && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                          {c.excerpt}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
