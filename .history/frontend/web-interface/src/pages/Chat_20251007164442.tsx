/**
 * Chat/Conversation Page
 *
 * Main conversation interface with streaming responses
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ChatInterface from '../components/chat/ChatInterface';
import ConversationList from '../components/chat/ConversationList';
import { PanelLeftClose, PanelLeft } from 'lucide-react';

export default function Chat() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(
    conversationId
  );

  useEffect(() => {
    setCurrentConversationId(conversationId);
  }, [conversationId]);

  const handleConversationSelect = (id: string) => {
    setCurrentConversationId(id);
    navigate(`/chat/${id}`);
  };

  const handleNewConversation = () => {
    setCurrentConversationId(undefined);
    navigate('/chat');
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Sidebar */}
      <div
        className={`
          ${isSidebarOpen ? 'w-80' : 'w-0'} 
          transition-all duration-300 ease-in-out 
          border-r border-gray-200 dark:border-gray-700 
          bg-white dark:bg-gray-800
          overflow-hidden
        `}
      >
        <ConversationList
          selectedId={currentConversationId}
          onSelect={handleConversationSelect}
          onNew={handleNewConversation}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Toggle sidebar"
          >
            {isSidebarOpen ? (
              <PanelLeftClose className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            ) : (
              <PanelLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            )}
          </button>

          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            {currentConversationId ? 'Conversation' : 'New Conversation'}
          </h1>

          <div className="w-9" /> {/* Spacer for centering */}
        </div>

        {/* Chat Interface */}
        <div className="flex-1 overflow-hidden">
          <ChatInterface
            conversationId={currentConversationId}
            onConversationCreated={handleConversationSelect}
          />
        </div>
      </div>
    </div>
  );
}
