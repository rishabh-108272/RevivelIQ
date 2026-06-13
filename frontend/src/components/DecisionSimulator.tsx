import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { X, Play, TrendingUp, Sparkles, AlertCircle } from 'lucide-react';

interface DecisionSimulatorProps {
  customerId: number;
  customerName: string;
  customerRevenue: number;
  onClose: () => void;
  onUpdateParent: () => void;
}

export const DecisionSimulator: React.FC<DecisionSimulatorProps> = ({ customerId, customerName, customerRevenue, onClose, onUpdateParent }) => {
  const { getAuthHeaders } = useAuth();
  
  const [resolveTickets, setResolveTickets] = useState(false);
  const [clearInvoices, setClearInvoices] = useState(false);
  const [applyDiscount, setApplyDiscount] = useState(false);
  const [discountPercent, setDiscountPercent] = useState(10);
  
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<any>(null);

  const handleRunSimulation = async () => {
    setIsSimulating(true);
    try {
      const headers = getAuthHeaders();
      const res = await fetch('/api/simulations/', {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer_id: customerId,
          query: `What if resolve_tickets=${resolveTickets}, clear_overdue_invoices=${clearInvoices}, apply_renewal_discount=${applyDiscount} (${discountPercent}%)?`,
          resolve_tickets: resolveTickets,
          clear_overdue_invoices: clearInvoices,
          apply_renewal_discount: applyDiscount,
          discount_percentage: applyDiscount ? discountPercent : 0.0
        })
      });
      
      if (res.ok) {
        const result = await res.json();
        setSimulationResult(result);
        onUpdateParent(); // Trigger refresh on details
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Compile Recharts side by side bars data
  const getChartData = () => {
    if (!simulationResult) return [];
    
    const orig = simulationResult.original_metrics_json;
    const sim = simulationResult.simulated_metrics_json;
    
    return [
      {
        metric: 'CS Health Score',
        Baseline: orig.health_score,
        Simulated: sim.health_score
      },
      {
        metric: 'Churn Prob %',
        Baseline: Math.round(orig.churn_probability * 100),
        Simulated: Math.round(sim.churn_probability * 100)
      }
    ];
  };

  const getRiskValueChartData = () => {
    if (!simulationResult) return [];
    const orig = simulationResult.original_metrics_json;
    const sim = simulationResult.simulated_metrics_json;
    return [
      {
        metric: 'Revenue at Risk ($)',
        Baseline: Math.round(orig.revenue_at_risk),
        Simulated: Math.round(sim.revenue_at_risk)
      }
    ];
  };

  return (
    <div className="absolute inset-0 z-50 overflow-hidden flex justify-end bg-black/40 backdrop-blur-sm">
      {/* Sliding Drawer Body */}
      <div className="w-full max-w-lg bg-white dark:bg-[#201f1e] h-full shadow-2xl flex flex-col border-l border-microsoft-border dark:border-zinc-800 animate-slide-in">
        
        {/* Drawer Header */}
        <div className="px-6 py-4 border-b border-microsoft-border dark:border-zinc-800 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-base dark:text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-microsoft-blue dark:text-blue-400" />
              <span>Decision Simulator</span>
            </h2>
            <p className="text-[11px] text-gray-500">{customerName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-850 text-gray-500 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Wrapper */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Controls Variables */}
          <div className="glass-panel p-5 bg-[#faf9f8] dark:bg-zinc-900/40 space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300">Modify Risk Variables</h3>
            
            <div className="space-y-3.5 text-xs">
              {/* Variable 1: support tickets */}
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={resolveTickets}
                  onChange={(e) => setResolveTickets(e.target.checked)}
                  className="mt-0.5 rounded text-microsoft-blue border-gray-300 focus:ring-microsoft-blue"
                />
                <div className="space-y-0.5">
                  <span className="font-semibold text-microsoft-charcoal dark:text-white">Resolve all open support tickets</span>
                  <p className="text-[10px] text-gray-400">Simulates resolving active blockers and boosting CSM sentiment score.</p>
                </div>
              </label>

              {/* Variable 2: clear invoices */}
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={clearInvoices}
                  onChange={(e) => setClearInvoices(e.target.checked)}
                  className="mt-0.5 rounded text-microsoft-blue border-gray-300 focus:ring-microsoft-blue"
                />
                <div className="space-y-0.5">
                  <span className="font-semibold text-microsoft-charcoal dark:text-white">Resolve overdue billing accounts</span>
                  <p className="text-[10px] text-gray-400">Simulates receiving past due receipts and clearing payment risk metrics.</p>
                </div>
              </label>

              {/* Variable 3: extension discount */}
              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={applyDiscount}
                  onChange={(e) => setApplyDiscount(e.target.checked)}
                  className="mt-0.5 rounded text-microsoft-blue border-gray-300 focus:ring-microsoft-blue"
                />
                <div className="space-y-0.5">
                  <span className="font-semibold text-microsoft-charcoal dark:text-white">Offer renewal contract rate discount</span>
                  <p className="text-[10px] text-gray-400">Simulates presenting price concessions to improve contract renewal risk.</p>
                </div>
              </label>

              {/* Discount percent slider */}
              {applyDiscount && (
                <div className="pl-6 space-y-1.5 animate-fade-in">
                  <div className="flex justify-between text-[11px] font-semibold text-gray-500">
                    <span>Discount Percentage:</span>
                    <span className="text-microsoft-blue font-bold">{discountPercent}%</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="30"
                    step="5"
                    value={discountPercent}
                    onChange={(e) => setDiscountPercent(parseInt(e.target.value))}
                    className="w-full accent-microsoft-blue"
                  />
                  <p className="text-[9px] text-gray-400 leading-normal">
                    Projected annual value adjustments: -${((customerRevenue * discountPercent) / 100).toLocaleString()} contract value.
                  </p>
                  {discountPercent > 20 && (
                    <div className="p-2 bg-red-50 dark:bg-red-950/20 text-risk-high rounded text-[10px] leading-normal font-semibold border border-red-200 dark:border-red-900/50 mt-1">
                      ⚠️ SafetyGuard Warning: Discounts above 20% require manual Board approval overrides.
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunSimulation}
              disabled={isSimulating}
              className="w-full flex items-center justify-center space-x-2 py-2 mt-4 rounded bg-microsoft-blue hover:bg-microsoft-darkBlue text-white text-xs font-bold disabled:opacity-50 transition-colors shadow-sm cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isSimulating ? 'Simulating Agent Recalculations...' : 'Execute Simulation Scenario'}</span>
            </button>
          </div>

          {/* Simulation Results Display Panel */}
          {simulationResult && (
            <div className="space-y-6 animate-fade-in">
              <div className="border-t border-microsoft-border dark:border-zinc-800 pt-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300 mb-3">Projected Metric Changes</h3>
                
                {/* Recharts Side-by-Side Bar Chart */}
                <div className="h-44 bg-gray-50 dark:bg-zinc-900/30 p-2 rounded border border-microsoft-border dark:border-zinc-850">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={getChartData()} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                      <XAxis dataKey="metric" stroke="#a19f9d" fontSize={10} tickLine={false} />
                      <YAxis stroke="#a19f9d" fontSize={10} domain={[0, 100]} tickLine={false} />
                      <Tooltip />
                      <Legend fontSize={9} iconSize={8} />
                      <Bar dataKey="Baseline" fill="#a19f9d" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="Simulated" fill="#0078d4" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="space-y-4">
                {/* Revenue impact chart */}
                <div className="h-32 bg-gray-50 dark:bg-zinc-900/30 p-2 rounded border border-microsoft-border dark:border-zinc-850">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={getRiskValueChartData()} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                      <XAxis dataKey="metric" stroke="#a19f9d" fontSize={10} tickLine={false} />
                      <YAxis stroke="#a19f9d" fontSize={10} tickLine={false} />
                      <Tooltip />
                      <Legend fontSize={9} iconSize={8} />
                      <Bar dataKey="Baseline" fill="#e81123" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="Simulated" fill="#107c41" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Narrative Summary explanation */}
                <div className="p-4 bg-blue-50/40 dark:bg-blue-950/10 border-l-4 border-microsoft-blue rounded flex items-start space-x-3 text-xs leading-relaxed text-microsoft-charcoal dark:text-zinc-300">
                  <Sparkles className="w-4 h-4 text-microsoft-blue mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="font-bold block mb-1">Decision Agent Impact Report:</span>
                    {simulationResult.explanation.split('\n').map((line: string, idx: number) => (
                      <p key={idx} className="mt-1">{line.replace('• ', '')}</p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {!simulationResult && !isSimulating && (
            <div className="flex flex-col items-center justify-center py-16 text-center text-gray-400 dark:text-zinc-500 space-y-2">
              <AlertCircle className="w-8 h-8" />
              <p className="text-xs font-semibold">No simulation metrics currently active.</p>
              <p className="text-[10px]">Select modifications above to simulate client recovery effects.</p>
            </div>
          )}

        </div>

      </div>
    </div>
  );
};
