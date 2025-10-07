/**
 * CitationCard Component
 *
 * Displays document citations with excerpt and relevance score
 */

import { FileText, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface Citation {
  document_id: string;
  document_title: string;
  chunk_text: string;
  relevance_score: number;
}

interface CitationCardProps {
  citation: Citation;
}

export default function CitationCard({ citation }: CitationCardProps) {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/documents/${citation.document_id}`);
  };

  return (
    <button
      onClick={handleClick}
      className="w-full text-left p-3 bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-900 transition-colors group"
    >
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" />

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between mb-1">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate pr-2">
              {citation.document_title}
            </h4>
            <div className="flex items-center space-x-2 flex-shrink-0">
              {/* Relevance Score */}
              <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                {Math.round(citation.relevance_score * 100)}%
              </span>
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors" />
            </div>
          </div>

          {/* Excerpt */}
          <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
            {citation.chunk_text}
          </p>
        </div>
      </div>
    </button>
  );
}
