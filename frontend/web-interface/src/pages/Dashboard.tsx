/**
 * Dashboard — live knowledge-base stats and recent documents.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Layers, MessageSquare, Loader2 } from 'lucide-react';
import { api, type KnowledgeStats, type DocumentSummary } from '../lib/api-client';

export default function Dashboard() {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [s, d] = await Promise.all([api.getStats(), api.listDocuments()]);
        if (active) {
          setStats(s);
          setDocs(d);
        }
      } catch {
        if (active) {
          setStats({ document_count: 0, chunk_count: 0, conversation_count: 0 });
        }
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Welcome to your personal knowledge management system
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Documents"
          value={loading ? null : (stats?.document_count ?? 0)}
          icon={<FileText className="w-5 h-5" />}
        />
        <StatCard
          title="Indexed Chunks"
          value={loading ? null : (stats?.chunk_count ?? 0)}
          icon={<Layers className="w-5 h-5" />}
        />
        <StatCard
          title="Conversations"
          value={loading ? null : (stats?.conversation_count ?? 0)}
          icon={<MessageSquare className="w-5 h-5" />}
        />
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Recent Documents
        </h2>
        {loading ? (
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading…
          </div>
        ) : docs.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400">
            No documents yet.{' '}
            <Link to="/documents" className="text-primary-600 dark:text-primary-400 hover:underline">
              Upload your first document
            </Link>{' '}
            to get started!
          </p>
        ) : (
          <ul className="divide-y divide-gray-100 dark:divide-gray-700">
            {docs.slice(0, 8).map((doc) => (
              <li key={doc.document_id} className="flex items-center gap-3 py-3">
                <FileText className="w-5 h-5 text-primary-500 flex-shrink-0" />
                <span className="font-medium text-gray-900 dark:text-white truncate">
                  {doc.title}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400 ml-auto">
                  {doc.chunk_count} chunk{doc.chunk_count === 1 ? '' : 's'}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: number | null;
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-2">
        {icon}
        <h3 className="text-sm font-medium">{title}</h3>
      </div>
      <p className="text-3xl font-bold text-gray-900 dark:text-white">
        {value === null ? <Loader2 className="w-7 h-7 animate-spin text-primary-500" /> : value}
      </p>
    </div>
  );
}
