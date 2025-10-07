/**
 * Document API Endpoints
 *
 * API functions for document management
 */

import apiClient from '../client';
import type { Document, UploadDocumentResponse } from '../../types/api';

export const documentApi = {
  /**
   * Upload a document
   */
  uploadDocument: async (
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<UploadDocumentResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  },

  /**
   * Get all documents
   */
  getDocuments: async (params?: {
    limit?: number;
    offset?: number;
    collection_id?: string;
  }): Promise<Document[]> => {
    const response = await apiClient.get('/api/documents', { params });
    return response.data;
  },

  /**
   * Get a specific document
   */
  getDocument: async (id: string): Promise<Document> => {
    const response = await apiClient.get(`/api/documents/${id}`);
    return response.data;
  },

  /**
   * Delete a document
   */
  deleteDocument: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/documents/${id}`);
  },

  /**
   * Get document chunks
   */
  getDocumentChunks: async (id: string): Promise<any[]> => {
    const response = await apiClient.get(`/api/documents/${id}/chunks`);
    return response.data;
  },
};
