/**
 * ChatInterface Component
 *
 * Main chat interface with message list and input
 * Supports streaming responses and citations
 */

import { useState, useEffect, useRef, KeyboardEvent } from 'react';
import { Send, Loader2, AlertCircle } from 'lucide-react';
import Message from './Message';
import { sendMessage, getMessages, createConversation } from '../../lib/api/endpoints/conversations';
import type { Message as MessageType } from '../../types/api';

interface ChatInterfaceProps {
  conversationId?: string;
  onConversationCreated?: (id: string) => void;
}

export default function ChatInterface({
  conversationId,
  onConversationCreated,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingMessage, setStreamingMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationId) {
      loadMessages();
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const loadMessages = async () => {
    if (!conversationId) return;

    try {
      const data = await getMessages(conversationId);
      setMessages(data);
      setError(null);
    } catch (err) {
      setError('Failed to load messages');
      console.error('Error loading messages:', err);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setError(null);
    setIsLoading(true);

    try {
      // Create conversation if needed
      let currentConversationId = conversationId;
      if (!currentConversationId) {
        const conversation = await createConversation({
          title: userMessage.slice(0, 50),
        });
        currentConversationId = conversation.id;
        onConversationCreated?.(currentConversationId);
      }

      // Add user message to UI
      const userMsg: MessageType = {
        id: `temp-${Date.now()}`,
        conversation_id: currentConversationId,
        role: 'user',
        content: userMessage,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Send message and stream response
      setStreamingMessage('');

      // Use EventSource for streaming (Server-Sent Events)
      const eventSource = new EventSource(
        `/api/conversations/${currentConversationId}/stream?message=${encodeURIComponent(
          userMessage
        )}`
      );

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token') {
          // Stream token
          setStreamingMessage((prev) => prev + data.content);
        } else if (data.type === 'done') {
          // Streaming complete
          const assistantMsg: MessageType = {
            id: data.message_id,
            conversation_id: currentConversationId!,
            role: 'assistant',
            content: data.content,
            created_at: new Date().toISOString(),
            citations: data.citations,
          };
          setMessages((prev) => [...prev, assistantMsg]);
          setStreamingMessage('');
          eventSource.close();
          setIsLoading(false);
        }
      };

      eventSource.onerror = () => {
        setError('Streaming failed. Falling back to normal response.');
        eventSource.close();
        
        // Fallback to non-streaming
        sendMessage(currentConversationId!, { content: userMessage })
          .then((response) => {
            const assistantMsg: MessageType = {
              id: response.id,
              conversation_id: currentConversationId!,
              role: 'assistant',
              content: response.content,
              created_at: response.created_at,
              citations: response.citations,
            };
            setMessages((prev) => [...prev, assistantMsg]);
          })
          .catch((err) => {
            setError('Failed to send message');
            console.error('Error sending message:', err);
          })
          .finally(() => {
            setIsLoading(false);
            setStreamingMessage('');
          });
      };
    } catch (err) {
      setError('Failed to send message');
      console.error('Error:', err);
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {messages.length === 0 && !streamingMessage && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="max-w-md">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Start a Conversation
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Ask me anything about your documents. I'll search through your knowledge base
                and provide answers with citations.
              </p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}

        {/* Streaming message */}
        {streamingMessage && (
          <Message
            message={{
              id: 'streaming',
              conversation_id: conversationId || '',
              role: 'assistant',
              content: streamingMessage,
              created_at: new Date().toISOString(),
            }}
            isStreaming
          />
        )}

        {/* Loading indicator */}
        {isLoading && !streamingMessage && (
          <div className="flex items-center space-x-2 text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Thinking...</span>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="flex items-center space-x-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-sm text-red-700 dark:text-red-400">{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Container */}
      <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-4">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question... (Shift+Enter for new line)"
                rows={1}
                className="w-full px-4 py-3 pr-12 border border-gray-300 dark:border-gray-600 rounded-lg resize-none bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent max-h-40 overflow-y-auto"
                disabled={isLoading}
              />
              <div className="absolute bottom-3 right-3 text-xs text-gray-400">
                {input.length > 0 && `${input.length} chars`}
              </div>
            </div>

            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="flex items-center justify-center px-4 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Press Enter to send • Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  );
}
