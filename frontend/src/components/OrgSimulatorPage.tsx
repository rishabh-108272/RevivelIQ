import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Activity, ShieldCheck, TrendingUp, Sliders, Play, BadgePercent, Heart } from 'lucide-react';
import { LoadingSpinner } from './LoadingState';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';

export const OrgSimulatorPage: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  const scenarios = [
    {
      id: 'support_time',
      title: 'Reduce support response time by 50%',
      description: 'Simulates faster ticket resolution times and communication SLAs portfolio-wide.',
      impactArea: 'Customer Success & Collaboration Index'
    },
    {
      id: 'resolve_high',
      title: 'Resolve all high priority tickets',
      description: 'Simulates clearing critical service roadblocks immediately across all accounts.',
      impactArea: 'Support Tickets Deficit & Sentiment'
    },
    {
      id: 'improve_renewal',
      title: 'Improve renewal conversion by 20%',
      description: 'Simulates deploying renegotiation offerings or rate discounts on imminent contracts.',
      impactArea: 'Agreement Expiration Renewal Risk'
    },
    {
      id: 'reduce_payment',
      title: 'Reduce payment delays by 30%',
      description: 'Simulates structuring proactive collections mediation plans on outstanding billing accounts.',
      impactArea: 'Overdue Invoices Delinquency'
    }
  ];

  const handleRunSimulation = async (scenarioId: string) => {
    setIsSimulating(true);
    setActiveScenario(scenarioId);
    setSimulationResult(null);
    try {
      const headers = getAuthHeaders();
      const res = await fetch('/api/simulations/organization', {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ scenario: scenarioId })
      });
      if (res.ok) {
        const data = await res.json();
        setSimulationResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Prepare simple visual data for chart
  const chartData = simulationResult ? [
    {
      name: 'Churn Reduction',
      Projected: Number(simulationResult.projected_churn_reduction.toFixed(1)),
      unit: '%'
    },
    {
      name: 'Health Improvement',
      Projected: Number(simulationResult.projected_health_score_improvement.toFixed(1)),
      unit: ' pts'
    }
  ] : [];

  return (
    <div className="p-8 space-y-8 flex-1 overflow-y-auto max-h-[calc(100vh-57px)] bg-[#faf9f8] dark:bg-[#11100f]">
      {/* Page Title */}
      <div className="border-b border-microsoft-border dark:border-zinc-800 pb-6">
        <h1 className="text-2xl font-bold dark:text-white flex items-center gap-2">
          <Activity className="w-6 h-6 text-microsoft-blue dark:text-blue-400" />
          <span>Organization Digital Twin Simulator</span>
        </h1>
        <p className="text-xs text-gray-500 dark:text-zinc-500 mt-2">
          Simulate strategic macro-operational adjustments portfolio-wide to project risk reduction rates and protected revenue.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        
        {/* Left Toggles Board */}
        <div className="lg:col-span-2 space-y-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300 flex items-center gap-2 px-1">
            <Sliders className="w-4 h-4 text-microsoft-blue" />
            <span>Operational Scenario Toggles</span>
          </h3>

          <div className="space-y-4">
            {scenarios.map((sc) => (
              <button
                key={sc.id}
                onClick={() => handleRunSimulation(sc.id)}
                disabled={isSimulating}
                className={`w-full text-left p-6 rounded-lg transition-all border shadow-sm hover:shadow-md flex flex-col justify-between items-start cursor-pointer ${
                  activeScenario === sc.id
                    ? 'bg-white dark:bg-[#201f1e] border-microsoft-blue border-l-4'
                    : 'bg-white hover:bg-gray-50 dark:bg-[#201f1e] dark:hover:bg-zinc-850 border-microsoft-border dark:border-zinc-800'
                }`}
              >
                <div className="flex justify-between items-start w-full">
                  <span className="font-bold text-xs text-microsoft-charcoal dark:text-white leading-snug">
                    {sc.title}
                  </span>
                  <div className="p-1 rounded-full bg-microsoft-lightBlue text-microsoft-blue dark:bg-blue-950/20 dark:text-blue-300 shrink-0">
                    <Play className="w-3 h-3 fill-current" />
                  </div>
                </div>
                <p className="text-[11px] text-gray-400 mt-2 leading-relaxed">
                  {sc.description}
                </p>
                <span className="inline-block mt-4 px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-blue-50 text-microsoft-blue dark:bg-blue-950/20 dark:text-blue-300">
                  Impact Layer: {sc.impactArea}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Right Output Projections Board */}
        <div className="lg:col-span-3 space-y-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300 flex items-center gap-2 px-1">
            <ShieldCheck className="w-4 h-4 text-risk-low" />
            <span>Projected Portfolio Metrics Lift</span>
          </h3>

          {isSimulating ? (
            <div className="glass-panel p-24 flex flex-col items-center justify-center space-y-4 min-h-[400px]">
              <LoadingSpinner />
              <p className="text-xs text-gray-400 font-semibold animate-pulse">Running Digital Twin calculations portfolio-wide...</p>
            </div>
          ) : simulationResult ? (
            <div className="space-y-6 animate-fade-in">
              {/* Projections KPI metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-panel p-6 border-l-4 border-l-risk-low flex flex-col justify-center shadow-sm">
                  <span className="text-[9px] font-bold uppercase tracking-wider text-gray-400">Churn Rate Drop</span>
                  <span className="text-2xl font-black text-risk-low mt-1">-{simulationResult.projected_churn_reduction}%</span>
                  <span className="text-[9px] text-gray-400 mt-1">Weighted drop rate</span>
                </div>
                
                <div className="glass-panel p-6 border-l-4 border-l-microsoft-blue flex flex-col justify-center shadow-sm">
                  <span className="text-[9px] font-bold uppercase tracking-wider text-gray-400">Revenue Protected</span>
                  <span className="text-2xl font-black text-microsoft-blue mt-1">${simulationResult.projected_revenue_protected.toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
                  <span className="text-[9px] text-gray-400 mt-1">Protected contract ACV</span>
                </div>

                <div className="glass-panel p-6 border-l-4 border-l-purple-500 flex flex-col justify-center shadow-sm">
                  <span className="text-[9px] font-bold uppercase tracking-wider text-gray-400">Health Index Boost</span>
                  <span className="text-2xl font-black text-purple-600 mt-1">+{simulationResult.projected_health_score_improvement.toFixed(1)}</span>
                  <span className="text-[9px] text-gray-400 mt-1">Average points gain</span>
                </div>
              </div>

              {/* Chart Visual delta */}
              <div className="glass-panel p-6">
                <div className="flex items-center gap-2 border-b border-microsoft-border dark:border-zinc-800 pb-4 mb-4">
                  <TrendingUp className="w-4 h-4 text-microsoft-blue" />
                  <h4 className="text-xs font-bold uppercase tracking-wider dark:text-white">Projections Comparison (Simulation Delta)</h4>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis dataKey="name" stroke="#888" tick={{ fontSize: 11 }} />
                      <YAxis stroke="#888" tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(value, name) => [`${value}`, 'Projected Delta']} />
                      <Legend />
                      <Bar dataKey="Projected" fill="#0078d4" radius={[4, 4, 0, 0]} barSize={50} name="Projected Improvement Delta" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Narrative explanation summary */}
              <div className="bg-[#faf9f8] dark:bg-zinc-900 border border-microsoft-border dark:border-zinc-800/80 p-6 rounded shadow-sm">
                <h4 className="text-xs font-bold uppercase tracking-wider text-microsoft-charcoal dark:text-white mb-2">Simulated Impact Assessment</h4>
                <p className="text-xs text-gray-500 dark:text-zinc-400 leading-relaxed">
                  {simulationResult.explanation}
                </p>
              </div>

            </div>
          ) : (
            <div className="glass-panel p-24 flex flex-col items-center justify-center text-center text-gray-400 dark:text-zinc-650 min-h-[400px] space-y-3">
              <BadgePercent className="w-12 h-12" />
              <p className="text-sm font-semibold">Ready to run portfolio twin simulation.</p>
              <p className="text-xs max-w-xs leading-normal">Select an operational scenario toggle from the left menu board to calculate delta risk projections.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
