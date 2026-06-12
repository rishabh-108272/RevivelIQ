import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { CustomerDetail } from './components/CustomerDetail';
import { Recommendations } from './components/Recommendations';
import { CampaignsPage } from './components/CampaignsPage';
import { WarRoomPage } from './components/WarRoomPage';
import { OrgSimulatorPage } from './components/OrgSimulatorPage';
import { CopilotAgentPanel } from './components/CopilotAgentPanel';
import { Bot, Shield, KeyRound, Sparkles, RefreshCw } from 'lucide-react';

const MainLayout: React.FC = () => {
  const { user, getAuthHeaders } = useAuth();
  
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  
  const [searchValue, setSearchValue] = useState('');
  const [isReseeding, setIsReseeding] = useState(false);

  const handleReseed = async () => {
    if (!window.confirm("Wipe simulation environment? This resets the database and pre-calculates 100 new customer risk assessments.")) return;
    
    setIsReseeding(true);
    try {
      const headers = getAuthHeaders();
      const res = await fetch('/api/analytics/reseed', {
        method: 'POST',
        headers
      });
      if (res.ok) {
        alert("Database successfully reseeded!");
        // Refresh page to load fresh metrics
        window.location.reload();
      }
    } catch (err) {
      console.error(err);
      alert("Failed to reseed database.");
    } finally {
      setIsReseeding(false);
    }
  };

  const handleSelectCustomer = (id: number) => {
    setSelectedCustomerId(id);
    setActiveTab('customers');
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#f3f2f1] dark:bg-[#11100f] text-microsoft-charcoal dark:text-zinc-200">
      
      {/* Header Banner */}
      <Header onSearchChange={setSearchValue} searchValue={searchValue} />
      
      {/* Content Frame */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Navigation */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={(tab) => {
            setActiveTab(tab);
            // If leaving customer tab, clear active customer selection
            if (tab !== 'customers') setSelectedCustomerId(null);
          }}
          onReseed={handleReseed}
          isReseeding={isReseeding}
        />

        {/* Dynamic Route views container */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#faf9f8] dark:bg-[#11100f] overflow-hidden">
          {activeTab === 'dashboard' && (
            <Dashboard onSelectCustomer={handleSelectCustomer} searchValue={searchValue} />
          )}
          
          {activeTab === 'customers' && (
            selectedCustomerId ? (
              <CustomerDetail customerId={selectedCustomerId} onBack={() => setSelectedCustomerId(null)} />
            ) : (
              // Default to Dashboard portfolio view if no customer selected
              <Dashboard onSelectCustomer={handleSelectCustomer} searchValue={searchValue} />
            )
          )}
          
          {activeTab === 'recommendations' && (
            <Recommendations />
          )}
          
          {activeTab === 'campaigns' && (
            <CampaignsPage />
          )}
          
          {activeTab === 'war-room' && (
            <WarRoomPage onSelectCustomer={handleSelectCustomer} />
          )}
          
          {activeTab === 'org-simulator' && (
            <OrgSimulatorPage />
          )}
          
          {activeTab === 'copilot' && (
            <CopilotAgentPanel />
          )}
        </main>
      </div>

      {/* Global Reseed Loader Overlay */}
      {isReseeding && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-md z-[9999] flex flex-col items-center justify-center text-white space-y-4">
          <RefreshCw className="w-12 h-12 text-microsoft-blue animate-spin" />
          <h2 className="text-lg font-bold">Reseeding Enterprise Datasets...</h2>
          <p className="text-xs text-zinc-400">Please wait while our 6 AI agents pre-calculate risk scores and recommendations for 100 seeded customers...</p>
        </div>
      )}

    </div>
  );
};

const LoginScreen: React.FC = () => {
  const { login } = useAuth();
  
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [role, setRole] = useState('Customer Success');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccessMessage('');
    
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      if (res.ok) {
        const data = await res.json();
        login(data.email, data.role, data.full_name, data.access_token);
      } else {
        const errData = await res.json();
        setError(errData.detail || "Authentication failed. Incorrect email or password.");
      }
    } catch (err) {
      console.error(err);
      setError("Cannot connect to ReviveIQ login API.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccessMessage('');
    
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
          organization_name: organizationName,
          role
        })
      });
      
      if (res.ok) {
        setSuccessMessage("Account created successfully! We are generating your organization's synthetic data and syncing risk models in the background. Please sign in now.");
        setIsRegistering(false);
        setPassword('');
      } else {
        const errData = await res.json();
        setError(errData.detail || "Registration failed. Please check your inputs.");
      }
    } catch (err) {
      console.error(err);
      setError("Cannot connect to ReviveIQ registration API.");
    } finally {
      setIsLoading(false);
    }
  };

  // Hackathon Quick Bypass Login Helper
  const handleQuickBypass = async (roleEmail: string, rolePass: string) => {
    setIsLoading(true);
    setError('');
    setSuccessMessage('');
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: roleEmail, password: rolePass })
      });
      
      if (res.ok) {
        const data = await res.json();
        login(data.email, data.role, data.full_name, data.access_token);
      }
    } catch (err) {
      console.error(err);
      setError("Bypass connection failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f3f2f1] dark:bg-[#11100f] flex items-center justify-center px-4 font-sans select-none transition-colors">
      <div className="w-full max-w-md bg-white dark:bg-[#201f1e] rounded-lg shadow-xl border border-microsoft-border dark:border-zinc-800 p-8 space-y-6">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center space-y-2 text-center">
          <div className="flex items-center justify-center w-12 h-12 bg-microsoft-blue text-white font-black text-2xl rounded shadow">
            R
          </div>
          <h1 className="text-xl font-bold dark:text-white mt-1.5 tracking-tight flex items-center gap-1.5">
            <span>ReviveIQ Control Center</span>
          </h1>
          <p className="text-xs text-gray-400">AI Revenue Recovery Agent for Microsoft 365 Copilot</p>
        </div>

        {successMessage && (
          <div className="p-3 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-400 rounded text-[11px] leading-normal font-semibold border border-green-250 dark:border-green-900/50">
            {successMessage}
          </div>
        )}

        {/* Hackathon Quick Bypass Banner */}
        <div className="p-4 bg-blue-50 dark:bg-zinc-900/50 border border-microsoft-blue/30 rounded-lg text-center space-y-2">
          <div className="text-[10px] font-bold text-microsoft-blue uppercase tracking-wider flex items-center justify-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 animate-pulse text-yellow-500" />
            <span>Hackathon Quick Mode</span>
          </div>
          <button
            onClick={() => {
              // Bypasses backend login API and enters dashboard immediately using the bypass token!
              login("admin@reviveiq.com", "Admin", "System Administrator", "hackathon-bypass-token");
            }}
            className="w-full py-2.5 rounded bg-microsoft-blue hover:bg-microsoft-darkBlue text-white text-xs font-bold transition-all shadow cursor-pointer flex items-center justify-center gap-1.5"
          >
            <KeyRound className="w-3.5 h-3.5" />
            <span>Instant Access Bypass</span>
          </button>
          <p className="text-[9px] text-gray-400">Enters dashboard directly with full Admin controls</p>
        </div>

        {isRegistering ? (
          /* Registration Form */
          <form onSubmit={handleRegisterSubmit} className="space-y-4 text-xs font-semibold">
            <div className="space-y-1.5">
              <label className="text-gray-400 uppercase tracking-widest text-[9px]">Full Name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Arianne Admin"
                className="w-full px-3.5 py-2.5 rounded border border-microsoft-border dark:border-zinc-700 bg-gray-50 dark:bg-zinc-900 focus:bg-white dark:focus:bg-[#11100f] outline-none focus:border-microsoft-blue dark:text-white font-normal"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-gray-400 uppercase tracking-widest text-[9px]">Organization Name</label>
              <input
                type="text"
                required
                value={organizationName}
                onChange={(e) => setOrganizationName(e.target.value)}
                placeholder="Contoso Corp"
                className="w-full px-3.5 py-2.5 rounded border border-microsoft-border dark:border-zinc-700 bg-gray-50 dark:bg-zinc-900 focus:bg-white dark:focus:bg-[#11100f] outline-none focus:border-microsoft-blue dark:text-white font-normal"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-gray-400 uppercase tracking-widest text-[9px]">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="w-full px-3.5 py-2.5 rounded border border-microsoft-border dark:border-zinc-700 bg-gray-50 dark:bg-zinc-900 focus:bg-white dark:focus:bg-[#11100f] outline-none focus:border-microsoft-blue dark:text-white font-normal"
              />
            </div>
            
            <div className="space-y-1.5">
              <label className="text-gray-400 uppercase tracking-widest text-[9px]">Security Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3.5 py-2.5 rounded border border-microsoft-border dark:border-zinc-700 bg-gray-50 dark:bg-zinc-900 focus:bg-white dark:focus:bg-[#11100f] outline-none focus:border-microsoft-blue dark:text-white font-normal"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-gray-400 uppercase tracking-widest text-[9px]">Enterprise Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded border border-microsoft-border dark:border-zinc-700 bg-gray-50 dark:bg-zinc-900 focus:bg-white dark:focus:bg-[#11100f] outline-none focus:border-microsoft-blue dark:text-white font-normal"
              >
                <option value="Customer Success">Customer Success</option>
                <option value="Finance">Finance Lead</option>
                <option value="Sales">Sales Lead</option>
                <option value="Admin">System Admin</option>
              </select>
            </div>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-950/20 text-risk-high rounded text-[11px] leading-normal font-semibold">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 rounded bg-microsoft-blue hover:bg-microsoft-darkBlue text-white text-xs font-bold transition-all shadow cursor-pointer disabled:opacity-50"
            >
              {isLoading ? 'Creating Account & Seeding...' : 'Register & Create Environment'}
            </button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(false);
                  setError('');
                  setSuccessMessage('');
                }}
                className="text-microsoft-blue hover:text-microsoft-darkBlue text-xs font-semibold hover:underline cursor-pointer bg-transparent border-none outline-none"
              >
                Already have an account? Sign in
              </button>
            </div>
          </form>
        ) : (
          /* Credentials Login Form */
          <form onSubmit={handleCredentialsSubmit} className="space-y-4 text-xs font-semibold">
            <div className="space-y-1.5">
              <label className="text-gray-400 uppercase tracking-widest text-[9px]">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@reviveiq.com"
                className="w-full px-3.5 py-2.5 rounded border border-microsoft-border dark:border-zinc-700 bg-gray-50 dark:bg-zinc-900 focus:bg-white dark:focus:bg-[#11100f] outline-none focus:border-microsoft-blue dark:text-white font-normal"
              />
            </div>
            
            <div className="space-y-1.5">
              <label className="text-gray-400 uppercase tracking-widest text-[9px]">Security Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3.5 py-2.5 rounded border border-microsoft-border dark:border-zinc-700 bg-gray-50 dark:bg-zinc-900 focus:bg-white dark:focus:bg-[#11100f] outline-none focus:border-microsoft-blue dark:text-white font-normal"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-950/20 text-risk-high rounded text-[11px] leading-normal font-semibold">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 rounded bg-microsoft-blue hover:bg-microsoft-darkBlue text-white text-xs font-bold transition-all shadow cursor-pointer disabled:opacity-50"
            >
              {isLoading ? 'Verifying Credentials...' : 'Sign In to Dashboard'}
            </button>

            <div className="text-center pt-2">
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(true);
                  setError('');
                  setSuccessMessage('');
                }}
                className="text-microsoft-blue hover:text-microsoft-darkBlue text-xs font-semibold hover:underline cursor-pointer bg-transparent border-none outline-none"
              >
                Don't have an account? Create one
              </button>
            </div>
          </form>
        )}

        {/* Quick Bypass Role Selectors */}
        <div className="space-y-3 pt-4 border-t border-microsoft-border dark:border-zinc-800">
          <div className="flex items-center space-x-1.5 text-microsoft-blue text-[10px] tracking-wider uppercase font-bold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Developer Role Selection Bypass</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => handleQuickBypass('admin@reviveiq.com', 'admin123')}
              className="p-2 rounded bg-gray-50 hover:bg-gray-100 dark:bg-zinc-900 dark:hover:bg-zinc-850 border border-microsoft-border dark:border-zinc-850 hover:border-microsoft-blue/50 text-[10px] text-left transition-colors flex items-center space-x-1.5 font-semibold text-microsoft-charcoal dark:text-zinc-300 cursor-pointer"
            >
              <Shield className="w-3.5 h-3.5 text-risk-high" />
              <div className="flex flex-col">
                <span className="font-bold">System Admin</span>
                <span className="text-[8px] text-gray-400">Wipe & Reseed DB</span>
              </div>
            </button>
            
            <button
              onClick={() => handleQuickBypass('cs@reviveiq.com', 'cs123')}
              className="p-2 rounded bg-gray-50 hover:bg-gray-100 dark:bg-zinc-900 dark:hover:bg-zinc-850 border border-microsoft-border dark:border-zinc-850 hover:border-microsoft-blue/50 text-[10px] text-left transition-colors flex items-center space-x-1.5 font-semibold text-microsoft-charcoal dark:text-zinc-300 cursor-pointer"
            >
              <Shield className="w-3.5 h-3.5 text-risk-low" />
              <div className="flex flex-col">
                <span className="font-bold">Customer Success</span>
                <span className="text-[8px] text-gray-400">Resolve tickets</span>
              </div>
            </button>

            <button
              onClick={() => handleQuickBypass('finance@reviveiq.com', 'finance123')}
              className="p-2 rounded bg-gray-50 hover:bg-gray-100 dark:bg-zinc-900 dark:hover:bg-zinc-850 border border-microsoft-border dark:border-zinc-850 hover:border-microsoft-blue/50 text-[10px] text-left transition-colors flex items-center space-x-1.5 font-semibold text-microsoft-charcoal dark:text-zinc-300 cursor-pointer"
            >
              <Shield className="w-3.5 h-3.5 text-risk-medium" />
              <div className="flex flex-col">
                <span className="font-bold">Finance Lead</span>
                <span className="text-[8px] text-gray-400">Collect invoices</span>
              </div>
            </button>

            <button
              onClick={() => handleQuickBypass('sales@reviveiq.com', 'sales123')}
              className="p-2 rounded bg-gray-50 hover:bg-gray-100 dark:bg-zinc-900 dark:hover:bg-zinc-850 border border-microsoft-border dark:border-zinc-850 hover:border-microsoft-blue/50 text-[10px] text-left transition-colors flex items-center space-x-1.5 font-semibold text-microsoft-charcoal dark:text-zinc-300 cursor-pointer"
            >
              <Shield className="w-3.5 h-3.5 text-microsoft-blue" />
              <div className="flex flex-col">
                <span className="font-bold">Sales Lead</span>
                <span className="text-[8px] text-gray-400">Renew contract</span>
              </div>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f3f2f1] dark:bg-[#11100f]">
        <RefreshCw className="w-8 h-8 text-microsoft-blue animate-spin" />
      </div>
    );
  }

  return user ? <MainLayout /> : <LoginScreen />;
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
