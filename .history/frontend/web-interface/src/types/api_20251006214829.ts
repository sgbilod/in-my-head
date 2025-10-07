/**
 * API Type Definitions
 * 
 * TypeScript interfaces for API requests and responses
 */

// ============= Conversation Types =============

export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  ai_model?: string;
  ai_provider?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  rag_context?: {
    chunks: Array<{
      chunk_id: string;
      document_id: string;
      content: string;
      score: number;
    }>;
  };
  citations?: {
    citations: Array<{
      document_id: string;
      document_title: string;
      chunk_id: string;
      relevance_score: number;
      excerpt: string;
    }>;
  };
  model?: string;
  tokens_used?: number;
  created_at: string;
}

export interface CreateConversationRequest {
  title: string;
  ai_model?: string;
  ai_provider?: string;
}

export interface SendMessageRequest {
  content: string;
  query?: string;
  use_rag?: boolean;
  top_k?: number;
  model?: string;
  temperature?: number;
}

// ============= Document Types =============

export interface Document {
  id: string;
  user_id: string;
  collection_id?: string;
  title: string;
  file_name: string;
  file_type: string;
  file_size: number;
  file_path: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count?: number;
  error_message?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface UploadDocumentResponse {
  document_id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  status: string;
  message: string;
}

// ============= Collection Types =============

export interface Collection {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateCollectionRequest {
  name: string;
  description?: string;
}

// ============= Search Types =============

export interface SearchRequest {
  query: string;
  top_k?: number;
  collection_id?: string;
  use_reranking?: boolean;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_title: string;
  content: string;
  score: number;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  processing_time: number;
}

// ============= Error Types =============

export interface APIError {
  message: string;
  status?: number;
  data?: any;
}

// ============= Auth Types =============

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  created_at: string;
}
