import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Users, HeartHandshake, Bot, RotateCcw, AlertTriangle, ShieldAlert, Zap, Activity } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onReseed: () => void;
  isReseeding: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, onReseed, isReseeding }) => {
  const { user } = useAuth();
  
  const navItems = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: LayoutDashboard },
    { id: 'customers', label: 'Client Portfolio', icon: Users },
    { id: 'recommendations', label: 'Recovery Outreach', icon: HeartHandshake },
    { id: 'campaigns', label: 'Rescue Campaigns', icon: ShieldAlert },
    { id: 'war-room', label: 'Revenue War Room', icon: Zap },
    { id: 'org-simulator', label: 'Org Simulator', icon: Activity },
    { id: 'copilot', label: 'Copilot Extension', icon: Bot },
  ];

  return (
    <aside className="w-64 bg-white dark:bg-[#201f1e] border-r border-microsoft-border dark:border-zinc-800 transition-colors duration-200 flex flex-col justify-between h-[calc(100vh-57px)]">
      {/* Navigation Links */}
      <div className="py-6 px-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-semibold transition-all duration-150 ${
                isActive
                  ? 'bg-microsoft-lightBlue text-microsoft-blue dark:bg-microsoft-blue/10 dark:text-blue-400'
                  : 'text-gray-600 hover:bg-gray-100 dark:text-zinc-400 dark:hover:bg-zinc-800 hover:text-microsoft-charcoal dark:hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Admin Controls Panel */}
      {user?.role === 'Admin' && (
        <div className="p-4 border-t border-microsoft-border dark:border-zinc-800 bg-[#faf9f8] dark:bg-zinc-900/40 m-4 rounded-lg space-y-3">
          <div className="flex items-center space-x-2 text-risk-medium">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-[10px] font-bold tracking-widest uppercase">Admin Workspace</span>
          </div>
          <p className="text-[11px] text-gray-500 dark:text-zinc-500 leading-normal">
            Need to refresh the simulation environment? Reseed resets to 100 fresh synthetic accounts.
          </p>
          <button
            onClick={onReseed}
            disabled={isReseeding}
            className="w-full flex items-center justify-center space-x-2 px-3 py-1.5 text-xs font-semibold text-white bg-microsoft-blue hover:bg-microsoft-darkBlue rounded disabled:opacity-50 transition-colors cursor-pointer"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isReseeding ? 'animate-spin' : ''}`} />
            <span>{isReseeding ? 'Reseeding...' : 'Reseed Workspace'}</span>
          </button>
        </div>
      )}
    </aside>
  );
};
