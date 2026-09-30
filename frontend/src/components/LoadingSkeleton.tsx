import React from 'react';

export const CardSkeleton: React.FC = () => {
  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-5 bg-white dark:bg-slate-900 shadow-card animate-pulse space-y-4">
      <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
      <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/2"></div>
      <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
    </div>
  );
};

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-4 bg-white dark:bg-slate-900 shadow-card animate-pulse space-y-4">
      <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/4 mb-6"></div>
      {Array.from({ length: rows }).map((_, idx) => (
        <div key={idx} className="flex gap-4 items-center">
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded flex-1"></div>
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded flex-1"></div>
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded flex-1"></div>
          <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-20"></div>
        </div>
      ))}
    </div>
  );
};

export const ChartSkeleton: React.FC = () => {
  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-lg p-6 bg-white dark:bg-slate-900 shadow-card animate-pulse flex flex-col justify-between h-80">
      <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/4"></div>
      <div className="flex-1 flex items-end gap-3 justify-center py-6">
        <div className="h-2/3 bg-slate-200 dark:bg-slate-800 rounded w-10"></div>
        <div className="h-4/5 bg-slate-200 dark:bg-slate-800 rounded w-10"></div>
        <div className="h-1/2 bg-slate-200 dark:bg-slate-800 rounded w-10"></div>
        <div className="h-3/4 bg-slate-200 dark:bg-slate-800 rounded w-10"></div>
        <div className="h-2/5 bg-slate-200 dark:bg-slate-800 rounded w-10"></div>
      </div>
      <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-1/2 mx-auto"></div>
    </div>
  );
};
