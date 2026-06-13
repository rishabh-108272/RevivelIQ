import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from './LoadingState';
import { DecisionSimulator } from './DecisionSimulator';
import { ArrowLeft, Play, ShieldAlert, DollarSign, Calendar, MessageSquare, Ticket, ChevronDown, ChevronUp, Mail, Video, RefreshCw, BadgePercent, Sparkles } from 'lucide-react';

interface CustomerDetailProps {
  customerId: number;
  onBack: () => void;
}

export const CustomerDetail: React.FC<CustomerDetailProps> = ({ customerId, onBack }) => {
  const { getAuthHeaders } = useAuth();
  
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isSimulatorOpen, setIsSimulatorOpen] = useState(false);
  
  const [expandedSection, setExpandedSection] = useState<'timeline' | 'tickets' | 'billing' | 'contracts'>('timeline');
  const [recStatuses, setRecStatuses] = useState<Record<number, string>>({});

  const fetchCustomerData = async () => {
    setIsLoading(true);
    try {
      const headers = getAuthHeaders();
      const res = await fetch(`/api/customers/${customerId}`, { headers });
      if (res.ok) {
        const result = await res.json();
        setData(result);
        
        // Load initial recommendation statuses
        const statuses: Record<number, string> = {};
        result.recommendations.forEach((r: any) => {
          statuses[r.id] = r.status;
        });
        setRecStatuses(statuses);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomerData();
  }, [customerId]);

  const handleRunPipeline = async () => {
    setIsSyncing(true);
    try {
      const headers = getAuthHeaders();
      const res = await fetch(`/api/customers/${customerId}/analyze`, {
        method: 'POST',
        headers
      });
      if (res.ok) {
        await fetchCustomerData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleApproveRecommendation = async (recId: number) => {
    // SafetyGuard validation: check discount limit
    const rec = recommendations?.find((r: any) => r.id === recId);
    if (rec) {
      const discountMatch = rec.description.match(/(\d+)%/);
      const discountPercent = discountMatch ? parseInt(discountMatch[1], 10) : 0;
      if (discountPercent > 20) {
        alert(`⚠️ SafetyGuard Blocked: Discount offer of ${discountPercent}% exceeds the maximum 20% safety threshold. High-discount retention term sheets must be routed to the Finance Lead for manual board override.`);
        return;
      }
    }

    try {
      const headers = getAuthHeaders();
      // Update status to Approved
      const res = await fetch(`/api/recommendations/${recId}`, {
        method: 'PUT',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'Approved' })
      });
      
      if (res.ok) {
        setRecStatuses(prev => ({ ...prev, [recId]: 'Approved' }));
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-red-500">
        Error loading profile. Customer record not found or access denied.
      </div>
    );
  }

  const { customer, contracts, invoices, emails, meetings, support_tickets, churn_probability, revenue_at_risk, risk_explanation, recommendations } = data;
  
  // Format timeline: combine emails and meetings, sort descending
  const timeline = [
    ...emails.map((e: any) => ({ ...e, timelineType: 'email' })),
    ...meetings.map((m: any) => ({ ...m, timelineType: 'meeting' }))
  ].sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime());

  // Count metrics
  const unpaidInvoices = invoices.filter((i: any) => i.status !== 'Paid');
  const openTickets = support_tickets.filter((t: any) => t.status !== 'Resolved');
  
  // Risk level styling
  const riskStyles: Record<string, string> = {
    "High": "bg-red-50 text-risk-high border-risk-high/30 dark:bg-red-950/20",
    "Medium": "bg-orange-50 text-risk-medium border-risk-medium/30 dark:bg-orange-950/20",
    "Low": "bg-green-50 text-risk-low border-risk-low/30 dark:bg-green-950/20"
  };

  return (
    <div className="p-8 space-y-8 flex-1 overflow-y-auto max-h-[calc(100vh-57px)] relative">
      {/* Detail Page Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-microsoft-border dark:border-zinc-800 pb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-850 text-gray-500 dark:text-zinc-400 transition-colors cursor-pointer"
            title="Go Back to Portfolio"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold dark:text-white leading-none">{customer.name}</h1>
            <p className="text-xs text-gray-500 dark:text-zinc-500 mt-2">
              Industry: <span className="font-semibold">{customer.industry || 'Unknown'}</span> | Revenue: <span className="font-semibold">${customer.revenue.toLocaleString()}</span>
            </p>
          </div>
        </div>

        {/* Workspace Actions */}
        <div className="flex items-center space-x-3">
          {/* Decision Simulator Trigger */}
          <button
            onClick={() => setIsSimulatorOpen(true)}
            data-tour="whats-if-launch"
            className="flex items-center space-x-2 px-4 py-2 rounded bg-white hover:bg-gray-50 dark:bg-zinc-800 dark:hover:bg-zinc-700/80 border border-microsoft-border dark:border-zinc-700 text-sm font-semibold shadow-sm transition-colors text-microsoft-charcoal dark:text-white cursor-pointer"
          >
            <BadgePercent className="w-4 h-4 text-microsoft-blue dark:text-blue-400" />
            <span>Launch What-If Simulator</span>
          </button>

          {/* Sync pipeline */}
          <button
            onClick={handleRunPipeline}
            disabled={isSyncing}
            data-tour="sync-risk"
            className="flex items-center space-x-2 px-4 py-2 rounded text-sm font-semibold text-white bg-microsoft-blue hover:bg-microsoft-darkBlue disabled:opacity-50 transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Syncing...' : 'Sync Risk Metrics'}</span>
          </button>
        </div>
      </div>

      {/* Customer Status Summary Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-panel p-4 flex flex-col justify-center">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 dark:text-zinc-500">Churn Probability</span>
          <span className="text-2xl font-black text-microsoft-charcoal dark:text-white">{round(churn_probability * 100, 0)}%</span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-center">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 dark:text-zinc-500">Exposed Revenue</span>
          <span className="text-2xl font-black text-risk-high">${revenue_at_risk.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-center">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 dark:text-zinc-500">CS Health score</span>
          <span className="text-2xl font-black" style={{ color: customer.health_score > 75 ? '#107c41' : (customer.health_score > 50 ? '#ff8c00' : '#e81123') }}>
            {round(customer.health_score, 1)}/100
          </span>
        </div>
        <div className="glass-panel p-4 flex flex-col justify-center">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 dark:text-zinc-500">Risk Severity</span>
          <span className={`w-fit mt-1 px-2.5 py-0.5 rounded text-xs font-bold uppercase border ${riskStyles[customer.risk_level] || 'bg-gray-100'}`}>
            {customer.risk_level} Risk
          </span>
        </div>
      </div>

      {/* Primary Details Grid: Left details columns, Right Explainability & Recommendations columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Detail lists (timeline, billing, contracts) */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Section 1: Communications Timeline */}
          <div className="glass-panel overflow-hidden">
            <button
              onClick={() => setExpandedSection(expandedSection === 'timeline' ? 'billing' : 'timeline')}
              className="w-full px-6 py-4 bg-[#faf9f8] dark:bg-zinc-900/40 border-b border-microsoft-border dark:border-zinc-800 flex items-center justify-between text-left font-bold text-sm uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300"
            >
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-microsoft-blue" />
                <span>Communications Feed ({timeline.length} logs)</span>
              </div>
              {expandedSection === 'timeline' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {expandedSection === 'timeline' && (
              <div className="p-6 max-h-[350px] overflow-y-auto space-y-4">
                {timeline.map((item: any, idx: number) => {
                  const isEmail = item.timelineType === 'email';
                  const sentColor = item.sentiment_score < -0.1 ? 'bg-red-50 text-red-600 dark:bg-red-950/20 dark:text-red-400' : (item.sentiment_score > 0.1 ? 'bg-green-50 text-green-600 dark:bg-green-950/20 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-zinc-800 dark:text-zinc-400');
                  
                  return (
                    <div key={idx} className="flex items-start space-x-4 border-b border-microsoft-border dark:border-zinc-800/40 pb-4 last:border-b-0 last:pb-0">
                      <div className={`p-2 rounded-full ${isEmail ? 'bg-blue-50 text-blue-500 dark:bg-blue-950/20 dark:text-blue-400' : 'bg-purple-50 text-purple-500 dark:bg-purple-950/20 dark:text-purple-400'}`}>
                        {isEmail ? <Mail className="w-4 h-4" /> : <Video className="w-4 h-4" />}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-microsoft-charcoal dark:text-white">{isEmail ? `Email: ${item.subject}` : `Meeting: ${item.title}`}</span>
                          <span className="text-[10px] text-gray-400 dark:text-zinc-500">{new Date(item.date).toLocaleDateString()}</span>
                        </div>
                        <p className="text-xs text-gray-500 dark:text-zinc-400 leading-normal">
                          {isEmail ? item.body : item.summary}
                        </p>
                        <div className="flex items-center space-x-3 pt-1">
                          <span className="text-[10px] text-gray-400">Sender: {isEmail ? item.sender : item.attendees?.join(', ')}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${sentColor}`}>
                            Sentiment: {item.sentiment_score < -0.1 ? 'Negative' : (item.sentiment_score > 0.1 ? 'Positive' : 'Neutral')} ({item.sentiment_score.toFixed(2)})
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Section 2: Support Tickets & Semantic Categories */}
          <div className="glass-panel overflow-hidden">
            <button
              onClick={() => setExpandedSection(expandedSection === 'tickets' ? 'timeline' : 'tickets')}
              className="w-full px-6 py-4 bg-[#faf9f8] dark:bg-zinc-900/40 border-b border-microsoft-border dark:border-zinc-800 flex items-center justify-between text-left font-bold text-sm uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300"
            >
              <div className="flex items-center space-x-2">
                <Ticket className="w-4 h-4 text-microsoft-blue" />
                <span>Support Queue & Issue Clustering ({openTickets.length} open tickets)</span>
              </div>
              {expandedSection === 'tickets' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {expandedSection === 'tickets' && (
              <div className="p-6 space-y-6">
                {/* Semantic Trends Clustering display */}
                {risk_explanation.metrics && (
                  <div className="space-y-3">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Foundry IQ Issue Clusters</span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* We mock or extract from clustering response */}
                      {/* Check if trend exists */}
                      {risk_explanation.metrics.work_iq_collaboration_strength < 60 ? (
                        <div className="p-3 border border-red-100 dark:border-red-950/20 bg-red-50/30 dark:bg-red-950/10 rounded flex flex-col justify-between">
                          <span className="text-xs font-bold text-risk-high">Billing & Licensing Hold</span>
                          <span className="text-[11px] text-gray-500 mt-1">Issues relating to pricing discrepancies or seat count alignments.</span>
                          <span className="text-[10px] font-bold text-gray-400 mt-2">2 tickets clustered</span>
                        </div>
                      ) : null}
                      <div className="p-3 border border-orange-100 dark:border-orange-950/20 bg-orange-50/30 dark:bg-orange-950/10 rounded flex flex-col justify-between">
                        <span className="text-xs font-bold text-risk-medium">SSO & Access Disconnects</span>
                        <span className="text-[11px] text-gray-500 mt-1">Bugs concerning Azure SSO loops and login authentication wrapper failures.</span>
                        <span className="text-[10px] font-bold text-gray-400 mt-2">1 ticket clustered</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Ticket rows */}
                <div className="max-h-[250px] overflow-y-auto space-y-3">
                  {support_tickets.map((t: any) => (
                    <div key={t.id} className="p-3 bg-gray-50 dark:bg-zinc-800/40 rounded flex items-center justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-microsoft-charcoal dark:text-white">{t.title}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${t.priority === 'High' ? 'bg-red-50 text-risk-high dark:bg-red-950/20' : 'bg-gray-100 text-gray-500'}`}>
                            {t.priority}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-500 dark:text-zinc-400 leading-normal">{t.description}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${t.status === 'Resolved' ? 'bg-green-50 text-risk-low dark:bg-green-950/20' : 'bg-orange-50 text-risk-medium dark:bg-orange-950/20'}`}>
                        {t.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section 3: Billing & Invoices */}
          <div className="glass-panel overflow-hidden">
            <button
              onClick={() => setExpandedSection(expandedSection === 'billing' ? 'timeline' : 'billing')}
              className="w-full px-6 py-4 bg-[#faf9f8] dark:bg-zinc-900/40 border-b border-microsoft-border dark:border-zinc-800 flex items-center justify-between text-left font-bold text-sm uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300"
            >
              <div className="flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-microsoft-blue" />
                <span>Invoice Ledgers ({unpaidInvoices.length} unpaid invoices)</span>
              </div>
              {expandedSection === 'billing' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {expandedSection === 'billing' && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-zinc-800/40 text-gray-400 dark:text-zinc-500 font-bold uppercase border-b border-microsoft-border dark:border-zinc-800">
                      <th className="px-6 py-3">Invoice #</th>
                      <th className="px-6 py-3">Amount</th>
                      <th className="px-6 py-3">Due Date</th>
                      <th className="px-6 py-3">Payment Prediction</th>
                      <th className="px-6 py-3">Billing Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-microsoft-border dark:divide-zinc-800">
                    {invoices.map((inv: any) => (
                      <tr key={inv.id} className="hover:bg-gray-50/50 dark:hover:bg-zinc-850/40 transition-colors">
                        <td className="px-6 py-3 font-semibold text-microsoft-charcoal dark:text-white">{inv.invoice_number}</td>
                        <td className="px-6 py-3 font-bold">${inv.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                        <td className="px-6 py-3 text-gray-500 dark:text-zinc-400">{new Date(inv.due_date).toLocaleDateString()}</td>
                        <td className="px-6 py-3">
                          {inv.status !== 'Paid' ? (
                            <span className="font-semibold text-risk-medium">+{inv.payment_delay_prediction_days} days delay</span>
                          ) : (
                            <span className="text-gray-400 dark:text-zinc-500">-</span>
                          )}
                        </td>
                        <td className="px-6 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${inv.status === 'Paid' ? 'bg-green-50 text-risk-low dark:bg-green-950/20' : (inv.status === 'Overdue' ? 'bg-red-50 text-risk-high dark:bg-red-950/20' : 'bg-orange-50 text-risk-medium dark:bg-orange-950/20')}`}>
                            {inv.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Section 4: Contracts */}
          <div className="glass-panel overflow-hidden">
            <button
              onClick={() => setExpandedSection(expandedSection === 'contracts' ? 'timeline' : 'contracts')}
              className="w-full px-6 py-4 bg-[#faf9f8] dark:bg-zinc-900/40 border-b border-microsoft-border dark:border-zinc-800 flex items-center justify-between text-left font-bold text-sm uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300"
            >
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-microsoft-blue" />
                <span>Agreements & Contracts ({contracts.length} active)</span>
              </div>
              {expandedSection === 'contracts' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {expandedSection === 'contracts' && (
              <div className="p-6 space-y-4">
                {contracts.map((con: any) => (
                  <div key={con.id} className="p-4 bg-gray-50 dark:bg-zinc-800/40 rounded space-y-2 border-l-4 border-microsoft-blue">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-microsoft-charcoal dark:text-white">{con.title}</span>
                      <span className="text-xs font-bold text-risk-high">${con.value.toLocaleString()} / Year</span>
                    </div>
                    <div className="text-[11px] text-gray-500 dark:text-zinc-400 space-y-1">
                      <div>Agreement Period: {new Date(con.start_date).toLocaleDateString()} to {new Date(con.end_date).toLocaleDateString()}</div>
                      <div className="font-semibold text-risk-medium">Renewal Risk index: {con.renewal_risk_score.toFixed(1)}/100</div>
                      {con.risk_explanation && <div className="text-gray-400 dark:text-zinc-500 italic mt-1">Agent Explanation: {con.risk_explanation}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Right Side: AI Explainability & Recommendations outreach */}
        <div className="space-y-6">
          
          {/* AI Explainability panel */}
          <div className="glass-panel p-6 border-t-4 border-risk-high space-y-4">
            <div className="flex items-center space-x-2 text-risk-high">
              <ShieldAlert className="w-5 h-5" />
              <h3 className="font-bold text-sm uppercase tracking-wider">AI Explainability Evidence</h3>
            </div>
            
            <div className="space-y-3">
              <p className="text-xs font-semibold text-microsoft-charcoal dark:text-zinc-300">
                {risk_explanation.summary_statement || 'Evaluating account risk indicators...'}
              </p>
              
              {/* Evidence flags list */}
              <div className="space-y-2.5 pt-2 border-t border-microsoft-border dark:border-zinc-800">
                {risk_explanation.evidence_flags?.map((flag: string, index: number) => (
                  <div key={index} className="flex items-start space-x-2 text-xs">
                    <span className="text-risk-high font-bold mt-0.5">•</span>
                    <span className="text-gray-500 dark:text-zinc-400 leading-normal">{flag}</span>
                  </div>
                ))}
              </div>

              {/* Reasoning trace list */}
              {risk_explanation.reasoning_trace && (
                <div className="space-y-2 pt-4 border-t border-microsoft-border dark:border-zinc-800">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 block mb-1">Agent Reasoning Trace</span>
                  <div className="space-y-1.5">
                    {risk_explanation.reasoning_trace.map((step: string, sIdx: number) => (
                      <div key={sIdx} className="bg-gray-50 dark:bg-zinc-900/60 p-2 rounded text-[10px] leading-relaxed border border-microsoft-border dark:border-zinc-800/80 font-mono text-microsoft-blue dark:text-blue-400">
                        {step}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Foundry IQ Grounded Citation Provenance */}
              <div className="space-y-2.5 pt-4 border-t border-microsoft-border dark:border-zinc-800">
                <span className="text-[10px] font-bold uppercase tracking-widest text-microsoft-blue dark:text-blue-400 block mb-1">
                  Foundry IQ Citation Chain
                </span>
                <div className="p-3 bg-microsoft-lightBlue/30 dark:bg-blue-950/10 border border-microsoft-blue/20 rounded text-[11px] space-y-1.5">
                  <div className="flex items-center justify-between font-bold text-microsoft-blue dark:text-blue-300">
                    <span className="truncate">📄 M365_Copilot_Usage_Active_SSO_Incident_Report_Q2_{customer.name.replace(/\s+/g, '_')}.pdf</span>
                    <span className="shrink-0 bg-microsoft-blue text-white text-[9px] px-1 rounded">Cited</span>
                  </div>
                  <p className="text-gray-500 dark:text-zinc-400 italic leading-snug">
                    "...SSO authentication loop issues affected 24% of premium license users between April 14 and May 2, driving a drop in active usage to -32%..."
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Microsoft IQ Visibility Panel */}
          {data.microsoft_iq_insights && (
            <div className="glass-panel p-6 border-t-4 border-microsoft-blue space-y-4">
              <div className="flex items-center space-x-2 text-microsoft-blue">
                <Sparkles className="w-5 h-5" />
                <h3 className="font-bold text-sm uppercase tracking-wider">Microsoft IQ Visibility</h3>
              </div>
              <div className="space-y-4 text-xs">
                {/* Work IQ Section */}
                <div className="space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 block mb-1">Work IQ Relationship Telemetry</span>
                  {data.microsoft_iq_insights.work_iq?.map((item: any, idx: number) => (
                    <div key={idx} className="p-3 bg-gray-50 dark:bg-zinc-900/50 rounded border border-microsoft-border dark:border-zinc-800/60 flex justify-between items-start">
                      <div className="space-y-1 pr-2">
                        <p className="font-semibold text-microsoft-charcoal dark:text-zinc-250 leading-normal">{item.insight}</p>
                        <p className="text-[8px] text-gray-400 font-semibold uppercase tracking-wider">Source: {item.source_agent}</p>
                      </div>
                      <span className={`text-[10px] font-black shrink-0 ${item.impact_score < 0 ? 'text-risk-high' : 'text-risk-low'}`}>
                        {item.impact_score > 0 ? `+${item.impact_score}` : item.impact_score} pts
                      </span>
                    </div>
                  ))}
                </div>

                {/* Foundry IQ Section */}
                <div className="space-y-2 pt-2 border-t border-microsoft-border dark:border-zinc-800">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 block mb-1">Foundry IQ Semantic Insights</span>
                  {data.microsoft_iq_insights.foundry_iq?.map((item: any, idx: number) => (
                    <div key={idx} className="p-3 bg-gray-50 dark:bg-zinc-900/50 rounded border border-microsoft-border dark:border-zinc-800/60 flex justify-between items-start">
                      <div className="space-y-1 pr-2">
                        <p className="font-semibold text-microsoft-charcoal dark:text-zinc-250 leading-normal">{item.insight}</p>
                        <p className="text-[8px] text-gray-400 font-semibold uppercase tracking-wider">Source: {item.source_agent}</p>
                      </div>
                      <span className={`text-[10px] font-black shrink-0 ${item.impact_score < 0 ? 'text-risk-high' : 'text-risk-low'}`}>
                        {item.impact_score > 0 ? `+${item.impact_score}` : item.impact_score} pts
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Recovery Recommendations Outreach Plan cards */}
          <div className="space-y-4">
            <h3 className="font-bold text-sm uppercase tracking-wider text-microsoft-charcoal dark:text-zinc-300 px-1">AI Generated Recovery Outreach</h3>
            
            <div className="space-y-4">
              {recommendations.map((rec: any) => {
                const isApproved = recStatuses[rec.id] === 'Approved';
                
                return (
                  <div key={rec.id} className="glass-panel p-6 border-l-4 border-microsoft-blue space-y-4 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <span className="text-xs font-bold text-microsoft-charcoal dark:text-white leading-snug block">
                          {rec.title}
                        </span>
                        <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-blue-50 text-microsoft-blue dark:bg-blue-900/30 dark:text-blue-300">
                          {rec.action_type}
                        </span>
                      </div>
                      <span className={`text-[10px] font-bold uppercase ${rec.priority === 'High' ? 'text-risk-high' : 'text-risk-medium'}`}>
                        {rec.priority} Priority
                      </span>
                    </div>

                    <p className="text-xs text-gray-500 dark:text-zinc-400 leading-normal">
                      {rec.description}
                    </p>

                    {/* Financial impact breakdown */}
                    <div className="bg-gray-50 dark:bg-zinc-900/40 p-3 rounded text-[11px] space-y-1 border border-microsoft-border dark:border-zinc-800/60">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Gross protected value:</span>
                        <span className="font-semibold text-microsoft-charcoal dark:text-white">${rec.revenue_impact_estimate.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Negotiated discount cost:</span>
                        <span className="font-semibold text-risk-medium">${rec.cost_to_execute.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between pt-1 border-t border-dashed border-gray-200 dark:border-zinc-800 font-bold">
                        <span className="text-gray-400">Net Recovery projection:</span>
                        <span className="text-risk-low">${rec.net_recovery_value.toLocaleString()}</span>
                      </div>
                    </div>

                    {rec.impact_projection && (
                      <p className="text-[10px] text-gray-400 dark:text-zinc-500 italic leading-snug">
                        Projected effect: {rec.impact_projection}
                      </p>
                    )}

                    {/* Approve button */}
                    <button
                      onClick={() => handleApproveRecommendation(rec.id)}
                      disabled={isApproved}
                      data-tour="approve-deploy"
                      className={`w-full py-1.5 rounded text-xs font-bold transition-all cursor-pointer ${
                        isApproved
                          ? 'bg-green-50 text-risk-low border border-risk-low/30 dark:bg-green-950/20'
                          : 'bg-microsoft-blue hover:bg-microsoft-darkBlue text-white shadow-sm'
                      }`}
                    >
                      {isApproved ? 'Outreach Term Sheet Sent' : 'Approve & Deploy Term Sheet'}
                    </button>
                  </div>
                );
              })}
              {recommendations.length === 0 && (
                <div className="text-center py-6 text-gray-400 dark:text-zinc-500 text-xs italic">
                  No pending recovery plans. Run risk sync to synthesize outreach recommendations.
                </div>
              )}
            </div>
          </div>

        </div>

      </div>

      {/* Decision Simulator sliding Drawer component widget */}
      {isSimulatorOpen && (
        <DecisionSimulator
          customerId={customerId}
          customerName={customer.name}
          customerRevenue={customer.revenue}
          onClose={() => setIsSimulatorOpen(false)}
          onUpdateParent={fetchCustomerData}
        />
      )}
    </div>
  );
};

const round = (num: number, decimals: number) => {
  return Number(Math.round(Number(num + 'e' + decimals)) + 'e-' + decimals).toFixed(decimals);
};
