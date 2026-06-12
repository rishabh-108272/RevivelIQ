import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Zap, ShieldAlert, DollarSign, ArrowUpDown, ExternalLink, Sparkles } from 'lucide-react';
import { LoadingSpinner } from './LoadingState';

interface WarRoomPageProps {
  onSelectCustomer: (id: number) => void;
}

export const WarRoomPage: React.FC<WarRoomPageProps> = ({ onSelectCustomer }) => {
  const { getAuthHeaders } = useAuth();
  const [threats, setThreats] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<string>('revenue_at_risk');

  const fetchThreats = async () => {
    setIsLoading(true);
    try {
      const headers = getAuthHeaders();
      const res = await fetch(`/api/analytics/war-room?sort_by=${sortBy}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setThreats(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchThreats();
  }, [sortBy]);

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#faf9f8] dark:bg-[#11100f] h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 flex-1 overflow-y-auto max-h-[calc(100vh-57px)] bg-[#faf9f8] dark:bg-[#11100f]">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-microsoft-border dark:border-zinc-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold dark:text-white flex items-center gap-2">
            <Zap className="w-6 h-6 text-microsoft-blue dark:text-blue-400 animate-pulse" />
            <span>Revenue War Room</span>
          </h1>
          <p className="text-xs text-gray-500 dark:text-zinc-500 mt-2">
            Prioritized tactical command center tracking the highest exposure revenue risks portfolio-wide.
          </p>
        </div>

        {/* Sorting Controls */}
        <div className="flex items-center space-x-3 bg-white dark:bg-[#201f1e] px-3 py-1.5 rounded border border-microsoft-border dark:border-zinc-800 shadow-sm text-xs font-semibold">
          <span className="text-gray-400 flex items-center gap-1">
            <ArrowUpDown className="w-3.5 h-3.5" /> Sort Threats By:
          </span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="border-none bg-transparent outline-none font-bold text-microsoft-charcoal dark:text-white cursor-pointer"
          >
            <option value="revenue_at_risk">Highest Business Impact (Revenue at Risk)</option>
            <option value="churn_probability">Vulnerability Rate (Churn Probability)</option>
            <option value="contract_value">Account Value (Contract ACV)</option>
          </select>
        </div>
      </div>

      {/* Threats Grid List */}
      <div className="space-y-6">
        {threats.map((t, idx) => {
          const riskColor = t.risk_level === 'High' ? 'text-risk-high border-risk-high/30 bg-red-50/30 dark:bg-red-950/10' : (t.risk_level === 'Medium' ? 'text-risk-medium border-risk-medium/30 bg-orange-50/30 dark:bg-orange-950/10' : 'text-risk-low border-risk-low/30 bg-green-50/30 dark:bg-green-950/10');
          
          return (
            <div key={t.id} className="glass-panel p-6 border-l-4 border-microsoft-blue hover:shadow-md transition-shadow relative overflow-hidden">
              {/* Index marker */}
              <div className="absolute right-0 top-0 w-12 h-12 bg-gray-50 dark:bg-zinc-900 border-l border-b border-microsoft-border dark:border-zinc-800 flex items-center justify-center font-black text-xs text-gray-400 select-none">
                #{idx + 1}
              </div>

              {/* Title row */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-microsoft-border dark:border-zinc-800/40 pb-4 mb-4">
                <div className="flex items-center space-x-3">
                  <h3 className="font-bold text-sm dark:text-white">{t.customer_name}</h3>
                  <span className="text-[10px] text-gray-400 italic">({t.industry || 'Unknown Sector'})</span>
                  <button
                    onClick={() => onSelectCustomer(t.id)}
                    className="p-1 rounded text-gray-400 hover:text-microsoft-blue dark:hover:text-blue-400 transition-colors"
                    title="View Detailed Customer Profile"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Score flags */}
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${riskColor}`}>
                    {t.risk_level} Risk ({t.risk_score}%)
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Financial KPI columns */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-[#faf9f8] dark:bg-zinc-900 border border-microsoft-border dark:border-zinc-800/60 p-3 rounded">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-gray-400 block">Exposed Revenue</span>
                    <span className="text-sm font-black text-risk-high">${t.revenue_at_risk.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="bg-[#faf9f8] dark:bg-zinc-900 border border-microsoft-border dark:border-zinc-800/60 p-3 rounded">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-gray-400 block">Total Contract Value</span>
                    <span className="text-sm font-bold text-microsoft-charcoal dark:text-white">${t.contract_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="bg-[#faf9f8] dark:bg-zinc-900 border border-microsoft-border dark:border-zinc-800/60 p-3 rounded col-span-2 border-l-4 border-l-risk-low">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-gray-400 block">Projected Recovery Value</span>
                    <span className="text-sm font-bold text-risk-low">${t.estimated_recovery_value.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>

                {/* Churn Reasons driver list */}
                <div className="space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1">
                    <ShieldAlert className="w-3.5 h-3.5" /> Core Churn Drivers
                  </span>
                  <div className="space-y-1.5 overflow-y-auto max-h-[85px] pr-2">
                    {t.key_reasons?.map((reason: string, rIdx: number) => (
                      <div key={rIdx} className="text-[11px] text-gray-500 dark:text-zinc-400 flex items-start space-x-1">
                        <span className="text-risk-high font-bold leading-none">•</span>
                        <span className="leading-snug">{reason}</span>
                      </div>
                    ))}
                    {(!t.key_reasons || t.key_reasons.length === 0) && (
                      <span className="text-gray-400 dark:text-zinc-500 text-[10px] italic">No active risk flags flagged.</span>
                    )}
                  </div>
                </div>

                {/* Recommended Outreach block */}
                <div className="space-y-2 bg-[#faf9f8]/40 dark:bg-zinc-900/20 p-4 rounded border border-microsoft-border dark:border-zinc-800 flex flex-col justify-between">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-microsoft-blue flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5" /> AI Recommended outreach
                    </span>
                    <p className="text-xs font-bold text-microsoft-charcoal dark:text-white leading-snug">
                      {t.recommended_action}
                    </p>
                  </div>

                  <button
                    onClick={() => onSelectCustomer(t.id)}
                    className="w-full mt-2 py-1.5 rounded bg-microsoft-blue hover:bg-microsoft-darkBlue text-white text-[10px] font-bold uppercase shadow-sm transition-all text-center cursor-pointer"
                  >
                    Deploy Escalation Outreach
                  </button>
                </div>
              </div>
            </div>
          );
        })}

        {threats.length === 0 && (
          <div className="text-center py-24 text-gray-400 dark:text-zinc-650 italic text-sm">
            No revenue threats found. Your active portfolio is fully optimized!
          </div>
        )}
      </div>
    </div>
  );
};
