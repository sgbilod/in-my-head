/**
 * Document Card Component
 * 
 * Individual document card with actions
 */

import { FileText, Trash2, Download, Calendar, FileType } from 'lucide-react';
import type { Document } from '../../types/api';

interface DocumentCardProps {
  document: Document;
  onDelete: (id: string) => void;
  onClick?: (document: Document) => void;
  isDeleting?: boolean;
}

export default function DocumentCard({ 
  document, 
  onDelete, 
  onClick,
  isDeleting = false
}: DocumentCardProps) {
  const getFileIcon = (fileType: string) => {
    // Return appropriate icon based on file type
    return <FileText className="h-8 w-8 text-indigo-600" />;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(date);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  return (
    <div
      onClick={() => onClick?.(document)}
      className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer group"
    >
      {/* Header with icon and actions */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-shrink-0">
          {getFileIcon(document.file_type)}
        </div>

        <div className="flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              // Download functionality
            }}
            className="p-1 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400"
            title="Download"
            aria-label="Download document"
          >
            <Download className="h-4 w-4" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(document.id);
            }}
            disabled={isDeleting}
            className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 disabled:opacity-50"
            title="Delete"
            aria-label="Delete document"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* File name */}
      <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2 truncate">
        {document.file_name}
      </h3>

      {/* Metadata */}
      <div className="space-y-2">
        <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
          <FileType className="h-3 w-3 mr-1" />
          <span className="uppercase">{document.file_type}</span>
          {document.file_size && (
            <>
              <span className="mx-2">•</span>
              <span>{formatFileSize(document.file_size)}</span>
            </>
          )}
        </div>

        <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
          <Calendar className="h-3 w-3 mr-1" />
          <span>{formatDate(document.created_at)}</span>
        </div>

        {/* Status badge */}
        <div className="flex items-center justify-between">
          <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
              document.status
            )}`}
          >
            {document.status}
          </span>

          {document.chunk_count && document.chunk_count > 0 && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {document.chunk_count} chunks
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
