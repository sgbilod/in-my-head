/**
 * Sidebar Component
 * 
 * Navigation sidebar with menu items and user profile
 */

import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  MessageSquare, 
  FileText, 
  FolderOpen, 
  BarChart3, 
  Settings,
  LogOut,
  Brain
} from 'lucide-react';

const navigation = [
  { name: 'Conversations', to: '/conversations', icon: MessageSquare },
  { name: 'Documents', to: '/documents', icon: FileText },
  { name: 'Collections', to: '/collections', icon: FolderOpen },
  { name: 'Analytics', to: '/analytics', icon: BarChart3 },
  { name: 'Settings', to: '/settings', icon: Settings },
];

export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200 dark:border-gray-700">
        <Brain className="h-8 w-8 text-indigo-600 mr-3" />
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          In My Head
        </h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                isActive
                  ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`
            }
          >
            <item.icon className="h-5 w-5 mr-3" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center mb-3">
          <div className="h-10 w-10 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
            <span className="text-indigo-600 dark:text-indigo-400 font-semibold text-sm">
              {user?.email?.[0].toUpperCase() || 'U'}
            </span>
          </div>
          <div className="ml-3 flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {user?.email || 'User'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Free Plan
            </p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </button>
      </div>
    </div>
  );
}
