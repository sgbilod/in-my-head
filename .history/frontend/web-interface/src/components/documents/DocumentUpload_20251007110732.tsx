/**
 * Document Upload Component
 * 
 * Drag-and-drop file upload with progress tracking and collection assignment
 */

import { useState, useCallback, useRef } from 'react';
import { Upload, X, File, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocument } from '../../lib/api/endpoints/documents';
import type { Collection } from '../../types/api';

interface DocumentUploadProps {
  collections?: Collection[];
  onUploadComplete?: (documentId: string) => void;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
  documentId?: string;
}

export default function DocumentUpload({ 
  collections = [], 
  onUploadComplete 
}: DocumentUploadProps) {
  const [uploadingFiles, setUploadingFiles] = useState<Map<string, UploadingFile>>(
    new Map()
  );
  const [isDragging, setIsDragging] = useState(false);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, [selectedCollectionId]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleFiles(files);
    }
  }, [selectedCollectionId]);

  const handleFiles = async (files: File[]) => {
    for (const file of files) {
      const fileId = `${file.name}-${Date.now()}`;
      
      // Add to uploading state
      setUploadingFiles((prev) => {
        const newMap = new Map(prev);
        newMap.set(fileId, {
          file,
          progress: 0,
          status: 'uploading',
        });
        return newMap;
      });

      try {
        // Upload file with progress tracking
        const response = await uploadDocument(file, (progress) => {
          setUploadingFiles((prev) => {
            const newMap = new Map(prev);
            const existing = newMap.get(fileId);
            if (existing) {
              newMap.set(fileId, { ...existing, progress });
            }
            return newMap;
          });
        });

        // Mark as completed
        setUploadingFiles((prev) => {
          const newMap = new Map(prev);
          newMap.set(fileId, {
            file,
            progress: 100,
            status: 'completed',
            documentId: response.document_id,
          });
          return newMap;
        });

        // Notify parent
        if (onUploadComplete && response.document_id) {
          onUploadComplete(response.document_id);
        }

        // Remove from list after 3 seconds
        setTimeout(() => {
          setUploadingFiles((prev) => {
            const newMap = new Map(prev);
            newMap.delete(fileId);
            return newMap;
          });
        }, 3000);

      } catch (error) {
        // Mark as error
        setUploadingFiles((prev) => {
          const newMap = new Map(prev);
          newMap.set(fileId, {
            file,
            progress: 0,
            status: 'error',
            error: error instanceof Error ? error.message : 'Upload failed',
          });
          return newMap;
        });
      }
    }
  };

  const removeFile = (fileId: string) => {
    setUploadingFiles((prev) => {
      const newMap = new Map(prev);
      newMap.delete(fileId);
      return newMap;
    });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Collection Selector */}
      {collections.length > 0 && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Add to Collection (Optional)
          </label>
          <select
            value={selectedCollectionId}
            onChange={(e) => setSelectedCollectionId(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">No Collection</option>
            {collections.map((collection) => (
              <option key={collection.id} value={collection.id}>
                {collection.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-all duration-200
          ${
            isDragging
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-indigo-400 dark:hover:border-indigo-500'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.txt,.md,.py,.js,.ts,.jsx,.tsx"
        />

        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        
        <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {isDragging ? 'Drop files here' : 'Click to upload or drag and drop'}
        </p>
        
        <p className="text-sm text-gray-500 dark:text-gray-400">
          PDF, DOC, DOCX, TXT, MD, or code files up to 50MB
        </p>
      </div>

      {/* Uploading Files List */}
      {uploadingFiles.size > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            Uploading Files ({uploadingFiles.size})
          </h3>
          
          {Array.from(uploadingFiles.entries()).map(([fileId, fileData]) => (
            <div
              key={fileId}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-start space-x-3 flex-1 min-w-0">
                  {/* Icon based on status */}
                  {fileData.status === 'uploading' && (
                    <Loader2 className="h-5 w-5 text-indigo-500 animate-spin flex-shrink-0 mt-0.5" />
                  )}
                  {fileData.status === 'completed' && (
                    <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                  )}
                  {fileData.status === 'error' && (
                    <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  )}

                  {/* File info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {fileData.file.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {formatFileSize(fileData.file.size)}
                    </p>
                    {fileData.status === 'error' && fileData.error && (
                      <p className="text-xs text-red-500 mt-1">{fileData.error}</p>
                    )}
                  </div>
                </div>

                {/* Remove button */}
                <button
                  onClick={() => removeFile(fileId)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Progress bar */}
              {fileData.status === 'uploading' && (
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${fileData.progress}%` }}
                  />
                </div>
              )}

              {/* Status text */}
              {fileData.status === 'completed' && (
                <p className="text-xs text-green-600 dark:text-green-400">
                  Upload completed successfully
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
