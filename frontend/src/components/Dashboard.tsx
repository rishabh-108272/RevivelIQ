import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { CardSkeleton, TableSkeleton, LoadingSpinner } from './LoadingState';
import { ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';
import { Download, Users, TrendingDown, DollarSign, Calendar, AlertCircle, FileText, ChevronRight } from 'lucide-react';

interface DashboardProps {
  onSelectCustomer: (id: number) => void;
  searchValue: string;
}

export const Dashboard: React.FC<DashboardProps> = ({ onSelectCustomer, searchValue }) => {
  const { getAuthHeaders } = useAuth();
  
  const [metrics, setMetrics] = useState<any>(null);
  const [customers, setCustomers] = useState<any[]>([]);
  const [briefing, setBriefing] = useState<any>(null);
  
  const [activeSubTab, setActiveSubTab] = useState<'portfolio' | 'briefing'>('portfolio');
  const [industryFilter, setIndustryFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isBriefingLoading, setIsBriefingLoading] = useState(true);

  // Fetch Dashboard Summary Metrics and Customers
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const headers = getAuthHeaders();
        
        // 1. Fetch metrics
        const metricsRes = await fetch('/api/analytics/dashboard', { headers });
        if (metricsRes.ok) {
          const metricsData = await metricsRes.json();
          setMetrics(metricsData);
        }
        
        // 2. Fetch customers
        let url = `/api/customers/?skip=0&limit=100`;
        if (searchValue) url += `&search=${encodeURIComponent(searchValue)}`;
        if (industryFilter) url += `&industry=${encodeURIComponent(industryFilter)}`;
        if (riskFilter) url += `&risk_level=${encodeURIComponent(riskFilter)}`;
        
        const custRes = await fetch(url, { headers });
        if (custRes.ok) {
          const custData = await custRes.json();
          setCustomers(custData);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [searchValue, industryFilter, riskFilter]);

  // Fetch Executive Briefing
  useEffect(() => {
    if (activeSubTab === 'briefing' && !briefing) {
      const fetchBriefing = async () => {
        setIsBriefingLoading(true);
        try {
          const headers = getAuthHeaders();
          const briefingRes = await fetch('/api/analytics/executive-briefing', { headers });
          if (briefingRes.ok) {
            const briefingData = await briefingRes.json();
            setBriefing(briefingData);
          }
        } catch (err) {
          console.error(err);
        } finally {
          setIsBriefingLoading(false);
        }
      };
      fetchBriefing();
    }
  }, [activeSubTab]);

  const handleExport = () => {
    // Open CSV export URL directly
    const token = localStorage.getItem('reviveiq_token') || '';
    window.open(`/api/customers/export?Authorization=Bearer ${token}`, '_blank');
  };

  if (isLoading && !metrics) {
    return (
      <div className="p-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => <CardSkeleton key={i} />)}
        </div>
        <TableSkeleton />
      </div>
    );
  }

  // Chart data formatting
  const pieData = metrics ? Object.entries(metrics.risk_distribution).map(([key, val]) => ({
    name: key,
    value: val as number
  })) : [];
  
  const COLORS = ['#e81123', '#ff8c00', '#107c41']; // Red, Orange, Green matching High, Medium, Low
  const pieColorsMap: Record<string, string> = {
    "High": '#e81123',
    "Medium": '#ff8c00',
    "Low": '#107c41'
  };

  return (
    <div className="p-8 space-y-8 flex-1 overflow-y-auto max-h-[calc(100vh-57px)]">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-microsoft-charcoal dark:text-white tracking-tight">Executive Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-zinc-400">Revenue risk protection and multi-agent customer insights control room.</p>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center space-x-2 px-4 py-2 rounded bg-white hover:bg-gray-50 dark:bg-zinc-800 dark:hover:bg-zinc-700/80 border border-microsoft-border dark:border-zinc-700 text-sm font-semibold shadow-sm transition-colors text-microsoft-charcoal dark:text-white cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Export Portfolio (CSV)</span>
        </button>
      </div>

      {/* KPI Indicators Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
        {/* KPI 1: Revenue at Risk */}
        <div data-tour="kpi-arr" className="glass-panel p-6 flex items-start justify-between">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-zinc-500">Revenue At Risk</span>
            <h2 className="text-2xl font-black text-risk-high">${metrics?.total_revenue_at_risk.toLocaleString('en-US', { minimumFractionDigits: 2 })}</h2>
            <p className="text-[11px] text-gray-500 dark:text-zinc-500">Projected annual contract value exposed to churn.</p>
          </div>
          <div className="p-3 bg-red-50 dark:bg-red-950/20 text-risk-high rounded">
            <DollarSign className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 2: Predicted Churn Accounts */}
        <div className="glass-panel p-6 flex items-start justify-between">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-zinc-500">Churn Risks</span>
            <h2 className="text-2xl font-black text-risk-high">{metrics?.predicted_churn_count} <span className="text-sm font-normal text-gray-500">Accounts</span></h2>
            <p className="text-[11px] text-gray-500 dark:text-zinc-500">Customers with churn probabilities exceeding 60%.</p>
          </div>
          <div className="p-3 bg-red-50 dark:bg-red-950/20 text-risk-high rounded">
            <TrendingDown className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 3: Upcoming Renewals */}
        <div className="glass-panel p-6 flex items-start justify-between">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-zinc-500">Expiring 60 Days</span>
            <h2 className="text-2xl font-black text-risk-medium">{metrics?.upcoming_renewals_count} <span className="text-sm font-normal text-gray-500">Contracts</span></h2>
            <p className="text-[11px] text-gray-500 dark:text-zinc-500">Agreements nearing expiration date deadlines.</p>
          </div>
          <div className="p-3 bg-orange-50 dark:bg-orange-950/20 text-risk-medium rounded">
            <Calendar className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 4: Overdue Invoices */}
        <div className="glass-panel p-6 flex items-start justify-between">
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-widest text-gray-400 dark:text-zinc-500">Overdue Payments</span>
            <h2 className="text-2xl font-black text-risk-medium">{metrics?.overdue_invoices_count} <span className="text-sm font-normal text-gray-500">Invoices</span></h2>
            <p className="text-[11px] text-gray-500 dark:text-zinc-500">Outstanding bills past active collection terms.</p>
          </div>
          <div className="p-3 bg-orange-50 dark:bg-orange-950/20 text-risk-medium rounded">
            <AlertCircle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart 1: Risk Level Distribution (Pie) */}
        <div className="glass-panel p-6 lg:col-span-1 flex flex-col justify-between min-h-[300px]">
          <div>
            <h3 className="font-bold text-sm uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300">Portfolio Risk Distribution</h3>
            <p className="text-xs text-gray-500 dark:text-zinc-500">Share of customers categorized by threat severity.</p>
          </div>
          <div className="h-48 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={pieColorsMap[entry.name] || '#ccc'} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-bold dark:text-white">{customers.length}</span>
              <span className="text-[9px] uppercase tracking-wider text-gray-400">Total Client Accounts</span>
            </div>
          </div>
          <div className="flex justify-center space-x-6 text-xs font-semibold">
            {pieData.map((entry, idx) => (
              <div key={entry.name} className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: pieColorsMap[entry.name] }}></span>
                <span className="dark:text-zinc-400">{entry.name} ({entry.value})</span>
              </div>
            ))}
          </div>
        </div>

        {/* Chart 2: Portfolio Health & Exposure Trend (Line) */}
        <div className="glass-panel p-6 lg:col-span-2 flex flex-col justify-between min-h-[300px]">
          <div>
            <h3 className="font-bold text-sm uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300">Customer Health & Exposure Trends</h3>
            <p className="text-xs text-gray-500 dark:text-zinc-500">Chronological monthly metrics tracking portfolio risk indicators.</p>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics?.health_trends || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edebe9" />
                <XAxis dataKey="month" stroke="#a19f9d" fontSize={11} tickLine={false} />
                <YAxis yAxisId="left" stroke="#107c41" fontSize={11} domain={[70, 100]} tickLine={false} label={{ value: 'Health Score (/100)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#107c41', fontWeight: 'bold' } }} />
                <YAxis yAxisId="right" orientation="right" stroke="#e81123" fontSize={11} tickLine={false} label={{ value: 'Revenue Exposure ($)', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#e81123', fontWeight: 'bold' } }} />
                <Tooltip />
                <Legend verticalAlign="top" height={36} />
                <Line yAxisId="left" type="monotone" dataKey="health_score" name="Avg Health" stroke="#107c41" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                <Line yAxisId="right" type="monotone" dataKey="revenue_at_risk" name="Revenue Exposure" stroke="#e81123" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Main Workspace Navigation: Portfolio Table vs Executive Briefing Narrative */}
      <div className="space-y-4">
        {/* Subtabs */}
        <div className="flex border-b border-microsoft-border dark:border-zinc-800">
          <button
            onClick={() => setActiveSubTab('portfolio')}
            className={`px-4 py-2 text-sm font-bold border-b-2 -mb-[2px] transition-all flex items-center space-x-2 ${
              activeSubTab === 'portfolio'
                ? 'border-microsoft-blue text-microsoft-blue dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-microsoft-charcoal dark:hover:text-white'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Active Risk Portfolios</span>
          </button>
          <button
            onClick={() => setActiveSubTab('briefing')}
            data-tour="executive-briefing"
            className={`px-4 py-2 text-sm font-bold border-b-2 -mb-[2px] transition-all flex items-center space-x-2 ${
              activeSubTab === 'briefing'
                ? 'border-microsoft-blue text-microsoft-blue dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-microsoft-charcoal dark:hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Executive Briefing Narrative</span>
          </button>
        </div>

        {/* View 1: Stressed Customers Portfolio List */}
        {activeSubTab === 'portfolio' && (
          <div data-tour="stressed-clients" className="glass-panel overflow-hidden">
            {/* Filter toolbars */}
            <div className="px-6 py-4 bg-[#faf9f8] dark:bg-zinc-900/40 border-b border-microsoft-border dark:border-zinc-800 flex flex-wrap gap-4 items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-zinc-500">Stressed Client Accounts ({customers.length})</span>
              <div className="flex space-x-3 text-xs">
                {/* Industry Filter dropdown */}
                <select
                  value={industryFilter}
                  onChange={(e) => setIndustryFilter(e.target.value)}
                  className="px-3 py-1.5 rounded bg-white dark:bg-zinc-800 border border-microsoft-border dark:border-zinc-700 text-microsoft-charcoal dark:text-white outline-none"
                >
                  <option value="">All Industries</option>
                  {INDUSTRIES_LIST.map(ind => <option key={ind} value={ind}>{ind}</option>)}
                </select>
                {/* Risk Level Filter dropdown */}
                <select
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                  className="px-3 py-1.5 rounded bg-white dark:bg-zinc-800 border border-microsoft-border dark:border-zinc-700 text-microsoft-charcoal dark:text-white outline-none"
                >
                  <option value="">All Risks</option>
                  <option value="High">High Risk</option>
                  <option value="Medium">Medium Risk</option>
                  <option value="Low">Low Risk</option>
                </select>
              </div>
            </div>

            {/* Customers Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-zinc-800/40 text-gray-400 dark:text-zinc-500 text-xs font-bold uppercase border-b border-microsoft-border dark:border-zinc-800">
                    <th className="px-6 py-3">Company Name</th>
                    <th className="px-6 py-3">Industry</th>
                    <th className="px-6 py-3">Annual Revenue</th>
                    <th className="px-6 py-3">Health Score</th>
                    <th className="px-6 py-3">Churn Prob</th>
                    <th className="px-6 py-3">Revenue Exposure</th>
                    <th className="px-6 py-3">Risk Level</th>
                    <th className="px-6 py-3 text-right">Outreach Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-microsoft-border dark:divide-zinc-800">
                  {customers.map((c) => {
                    const levelColors: Record<string, string> = {
                      "High": "bg-red-50 text-risk-high dark:bg-red-950/20",
                      "Medium": "bg-orange-50 text-risk-medium dark:bg-orange-950/20",
                      "Low": "bg-green-50 text-risk-low dark:bg-green-950/20"
                    };
                    return (
                      <tr key={c.id} className="hover:bg-gray-50/50 dark:hover:bg-zinc-850/40 transition-colors">
                        <td className="px-6 py-4 font-bold text-microsoft-charcoal dark:text-white">{c.name}</td>
                        <td className="px-6 py-4 text-gray-500 dark:text-zinc-400">{c.industry || 'Unknown'}</td>
                        <td className="px-6 py-4 font-semibold">${c.revenue.toLocaleString('en-US')}</td>
                        <td className="px-6 py-4 font-bold" style={{ color: c.health_score > 75 ? '#107c41' : (c.health_score > 50 ? '#ff8c00' : '#e81123') }}>
                          {round(c.health_score, 1)}
                        </td>
                        <td className="px-6 py-4 font-semibold">{round(c.churn_probability * 100, 0)}%</td>
                        <td className="px-6 py-4 font-bold text-risk-high">${c.revenue_at_risk.toLocaleString('en-US')}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${levelColors[c.risk_level] || 'bg-gray-100'}`}>
                            {c.risk_level}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => onSelectCustomer(c.id)}
                            className="inline-flex items-center space-x-1 text-xs font-bold text-microsoft-blue hover:text-microsoft-darkBlue dark:text-blue-400 dark:hover:text-blue-300 transition-colors cursor-pointer"
                          >
                            <span>Analyze Profile</span>
                            <ChevronRight className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  {customers.length === 0 && (
                    <tr>
                      <td colSpan={8} className="text-center py-12 text-gray-400 dark:text-zinc-500 font-semibold">
                        No customer accounts found matching current search/filters criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* View 2: Synthesized Narrative Executive Briefing */}
        {activeSubTab === 'briefing' && (
          <div className="glass-panel p-8 min-h-[400px]">
            {isBriefingLoading ? (
              <LoadingSpinner />
            ) : briefing ? (
              <div className="space-y-6">
                {/* Heading with date */}
                <div className="flex items-center justify-between border-b border-microsoft-border dark:border-zinc-800 pb-4">
                  <div>
                    <h2 className="text-xl font-bold dark:text-white">Synthesized C-Suite Narrative briefing</h2>
                    <p className="text-xs text-gray-500">Parsed: {new Date(briefing.generated_at).toLocaleString()}</p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-xs bg-green-50 text-risk-low font-bold">
                    PRE-CALCULATED BY EXECUTIVE AGENT
                  </span>
                </div>

                {/* Briefing text formatted inside structured markdown container */}
                <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed space-y-4 text-microsoft-charcoal dark:text-zinc-300">
                  {briefing.narrative.split('\n').map((line: string, idx: number) => {
                    if (line.startsWith('# ')) {
                      return <h1 key={idx} className="text-2xl font-black border-b border-transparent pb-1 dark:text-white">{line.replace('# ', '')}</h1>;
                    }
                    if (line.startsWith('## ')) {
                      return <h2 key={idx} className="text-lg font-bold text-microsoft-blue dark:text-blue-400 mt-6">{line.replace('## ', '')}</h2>;
                    }
                    if (line.startsWith('- ') || line.startsWith('* ')) {
                      return <li key={idx} className="list-disc ml-6">{line.substring(2)}</li>;
                    }
                    if (line.trim() === '') {
                      return <div key={idx} className="h-2" />;
                    }
                    // Handle bullet formatting
                    if (line.match(/^\d+\./)) {
                      return <div key={idx} className="font-semibold text-microsoft-charcoal dark:text-white pl-2 mt-2">{line}</div>;
                    }
                    if (line.startsWith('   - ')) {
                      return <div key={idx} className="pl-6 text-gray-500 dark:text-zinc-400 text-xs italic">{line.substring(5)}</div>;
                    }
                    return <p key={idx}>{line}</p>;
                  })}
                </div>
              </div>
            ) : (
              <p className="text-center text-gray-400 py-12">Failed to load briefing.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Utilities
const INDUSTRIES_LIST = ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Energy", "Logistics", "Media"];
const round = (num: number, decimals: number) => {
  return Number(Math.round(Number(num + 'e' + decimals)) + 'e-' + decimals).toFixed(decimals);
};
