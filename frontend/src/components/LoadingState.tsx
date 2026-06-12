import React from 'react';

export const CardSkeleton: React.FC = () => (
  <div className="glass-panel p-6 animate-pulse space-y-4">
    <div className="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-1/3"></div>
    <div className="h-8 bg-gray-300 dark:bg-zinc-700 rounded w-1/2"></div>
    <div className="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-5/6"></div>
  </div>
);

export const TableSkeleton: React.FC = () => (
  <div className="glass-panel p-6 animate-pulse space-y-4">
    <div className="h-5 bg-gray-300 dark:bg-zinc-700 rounded w-1/4"></div>
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((idx) => (
        <div key={idx} className="flex space-x-4">
          <div className="h-4 bg-gray-200 dark:bg-zinc-800 rounded flex-1"></div>
          <div className="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-1/6"></div>
        </div>
      ))}
    </div>
  </div>
);

export const LoadingSpinner: React.FC = () => (
  <div className="flex flex-col items-center justify-center space-y-3 py-12">
    <div className="w-10 h-10 border-4 border-microsoft-lightBlue border-t-microsoft-blue rounded-full animate-spin"></div>
    <p className="text-sm font-semibold text-gray-500 dark:text-zinc-400">Loading intelligence data...</p>
  </div>
);
