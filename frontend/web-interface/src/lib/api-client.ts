import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// ==================== Typed API ====================
// All paths are relative to baseURL '/api', which the Vite dev server proxies
// to the ai-engine (http://localhost:8001) with the '/api' prefix stripped.

export interface Citation {
  document_id: string;
  document_title: string;
  chunk_id: string;
  chunk_index: number;
  relevance_score: number;
  excerpt: string;
}

export interface RagQueryResponse {
  query: string;
  answer: string;
  citations: Citation[];
  context_used: string;
  model: string;
  tokens_used: number;
}

export interface DocumentSummary {
  document_id: string;
  title: string;
  chunk_count: number;
}

export interface IngestResponse {
  document_id: string;
  title: string;
  chunks_created: number;
  collection: string;
  embedding_dimension: number;
}

export interface KnowledgeStats {
  document_count: number;
  chunk_count: number;
  conversation_count: number;
}

export const api = {
  ragQuery: async (params: {
    query: string;
    model?: string;
    top_k?: number;
    max_tokens?: number;
    use_reranking?: boolean;
  }): Promise<RagQueryResponse> => {
    const res = await apiClient.post(
      '/rag/query',
      {
        query: params.query,
        model: params.model ?? 'llama3',
        top_k: params.top_k ?? 5,
        max_tokens: params.max_tokens ?? 400,
        use_reranking: params.use_reranking ?? true,
      },
      // Local LLM generation can be slow; allow up to 3 minutes.
      { timeout: 180000 }
    );
    return res.data;
  },

  listDocuments: async (): Promise<DocumentSummary[]> => {
    const res = await apiClient.get('/documents');
    return res.data;
  },

  getStats: async (): Promise<KnowledgeStats> => {
    const res = await apiClient.get('/documents/stats');
    return res.data;
  },

  uploadDocument: async (file: File, title?: string): Promise<IngestResponse> => {
    const form = new FormData();
    form.append('file', file);
    if (title) form.append('title', title);
    const res = await apiClient.post('/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  ingestText: async (content: string, title: string): Promise<IngestResponse> => {
    const res = await apiClient.post('/documents/ingest', { content, title });
    return res.data;
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/documents/${documentId}`);
  },
};
