import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Sun, Moon, LogOut, Search, Settings, Shield, HelpCircle } from 'lucide-react';

interface HeaderProps {
  onSearchChange: (val: string) => void;
  searchValue: string;
  onStartTour?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onSearchChange, searchValue, onStartTour }) => {
  const { user, logout } = useAuth();
  const [isDark, setIsDark] = React.useState(false);

  React.useEffect(() => {
    // Check initial dark mode state
    const isDarkClass = document.documentElement.classList.contains('dark');
    setIsDark(isDarkClass);
  }, []);

  const toggleDarkMode = () => {
    const root = document.documentElement;
    if (root.classList.contains('dark')) {
      root.classList.remove('dark');
      setIsDark(false);
      localStorage.setItem('theme', 'light');
    } else {
      root.classList.add('dark');
      setIsDark(true);
      localStorage.setItem('theme', 'dark');
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white dark:bg-[#201f1e] border-b border-microsoft-border dark:border-zinc-800 shadow-sm transition-colors duration-200 px-6 py-3 flex items-center justify-between">
      {/* Brand Logo & Extensibility Badge */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-8 h-8 rounded bg-microsoft-blue text-white font-black text-lg">
          R
        </div>
        <div>
          <span className="font-bold text-lg text-microsoft-charcoal dark:text-white tracking-tight">ReviveIQ</span>
          <span className="ml-2 px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wider bg-microsoft-lightBlue text-microsoft-blue dark:bg-microsoft-blue/20 dark:text-blue-300 border border-microsoft-blue/20">
            M365 COPILOT AGENT
          </span>
        </div>
      </div>

      {/* Global Context Search */}
      <div className="hidden md:flex items-center flex-1 max-w-md mx-8 relative">
        <Search className="absolute left-3 w-4 h-4 text-gray-400 dark:text-zinc-500" />
        <input
          type="text"
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Filter customers, contracts, or issues..."
          className="w-full pl-9 pr-4 py-1.5 text-sm rounded bg-gray-100 dark:bg-zinc-800 border border-transparent focus:border-microsoft-blue focus:bg-white dark:focus:bg-[#11100f] text-microsoft-charcoal dark:text-white outline-none transition-all duration-150"
        />
      </div>

      {/* Control Actions & User profile */}
      <div className="flex items-center space-x-4">
        {/* Help / Tour Guide Button */}
        {onStartTour && (
          <button
            onClick={onStartTour}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-microsoft-lightBlue hover:bg-microsoft-blue/20 dark:bg-microsoft-blue/15 dark:hover:bg-microsoft-blue/25 text-microsoft-blue dark:text-blue-400 text-xs font-bold transition-all cursor-pointer border border-microsoft-blue/10"
            title="Launch Interactive Tour Guide"
          >
            <HelpCircle className="w-4 h-4" />
            <span className="hidden sm:inline">Quick Tour</span>
          </button>
        )}

        {/* Light/Dark Toggle */}
        <button
          onClick={toggleDarkMode}
          className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-500 dark:text-zinc-400 transition-colors"
          title="Toggle Light/Dark Theme"
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* User Badging and actions */}
        {user && (
          <div className="flex items-center space-x-3 border-l border-microsoft-border dark:border-zinc-800 pl-4">
            <div className="flex flex-col items-end hidden sm:flex">
              <span className="text-sm font-semibold text-microsoft-charcoal dark:text-white leading-none">
                {user.fullName}
              </span>
              <span className="text-[10px] font-bold text-microsoft-blue dark:text-blue-400 uppercase tracking-widest mt-1 flex items-center gap-1">
                <Shield className="w-3 h-3" /> {user.role}
              </span>
            </div>
            
            <button
              onClick={logout}
              className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-950/20 text-red-500 transition-colors"
              title="Logout Account"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
