import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { TableSkeleton, LoadingSpinner } from './LoadingState';
import { DollarSign, CheckCircle, HelpCircle, User, ShieldAlert, Award } from 'lucide-react';

export const Recommendations: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  
  const [recs, setRecs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  const fetchRecommendations = async () => {
    setIsLoading(true);
    try {
      const headers = getAuthHeaders();
      const res = await fetch('/api/recommendations/', { headers });
      if (res.ok) {
        const data = await res.json();
        setRecs(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const handleUpdateStatus = async (recId: number, status: string) => {
    try {
      const headers = getAuthHeaders();
      const res = await fetch(`/api/recommendations/${recId}`, {
        method: 'PUT',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        // Optimistic update
        setRecs(prev => prev.map(r => r.id === recId ? { ...r, status } : r));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const getFilteredRecs = () => {
    return recs.filter(r => {
      const matchesAction = !actionFilter || r.action_type === actionFilter;
      const matchesPriority = !priorityFilter || r.priority === priorityFilter;
      return matchesAction && matchesPriority;
    });
  };

  if (isLoading && recs.length === 0) {
    return (
      <div className="p-8 space-y-6">
        <TableSkeleton />
      </div>
    );
  }

  const filtered = getFilteredRecs();
  const totalNetRecovery = filtered
    .filter(r => r.status === 'Approved' || r.status === 'Completed')
    .reduce((sum, r) => sum + r.net_recovery_value, 0);

  return (
    <div className="p-8 space-y-8 flex-1 overflow-y-auto max-h-[calc(100vh-57px)]">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-microsoft-border dark:border-zinc-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-microsoft-charcoal dark:text-white tracking-tight">Recovery Outreach Actions</h1>
          <p className="text-sm text-gray-500">AI-generated financial incentives, billing mitigations, and support escalations.</p>
        </div>

        {/* Aggregated Recovery Net */}
        <div className="glass-panel px-4 py-2 border-l-4 border-risk-low flex items-center space-x-3 bg-green-50/20">
          <Award className="w-5 h-5 text-risk-low" />
          <div className="flex flex-col">
            <span className="text-[9px] font-bold text-gray-400 uppercase tracking-wider">Secured Net Recovery</span>
            <span className="text-sm font-black text-risk-low">${totalNetRecovery.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Filter toolbar */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Outreach Actions List ({filtered.length})</span>
        <div className="flex space-x-3 text-xs">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="px-3 py-1.5 rounded bg-white dark:bg-zinc-800 border border-microsoft-border dark:border-zinc-700 text-microsoft-charcoal dark:text-white outline-none font-semibold"
          >
            <option value="">All Action Types</option>
            <option value="Discount">Rate Discounts</option>
            <option value="Priority Outreach">Billing Outreach</option>
            <option value="Support">Engineering Escalations</option>
            <option value="Review">QBR Reviews</option>
          </select>
          
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-3 py-1.5 rounded bg-white dark:bg-zinc-800 border border-microsoft-border dark:border-zinc-700 text-microsoft-charcoal dark:text-white outline-none font-semibold"
          >
            <option value="">All Priorities</option>
            <option value="High">High Priority</option>
            <option value="Medium">Medium Priority</option>
            <option value="Low">Low Priority</option>
          </select>
        </div>
      </div>

      {/* Recommendations Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((rec) => {
          const isPending = rec.status === 'Pending';
          const isApproved = rec.status === 'Approved';
          const isCompleted = rec.status === 'Completed';
          
          return (
            <div key={rec.id} className="glass-panel p-6 border-t-4 border-microsoft-blue flex flex-col justify-between space-y-4 hover:shadow-md transition-shadow">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-microsoft-charcoal dark:text-white leading-snug">{rec.title}</span>
                    <span className="text-[10px] text-gray-400 font-semibold block">{rec.customer_name}</span>
                  </div>
                  <span className={`text-[10px] font-bold uppercase ${rec.priority === 'High' ? 'text-risk-high' : 'text-risk-medium'}`}>
                    {rec.priority}
                  </span>
                </div>

                <p className="text-xs text-gray-500 dark:text-zinc-400 leading-normal">
                  {rec.description}
                </p>

                {/* Net Recovery Box */}
                <div className="bg-gray-50 dark:bg-zinc-900/40 p-3 rounded text-[11px] space-y-1 border border-microsoft-border dark:border-zinc-800/60">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Cost to execute:</span>
                    <span className="font-semibold text-risk-medium">${rec.cost_to_execute.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between font-bold">
                    <span className="text-gray-400">Net recovered:</span>
                    <span className="text-risk-low">${rec.net_recovery_value.toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Status Actions */}
              <div className="pt-2 flex items-center gap-2">
                {isPending && (
                  <>
                    <button
                      onClick={() => handleUpdateStatus(rec.id, 'Approved')}
                      className="flex-1 py-1.5 rounded text-xs font-bold bg-microsoft-blue hover:bg-microsoft-darkBlue text-white shadow-sm transition-colors cursor-pointer"
                    >
                      Approve Action
                    </button>
                    <button
                      onClick={() => handleUpdateStatus(rec.id, 'Rejected')}
                      className="px-3 py-1.5 rounded text-xs font-bold border border-microsoft-border hover:bg-gray-50 text-gray-500 dark:border-zinc-700 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
                    >
                      Dismiss
                    </button>
                  </>
                )}
                {isApproved && (
                  <button
                    onClick={() => handleUpdateStatus(rec.id, 'Completed')}
                    className="w-full py-1.5 rounded text-xs font-bold bg-green-50 text-risk-low border border-risk-low/30 hover:bg-green-100/40 dark:bg-green-950/20 dark:hover:bg-green-900/10 transition-all cursor-pointer"
                  >
                    Mark as Completed
                  </button>
                )}
                {isCompleted && (
                  <span className="w-full text-center py-1.5 text-xs font-bold text-gray-400 bg-gray-50 dark:bg-zinc-900/40 border border-transparent rounded cursor-default">
                    Outreach Successfully Completed
                  </span>
                )}
                {rec.status === 'Rejected' && (
                  <span className="w-full text-center py-1.5 text-xs font-bold text-red-400 bg-red-50/20 border border-transparent rounded cursor-default">
                    Recommendation Dismissed
                  </span>
                )}
              </div>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <div className="col-span-3 text-center py-16 text-gray-400 dark:text-zinc-500 font-semibold italic">
            No outreach tasks match current filters.
          </div>
        )}
      </div>
    </div>
  );
};
