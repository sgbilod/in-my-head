/**
 * Message Component
 *
 * Displays individual chat messages with markdown rendering and citations
 */

import { Bot, User, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Message as MessageType } from '../../types/api';
import CitationCard from './CitationCard';

interface MessageProps {
  message: MessageType;
  isStreaming?: boolean;
}

export default function Message({ message, isStreaming = false }: MessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
    >
      <div className={`flex max-w-3xl space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
            isUser
              ? 'bg-indigo-600'
              : 'bg-gradient-to-br from-purple-500 to-indigo-600'
          }`}
        >
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <Bot className="w-5 h-5 text-white" />
          )}
        </div>

        {/* Message Content */}
        <div className="flex-1 space-y-2">
          <div
            className={`rounded-lg px-4 py-3 ${
              isUser
                ? 'bg-indigo-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
            }`}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap break-words">{message.content}</p>
            ) : (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                    a({ node, children, ...props }) {
                      return (
                        <a
                          {...props}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 dark:text-indigo-400 hover:underline inline-flex items-center gap-1"
                        >
                          {children}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      );
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
                
                {isStreaming && (
                  <span className="inline-block w-2 h-4 bg-indigo-600 animate-pulse ml-1" />
                )}
              </div>
            )}
          </div>

          {/* Citations */}
          {message.citations && message.citations.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                Sources ({message.citations.length})
              </p>
              <div className="grid gap-2">
                {message.citations.map((citation, index) => (
                  <CitationCard key={index} citation={citation} />
                ))}
              </div>
            </div>
          )}

          {/* Timestamp */}
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {new Date(message.created_at).toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
}
