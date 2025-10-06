export interface Document {
  id: string;
  user_id: string;
  collection_id?: string;
  title: string;
  content: string;
  file_path: string;
  file_type: string;
  file_size_bytes: number;
  status: string;
  mime_type?: string;
  word_count?: number;
  page_count?: number;
  keywords?: string[];
  entities?: string[];
  topics?: string[];
  created_at: string;
  updated_at: string;
}

export interface Collection {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  is_default: boolean;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: string;
  user_id: string;
  name: string;
  color?: string;
  created_at: string;
}

export interface UploadDocumentRequest {
  file: File;
  collection_id?: string;
  tags?: string[];
}

export interface DocumentResponse {
  id: string;
  title: string;
  file_type: string;
  status: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
