/**
 * Chat — multi-turn RAG conversation against ingested documents.
 *
 * Answers stream token-by-token from /api/rag/query/stream (SSE); a semantic
 * cache hit arrives instantly as one chunk. Citations render after the answer.
 * History is kept client-side.
 */

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, FileText } from 'lucide-react';
import { ragQueryStream, type Citation } from '../lib/api-client';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  model?: string;
  error?: boolean;
  streaming?: boolean;
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async () => {
    const query = input.trim();
    if (!query || loading) return;

    setInput('');
    setLoading(true);
    // Add the user turn plus an empty assistant bubble to stream into.
    setMessages((m) => [
      ...m,
      { role: 'user', content: query },
      { role: 'assistant', content: '', citations: [], streaming: true },
    ]);

    // Patch the most recent assistant message immutably.
    const patchLast = (patch: Partial<ChatMessage>) =>
      setMessages((m) => {
        const copy = [...m];
        for (let i = copy.length - 1; i >= 0; i--) {
          if (copy[i].role === 'assistant') {
            copy[i] = { ...copy[i], ...patch };
            break;
          }
        }
        return copy;
      });

    let acc = '';
    await ragQueryStream(
      { query },
      {
        onChunk: (t) => {
          acc += t;
          patchLast({ content: acc });
        },
        onCitations: (c) => patchLast({ citations: c }),
        onDone: (cached) => {
          patchLast({ streaming: false, model: cached ? 'llama3 · cached' : 'llama3' });
          setLoading(false);
        },
        onError: (msg) => {
          patchLast({ content: `Error: ${msg}`, error: true, streaming: false });
          setLoading(false);
        },
      },
    );
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Chat</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Ask questions about your documents — answers are grounded in your knowledge base.
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 dark:text-gray-500 mt-16">
            <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Start a conversation. Try “What documents do I have?”</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}
            <div
              className={`max-w-2xl rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-primary-500 text-white'
                  : msg.error
                    ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow'
              }`}
            >
              {msg.role === 'assistant' && msg.streaming && !msg.content ? (
                <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
              ) : (
                <p className="whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                  {msg.streaming && (
                    <span className="inline-block w-1.5 h-4 ml-0.5 align-middle bg-primary-500 animate-pulse" />
                  )}
                </p>
              )}

              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                    Sources
                  </p>
                  {msg.citations.map((c, ci) => (
                    <div
                      key={ci}
                      className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300"
                    >
                      <FileText className="w-4 h-4 mt-0.5 flex-shrink-0 text-primary-500" />
                      <span>
                        <span className="font-medium">{c.document_title}</span>
                        {c.excerpt && (
                          <span className="text-gray-500 dark:text-gray-400">
                            {' '}
                            — {c.excerpt.slice(0, 100)}
                            {c.excerpt.length > 100 ? '…' : ''}
                          </span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {msg.model && (
                <p className="mt-2 text-xs text-gray-400 dark:text-gray-500">via {msg.model}</p>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
                <User className="w-5 h-5 text-gray-700 dark:text-gray-200" />
              </div>
            )}
          </div>
        ))}

        <div ref={endRef} />
      </div>

      {/* Composer */}
      <div className="flex gap-2 items-end pt-2 border-t border-gray-200 dark:border-gray-700">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          placeholder="Ask a question…"
          className="flex-1 resize-none px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-4 py-3 bg-primary-500 hover:bg-primary-600 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          aria-label="Send"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
