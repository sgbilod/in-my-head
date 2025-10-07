/**
 * Header Component
 *
 * Top header bar with title and user menu
 */

import { useLocation } from 'react-router-dom';
import { Bell, Moon, Sun } from 'lucide-react';
import { useState, useEffect } from 'react';

const pageNames: Record<string, string> = {
  '/conversations': 'Conversations',
  '/documents': 'Documents',
  '/collections': 'Collections',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
};

export default function Header() {
  const location = useLocation();
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Check for saved dark mode preference
    const isDark = localStorage.getItem('darkMode') === 'true';
    setDarkMode(isDark);
    if (isDark) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    localStorage.setItem('darkMode', String(newDarkMode));

    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const pageName = pageNames[location.pathname] || 'In My Head';

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
      {/* Page Title */}
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">{pageName}</h2>

      {/* Right Side Actions */}
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <button
          className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors relative"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          {/* Notification badge */}
          <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
        </button>

        {/* Dark Mode Toggle */}
        <button
          onClick={toggleDarkMode}
          className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          aria-label="Toggle Dark Mode"
        >
          {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
      </div>
    </header>
  );
}
