import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Bot, Send, ShieldAlert, Sparkles, Terminal, Code, ExternalLink, RefreshCw } from 'lucide-react';

export const CopilotAgentPanel: React.FC = () => {
  const { getAuthHeaders } = useAuth();
  
  const [messages, setMessages] = useState<any[]>([
    {
      sender: 'copilot',
      text: "Hello! I am your ReviveIQ Revenue Recovery Agent for Microsoft 365 Copilot. Ask me questions like:\n- Who has unpaid invoices over $20k?\n- Find high-risk customers\n- Find emails regarding contract disputes",
      date: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTrace, setActiveTrace] = useState<any>(null);

  const starters = [
    "Which customers are likely to churn?",
    "What revenue is at risk this month?",
    "Show top revenue threats.",
    "Generate a rescue campaign for Acme Corp.",
    "Create a board report.",
    "Show revenue crisis alerts."
  ];

  const handleSendPrompt = async (promptText: string) => {
    if (!promptText.trim()) return;
    
    // Append user message
    const userMsg = { sender: 'user', text: promptText, date: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);
    setActiveTrace(null);
    
    try {
      const headers = getAuthHeaders();
      const res = await fetch('/api/copilot/query', {
        method: 'POST',
        headers: {
          ...headers,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt: promptText })
      });
      
      if (res.ok) {
        const data = await res.json();
        
        // Append Copilot response
        setMessages(prev => [...prev, {
          sender: 'copilot',
          text: data.response_text,
          adaptiveCard: data.adaptive_card,
          reasoningTrace: data.reasoning_trace,
          supportingEvidence: data.supporting_evidence,
          date: new Date()
        }]);
        
        // Save integration trace
        setActiveTrace({
          endpoint: 'POST /api/copilot/query',
          payload: { prompt: promptText },
          response: data
        });
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        sender: 'copilot',
        text: "Error connecting to the ReviveIQ Copilot Extensibility API.",
        date: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Live custom renderer for Microsoft Adaptive Cards JSON
  const renderAdaptiveCard = (card: any) => {
    if (!card || card.type !== 'AdaptiveCard') return null;
    
    return (
      <div className="w-full bg-[#f3f2f1] dark:bg-zinc-900 border border-microsoft-border dark:border-zinc-800 rounded-lg p-4 font-sans text-xs space-y-3 max-w-sm mt-3 animate-fade-in shadow-sm">
        {card.body?.map((element: any, idx: number) => {
          if (element.type === 'Container') {
            const isEmphasis = element.style === 'emphasis';
            const styleColor = element.style === 'Attention' ? 'border-l-4 border-risk-high bg-red-50/20' : (element.style === 'Warning' ? 'border-l-4 border-risk-medium bg-orange-50/20' : '');
            
            return (
              <div key={idx} className={`p-2.5 rounded ${isEmphasis ? 'bg-microsoft-lightBlue/40 dark:bg-blue-950/10' : ''} ${styleColor}`}>
                {element.items?.map((item: any, itemIdx: number) => (
                  <div
                    key={itemIdx}
                    className={`
                      ${item.weight === 'Bolder' ? 'font-bold' : ''}
                      ${item.size === 'Large' ? 'text-sm' : (item.size === 'Medium' ? 'text-xs' : 'text-[11px]')}
                      ${item.color === 'Accent' ? 'text-microsoft-blue' : 'text-microsoft-charcoal dark:text-zinc-200'}
                    `}
                  >
                    {item.text}
                  </div>
                ))}
              </div>
            );
          }
          
          if (element.type === 'FactSet') {
            return (
              <div key={idx} className="grid grid-cols-2 gap-y-1 py-1 border-t border-b border-gray-200 dark:border-zinc-800 my-2">
                {element.facts?.map((fact: any, factIdx: number) => (
                  <React.Fragment key={factIdx}>
                    <span className="text-gray-400 font-semibold">{fact.title}:</span>
                    <span className="font-semibold text-microsoft-charcoal dark:text-white text-right">{fact.value}</span>
                  </React.Fragment>
                ))}
              </div>
            );
          }
          
          if (element.type === 'TextBlock') {
            return (
              <div
                key={idx}
                className={`
                  ${element.weight === 'Bolder' ? 'font-bold' : ''}
                  ${element.size === 'Large' ? 'text-sm' : (element.size === 'Medium' ? 'text-xs' : 'text-[11px]')}
                  ${element.spacing === 'Medium' ? 'mt-2 font-bold text-microsoft-blue' : ''}
                  dark:text-zinc-300
                `}
              >
                {element.text}
              </div>
            );
          }
          
          return null;
        })}
        
        {/* Actions rendering */}
        {card.actions && (
          <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-200 dark:border-zinc-800">
            {card.actions.map((act: any, idx: number) => (
              <button
                key={idx}
                onClick={() => {
                  if (act.type === 'Action.OpenUrl') {
                    window.open(act.url, '_blank');
                  } else {
                    alert(`Action.Submit triggered: ${JSON.stringify(act.data)}`);
                  }
                }}
                className="flex items-center space-x-1.5 px-3 py-1 rounded bg-microsoft-blue text-white hover:bg-microsoft-darkBlue font-bold text-[10px] transition-colors cursor-pointer"
              >
                <span>{act.title}</span>
                {act.type === 'Action.OpenUrl' && <ExternalLink className="w-3 h-3" />}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 flex overflow-hidden h-[calc(100vh-57px)]">
      
      {/* Left Chat Window Panel */}
      <div className="flex-1 flex flex-col justify-between bg-white dark:bg-[#201f1e] p-6 border-r border-microsoft-border dark:border-zinc-850">
        
        {/* Chat Header */}
        <div className="border-b border-microsoft-border dark:border-zinc-800 pb-4 flex items-center space-x-3">
          <div className="p-2 bg-microsoft-lightBlue dark:bg-microsoft-blue/10 text-microsoft-blue rounded-full">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-sm dark:text-white leading-none">Microsoft 365 Copilot Chat</h2>
            <p className="text-[10px] text-gray-400 mt-1.5">Simulated Copilot Agent Extensibility Sandbox</p>
          </div>
        </div>

        {/* Conversation flow */}
        <div className="flex-1 overflow-y-auto py-6 space-y-4 pr-2">
          {messages.map((msg, index) => {
            const isCopilot = msg.sender === 'copilot';
            return (
              <div key={index} className={`flex items-start space-x-3 ${isCopilot ? '' : 'flex-row-reverse space-x-reverse'}`}>
                <div className={`p-1.5 rounded-full ${isCopilot ? 'bg-microsoft-blue text-white' : 'bg-gray-200 dark:bg-zinc-700 text-microsoft-charcoal dark:text-zinc-200'}`}>
                  <Bot className="w-3.5 h-3.5" />
                </div>
                <div className={`max-w-md p-4 rounded-lg text-xs leading-normal shadow-sm ${
                  isCopilot
                    ? 'bg-[#faf9f8] dark:bg-zinc-900 border border-microsoft-border dark:border-zinc-800 text-microsoft-charcoal dark:text-zinc-300'
                    : 'bg-microsoft-blue text-white font-semibold'
                }`}>
                  {/* Handle newlines in messages */}
                  <div className="whitespace-pre-line">{msg.text}</div>
                  
                  {/* Render adaptive card if present */}
                  {msg.adaptiveCard && renderAdaptiveCard(msg.adaptiveCard)}

                  {/* Render Reasoning Trace if present */}
                  {isCopilot && msg.reasoningTrace && (
                    <div className="mt-4 pt-3 border-t border-gray-200 dark:border-zinc-800">
                      <details className="group">
                        <summary className="font-bold text-[10px] text-gray-400 dark:text-zinc-500 cursor-pointer flex items-center justify-between select-none hover:text-microsoft-blue dark:hover:text-blue-400">
                          <span>AI Agent Reasoning Trace</span>
                          <span className="text-[8px] transition-transform group-open:rotate-180">▼</span>
                        </summary>
                        <div className="mt-2 space-y-1 bg-white dark:bg-zinc-950 p-2 rounded border border-microsoft-border dark:border-zinc-850/80 font-mono text-[9px] text-microsoft-blue dark:text-blue-300">
                          {msg.reasoningTrace.map((step: string, sIdx: number) => (
                            <div key={sIdx}>{step}</div>
                          ))}
                        </div>
                      </details>
                    </div>
                  )}

                  {/* Render Supporting Evidence if present */}
                  {isCopilot && msg.supportingEvidence && (
                    <div className="mt-2 pt-2 border-t border-gray-200 dark:border-zinc-800">
                      <details className="group">
                        <summary className="font-bold text-[10px] text-gray-400 dark:text-zinc-500 cursor-pointer flex items-center justify-between select-none hover:text-microsoft-blue dark:hover:text-blue-400">
                          <span>Supporting Evidence</span>
                          <span className="text-[8px] transition-transform group-open:rotate-180">▼</span>
                        </summary>
                        <div className="mt-2 bg-white dark:bg-zinc-950 p-2 rounded border border-microsoft-border dark:border-zinc-850/80 text-[9px] text-gray-500 dark:text-zinc-400 max-h-48 overflow-y-auto">
                          <pre className="whitespace-pre-wrap font-mono leading-relaxed">
                            {typeof msg.supportingEvidence === 'string' ? msg.supportingEvidence : JSON.stringify(msg.supportingEvidence, null, 2)}
                          </pre>
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {isLoading && (
            <div className="flex items-center space-x-2 text-xs text-gray-400 pl-8">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Copilot is generating response...</span>
            </div>
          )}
        </div>

        {/* Suggestion starters */}
        <div className="space-y-4 border-t border-microsoft-border dark:border-zinc-800 pt-4">
          <div className="flex flex-wrap gap-2">
            {starters.map((start, idx) => (
              <button
                key={idx}
                onClick={() => handleSendPrompt(start)}
                className="px-3 py-1.5 rounded-full border border-microsoft-border dark:border-zinc-700 hover:border-microsoft-blue text-[11px] text-gray-500 hover:text-microsoft-blue dark:text-zinc-400 dark:hover:text-blue-300 bg-[#faf9f8] dark:bg-zinc-900 transition-all cursor-pointer"
              >
                {start}
              </button>
            ))}
          </div>

          {/* Form input */}
          <div className="flex space-x-3">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendPrompt(inputText)}
              placeholder="Ask Copilot about customer risks..."
              className="flex-1 px-4 py-2 border border-microsoft-border dark:border-zinc-700 rounded bg-[#faf9f8] dark:bg-zinc-900 focus:bg-white dark:focus:bg-[#11100f] text-xs outline-none focus:border-microsoft-blue text-microsoft-charcoal dark:text-white"
            />
            <button
              onClick={() => handleSendPrompt(inputText)}
              className="p-2.5 rounded bg-microsoft-blue hover:bg-microsoft-darkBlue text-white shadow transition-colors cursor-pointer"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>

      {/* Right Developer Integration Payload Trace Panel */}
      <div className="hidden lg:flex flex-col w-96 bg-[#faf9f8] dark:bg-zinc-900/40 p-6 overflow-y-auto">
        <div className="flex items-center space-x-2 text-microsoft-blue pb-4 border-b border-microsoft-border dark:border-zinc-800">
          <Terminal className="w-5 h-5" />
          <h3 className="font-bold text-xs uppercase tracking-wider">Integration Trace Log</h3>
        </div>

        {activeTrace ? (
          <div className="space-y-5 pt-4">
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-gray-400 uppercase">REST Endpoint Invoked:</span>
              <code className="block text-[11px] font-mono text-pink-600 bg-pink-50 dark:bg-pink-950/20 px-2 py-1 rounded">
                {activeTrace.endpoint}
              </code>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-gray-400 uppercase flex items-center gap-1">
                <Code className="w-3.5 h-3.5" /> Request Payload:
              </span>
              <pre className="text-[10px] font-mono bg-white dark:bg-zinc-900 p-3 rounded border border-microsoft-border dark:border-zinc-800 overflow-x-auto dark:text-zinc-300">
                {JSON.stringify(activeTrace.payload, null, 2)}
              </pre>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-gray-400 uppercase flex items-center gap-1">
                <Code className="w-3.5 h-3.5" /> Response JSON:
              </span>
              <pre className="text-[10px] font-mono bg-white dark:bg-zinc-900 p-3 rounded border border-microsoft-border dark:border-zinc-800 overflow-x-auto dark:text-zinc-300">
                {JSON.stringify(activeTrace.response, null, 2)}
              </pre>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-400 dark:text-zinc-500 py-24 space-y-2">
            <Code className="w-6 h-6" />
            <p className="text-[10px] font-bold">No API calls recorded yet.</p>
            <p className="text-[9px]">Send a Copilot prompt to view real-time HTTP trace telemetry payloads.</p>
          </div>
        )}
      </div>

    </div>
  );
};
