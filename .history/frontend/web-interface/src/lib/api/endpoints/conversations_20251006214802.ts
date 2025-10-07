/**
 * Conversation API Endpoints
 * 
 * API functions for conversation management
 */

import apiClient from '../client';
import type { Conversation, Message, CreateConversationRequest, SendMessageRequest } from '../../types/api';

export const conversationApi = {
  /**
   * Create a new conversation
   */
  createConversation: async (data: CreateConversationRequest): Promise<Conversation> => {
    const response = await apiClient.post('/api/conversations', data);
    return response.data;
  },

  /**
   * Get all conversations
   */
  getConversations: async (params?: {
    limit?: number;
    offset?: number;
  }): Promise<Conversation[]> => {
    const response = await apiClient.get('/api/conversations', { params });
    return response.data;
  },

  /**
   * Get a specific conversation
   */
  getConversation: async (id: string): Promise<Conversation> => {
    const response = await apiClient.get(`/api/conversations/${id}`);
    return response.data;
  },

  /**
   * Delete a conversation
   */
  deleteConversation: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/conversations/${id}`);
  },

  /**
   * Get messages in a conversation
   */
  getMessages: async (
    conversationId: string,
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<Message[]> => {
    const response = await apiClient.get(
      `/api/conversations/${conversationId}/messages`,
      { params }
    );
    return response.data;
  },

  /**
   * Send a message in a conversation
   */
  sendMessage: async (
    conversationId: string,
    data: SendMessageRequest
  ): Promise<Message> => {
    const response = await apiClient.post(
      `/api/conversations/${conversationId}/messages`,
      data
    );
    return response.data;
  },

  /**
   * Stream a message response (Server-Sent Events)
   * Note: This returns an EventSource, not a Promise
   */
  streamMessage: (conversationId: string, query: string): EventSource => {
    const url = new URL(
      `/api/conversations/${conversationId}/stream`,
      import.meta.env.VITE_API_URL || 'http://localhost:8000'
    );
    url.searchParams.set('query', query);
    
    const token = localStorage.getItem('auth_token');
    if (token) {
      url.searchParams.set('token', token);
    }
    
    return new EventSource(url.toString());
  },
};
