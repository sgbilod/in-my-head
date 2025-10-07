/**
 * Document List Component
 *
 * Display and manage uploaded documents
 */

import { useState, useEffect } from 'react';
import { FileText, Trash2, Download, Eye, Loader2 } from 'lucide-react';
import { getDocuments, deleteDocument } from '../../lib/api/endpoints/documents';
import type { Document } from '../../types/api';
import DocumentCard from './DocumentCard';

interface DocumentListProps {
  collectionId?: string;
  onDocumentClick?: (document: Document) => void;
  refreshTrigger?: number;
}

export default function DocumentList({
  collectionId,
  onDocumentClick,
  refreshTrigger = 0,
}: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, [collectionId, refreshTrigger]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {};
      if (collectionId) {
        params.collection_id = collectionId;
      }

      const response = await getDocuments(params);
      setDocuments(response.documents || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      setDeletingId(documentId);
      await deleteDocument(documentId);

      // Remove from list
      setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete document');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 dark:text-red-400">{error}</p>
        <button
          onClick={loadDocuments}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No documents yet</h3>
        <p className="text-gray-500 dark:text-gray-400">
          Upload your first document to get started
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Documents ({documents.length})
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map((document) => (
          <DocumentCard
            key={document.id}
            document={document}
            onDelete={handleDelete}
            onClick={onDocumentClick}
            isDeleting={deletingId === document.id}
          />
        ))}
      </div>
    </div>
  );
}
