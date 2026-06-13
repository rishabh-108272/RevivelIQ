import React, { useState, useEffect } from 'react';
import { Sparkles, ChevronRight, ChevronLeft, X, Check, Landmark, DollarSign, Activity, Pointer } from 'lucide-react';

interface InteractiveTourProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  selectedCustomerId: number | null;
  setSelectedCustomerId: (id: number | null) => void;
  isOpen: boolean;
  onClose: () => void;
}

interface TourStep {
  title: string;
  description: string;
  actionInstruction: string;
  tab: string;
  badge: string;
  headerIcon?: React.ReactNode;
}

export const InteractiveTour: React.FC<InteractiveTourProps> = ({
  activeTab,
  setActiveTab,
  selectedCustomerId,
  setSelectedCustomerId,
  isOpen,
  onClose,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSimulatorOpen, setIsSimulatorOpen] = useState(false);

  const steps: TourStep[] = [
    {
      title: "Interactive Onboarding Tour",
      description: "Welcome! Let's explore the platform. Rather than showing you slides, this tour will guide you to click through the platform yourself. We'll trace a real recovery case study: rescuing Contoso Corp ($450k ARR). Click 'Start Tour' to begin.",
      actionInstruction: "Click 'Start Tour' below to begin.",
      tab: "dashboard",
      badge: "Getting Started",
      headerIcon: <Landmark className="w-5 h-5 text-microsoft-blue animate-bounce" />
    },
    {
      title: "1. View Churn Risks on the Dashboard",
      description: "You've arrived at the Executive Dashboard. To explore our client list and locate Contoso Corp, let's navigate to the Client Portfolio.",
      actionInstruction: "👉 Action: Click on 'Client Portfolio' in the sidebar.",
      tab: "dashboard",
      badge: "Dashboard"
    },
    {
      title: "2. Analyze Contoso Corp's Profile",
      description: "Great! Now you're in the Client Portfolio view. Find Contoso Corp in the table (first item) and let's analyze their churn risk detail page.",
      actionInstruction: "👉 Action: Click 'Analyze Profile' next to Contoso Corp.",
      tab: "customers",
      badge: "Client Portfolio",
      headerIcon: <Activity className="w-5 h-5 text-risk-high animate-pulse" />
    },
    {
      title: "3. Run a What-If Risk Simulation",
      description: "Welcome to Contoso's risk profile! Look at their Churn Probability (80%) and Exposed Revenue. Let's simulate how we can recover this revenue.",
      actionInstruction: "👉 Action: Click the 'Launch What-If Simulator' button at the top right.",
      tab: "customers",
      badge: "Risk Profile"
    },
    {
      title: "4. Close the Decision Simulator",
      description: "Awesome! You launched the Decision Simulator. CS leads check off variables like 'Resolve all open support tickets' and 'Offer renewal discount' to forecast health changes. Let's return to the profile view.",
      actionInstruction: "👉 Action: Close the Decision Simulator drawer (click 'X' at top right).",
      tab: "customers",
      badge: "Simulator Active"
    },
    {
      title: "5. Approve AI Recovery Recommendations",
      description: "Look at the 'AI Generated Recovery Outreach' on the right side of the profile page. It suggests a 'M365 Copilot Rate Discount'. Let's deploy it.",
      actionInstruction: "👉 Action: Click 'Approve & Deploy Term Sheet' on the outreach card, then click 'Next Step'.",
      tab: "customers",
      badge: "AI Recommendations"
    },
    {
      title: "6. Check the Recovery Outreach queue",
      description: "The discount outreach is now deployed. Let's check our active outreach tracker to monitor its progress.",
      actionInstruction: "👉 Action: Click on 'Recovery Outreach' in the sidebar.",
      tab: "recommendations",
      badge: "Outreach Actions"
    },
    {
      title: "7. Scaled Rescue Campaigns",
      description: "Great job! This is the Recovery Outreach board. Now let's explore how we automate this process for multiple accounts at once.",
      actionInstruction: "👉 Action: Click on 'Rescue Campaigns' in the sidebar.",
      tab: "campaigns",
      badge: "Rescue Campaigns"
    },
    {
      title: "8. Enter the Revenue War Room",
      description: "Campaigns help scale outreach. For critical emergency events, we use a collaborative incident room to align cross-functional teams.",
      actionInstruction: "👉 Action: Click on 'Revenue War Room' in the sidebar.",
      tab: "war-room",
      badge: "War Room"
    },
    {
      title: "9. Map Stakeholder Sentiment",
      description: "In addition to team collaboration, mapping organizational structure is crucial. Let's look at the Org Simulator.",
      actionInstruction: "👉 Action: Click on 'Org Simulator' in the sidebar.",
      tab: "org-simulator",
      badge: "Org Simulator"
    },
    {
      title: "10. View AI Copilot Agent Logs",
      description: "Finally, let's look behind the curtain at the 6 specialized AI agents running our risk predictions, billing syncs, and communications analysis.",
      actionInstruction: "👉 Action: Click on 'Copilot Extension' in the sidebar.",
      tab: "copilot",
      badge: "Copilot Agents",
      headerIcon: <Sparkles className="w-5 h-5 text-microsoft-blue animate-pulse" />
    },
    {
      title: "Tour Completed Successfully!",
      description: "Congratulations! You have completed the interactive click tour. You now know how to detect churn risks, drill down into customer details, run What-If simulations, approve AI-generated outreach term sheets, and collaborate across departments.",
      actionInstruction: "Click 'Finish Tour' below to start using ReviveIQ!",
      tab: "copilot",
      badge: "Tour Done",
      headerIcon: <Check className="w-5 h-5 text-risk-low" />
    }
  ];

  // Poll for DOM state (specifically if Decision Simulator is open)
  useEffect(() => {
    if (!isOpen) return;
    const interval = setInterval(() => {
      const isSimOpen = Array.from(document.querySelectorAll('h2')).some(
        el => el.textContent?.includes('Decision Simulator')
      );
      setIsSimulatorOpen(isSimOpen);
    }, 250);
    return () => clearInterval(interval);
  }, [isOpen]);

  // Monitor user clicks and state changes to automatically advance the tour
  useEffect(() => {
    if (!isOpen) return;

    // STEP 1: Wait for user to navigate to "customers" (Client Portfolio)
    if (currentStep === 1 && activeTab === 'customers' && selectedCustomerId === null) {
      setCurrentStep(2);
    }
    
    // STEP 2: Wait for user to open a customer profile (which sets selectedCustomerId)
    if (currentStep === 2 && selectedCustomerId !== null) {
      setCurrentStep(3);
    }

    // STEP 3: Wait for user to open the Decision Simulator drawer
    if (currentStep === 3 && isSimulatorOpen) {
      setCurrentStep(4);
    }

    // STEP 4: Wait for user to close the Decision Simulator drawer
    if (currentStep === 4 && !isSimulatorOpen && selectedCustomerId !== null) {
      setCurrentStep(5);
    }

    // STEP 6: Wait for user to navigate to "recommendations" (Recovery Outreach)
    if (currentStep === 6 && activeTab === 'recommendations') {
      setCurrentStep(7);
    }

    // STEP 7: Wait for user to navigate to "campaigns" (Rescue Campaigns)
    if (currentStep === 7 && activeTab === 'campaigns') {
      setCurrentStep(8);
    }

    // STEP 8: Wait for user to navigate to "war-room" (Revenue War Room)
    if (currentStep === 8 && activeTab === 'war-room') {
      setCurrentStep(9);
    }

    // STEP 9: Wait for user to navigate to "org-simulator" (Org Simulator)
    if (currentStep === 9 && activeTab === 'org-simulator') {
      setCurrentStep(10);
    }

    // STEP 10: Wait for user to navigate to "copilot" (Copilot Extension)
    if (currentStep === 10 && activeTab === 'copilot') {
      setCurrentStep(11);
    }

  }, [activeTab, selectedCustomerId, isSimulatorOpen, currentStep, isOpen]);

  if (!isOpen) return null;

  const step = steps[currentStep];
  const isFirst = currentStep === 0;
  const isLast = currentStep === steps.length - 1;

  const handleNext = () => {
    if (isLast) {
      handleComplete();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirst) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleComplete = () => {
    localStorage.setItem('reviveiq_tour_completed', 'true');
    onClose();
  };

  return (
    <div className="fixed bottom-6 right-6 z-[9999] max-w-sm sm:max-w-md w-full animate-in fade-in slide-in-from-bottom-5 duration-300">
      <div className="bg-white dark:bg-[#201f1e] border-2 border-microsoft-blue dark:border-blue-500 rounded-xl shadow-2xl overflow-hidden p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-microsoft-border dark:border-zinc-800 pb-3">
          <div className="flex items-center space-x-2">
            {step.headerIcon || <Sparkles className="w-5 h-5 text-microsoft-blue dark:text-blue-400 animate-pulse" />}
            <span className="text-[10px] font-bold text-microsoft-blue dark:text-blue-400 uppercase tracking-widest bg-microsoft-blue/10 dark:bg-blue-500/10 px-2 py-0.5 rounded">
              {step.badge || "Tour Guide"}
            </span>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-850 text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-2.5">
          <h3 className="text-base font-bold text-microsoft-charcoal dark:text-white">
            {step.title}
          </h3>
          <p className="text-xs text-gray-500 dark:text-zinc-400 leading-relaxed min-h-[64px]">
            {step.description}
          </p>
          
          {/* Interactive Action Instruction */}
          <div className="p-3 bg-blue-50/60 dark:bg-blue-950/20 border-l-4 border-microsoft-blue rounded-r text-xs font-bold text-microsoft-blue dark:text-blue-400 flex items-center space-x-2">
            <Pointer className="w-4 h-4 animate-pulse shrink-0" />
            <span>{step.actionInstruction}</span>
          </div>
        </div>

        {/* Footer & Controls */}
        <div className="flex items-center justify-between pt-2 border-t border-microsoft-border dark:border-zinc-800">
          <div className="text-[11px] font-semibold text-gray-400 dark:text-zinc-500">
            Step <span className="text-microsoft-charcoal dark:text-white font-bold">{currentStep + 1}</span> of {steps.length}
          </div>

          <div className="flex items-center space-x-2">
            {!isFirst && (
              <button
                onClick={handlePrev}
                className="flex items-center space-x-1 px-3 py-1.5 rounded text-xs font-semibold border border-microsoft-border hover:bg-gray-50 dark:border-zinc-700 dark:hover:bg-zinc-800 text-gray-600 dark:text-zinc-300 transition-colors cursor-pointer"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Back</span>
              </button>
            )}
            
            <button
              onClick={handleNext}
              className="flex items-center space-x-1 px-4 py-1.5 rounded text-xs font-bold bg-microsoft-blue hover:bg-microsoft-darkBlue text-white shadow transition-colors cursor-pointer"
            >
              <span>{isFirst ? 'Start Tour' : (isLast ? 'Finish Tour' : 'Skip Step')}</span>
              {isLast ? <Check className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
