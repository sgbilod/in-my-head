/**
 * Collections API Endpoints
 *
 * API functions for collection management
 */

import apiClient from '../client';
import type { Collection } from '../../../types/api';

export interface CreateCollectionRequest {
  name: string;
  description?: string;
}

export interface UpdateCollectionRequest {
  name?: string;
  description?: string;
}

export interface ListCollectionsParams {
  limit?: number;
  offset?: number;
  sort_by?: 'name' | 'created_at' | 'updated_at';
  sort_order?: 'asc' | 'desc';
}

export interface AddDocumentToCollectionRequest {
  document_id: string;
}

/**
 * Create a new collection
 */
export const createCollection = async (data: CreateCollectionRequest): Promise<Collection> => {
  const response = await apiClient.post('/api/collections', data);
  return response.data;
};

/**
 * Get all collections
 */
export const getCollections = async (params?: ListCollectionsParams): Promise<Collection[]> => {
  const response = await apiClient.get('/api/collections', { params });
  return response.data;
};

/**
 * Get a specific collection
 */
export const getCollection = async (id: string): Promise<Collection> => {
  const response = await apiClient.get(`/api/collections/${id}`);
  return response.data;
};

/**
 * Update a collection
 */
export const updateCollection = async (
  id: string,
  data: UpdateCollectionRequest
): Promise<Collection> => {
  const response = await apiClient.put(`/api/collections/${id}`, data);
  return response.data;
};

/**
 * Delete a collection
 */
export const deleteCollection = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/collections/${id}`);
};

/**
 * Add document to collection
 */
export const addDocumentToCollection = async (
  collectionId: string,
  documentId: string
): Promise<void> => {
  await apiClient.post(`/api/collections/${collectionId}/documents`, {
    document_id: documentId,
  });
};

/**
 * Remove document from collection
 */
export const removeDocumentFromCollection = async (
  collectionId: string,
  documentId: string
): Promise<void> => {
  await apiClient.delete(`/api/collections/${collectionId}/documents/${documentId}`);
};

/**
 * Get documents in a collection
 */
export const getCollectionDocuments = async (
  collectionId: string,
  params?: { limit?: number; offset?: number }
): Promise<any[]> => {
  const response = await apiClient.get(`/api/collections/${collectionId}/documents`, { params });
  return response.data;
};

// Legacy object export for backward compatibility
export const collectionsApi = {
  createCollection,
  getCollections,
  getCollection,
  updateCollection,
  deleteCollection,
  addDocumentToCollection,
  removeDocumentFromCollection,
  getCollectionDocuments,
};
