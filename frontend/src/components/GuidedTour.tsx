import { useState, useEffect, useRef } from "react";

export interface TourStep {
  targetSelector: string;   // CSS selector for the element to spotlight
  title: string;
  description: string;
  position: "top" | "bottom" | "left" | "right";
  action?: string;          // Optional: label for a simulated click action
}

export const reviveIQTourSteps: TourStep[] = [
  {
    targetSelector: "[data-tour='kpi-arr']",
    title: "Revenue at Risk",
    description: "This card shows the total ARR across accounts flagged as High or Critical risk. Watch this number — it's your north star.",
    position: "bottom",
  },
  {
    targetSelector: "[data-tour='executive-briefing']",
    title: "AI Executive Briefing",
    description: "The Executive Briefing Agent synthesizes your entire portfolio into a plain-English narrative every morning. No spreadsheet diving.",
    position: "bottom",
  },
  {
    targetSelector: "[data-tour='stressed-clients']",
    title: "Stressed accounts",
    description: "Accounts sorted by churn probability. Click any row to open the full customer profile with the agent's risk evidence.",
    position: "top",
  },
  {
    targetSelector: "[data-tour='sync-risk']",
    title: "Sync risk metrics",
    description: "This triggers the full 6-agent orchestration pipeline. All agents run in sequence and write fresh scores to the database.",
    position: "bottom",
    action: "Trigger sync",
  },
  {
    targetSelector: "[data-tour='whats-if-launch']",
    title: "What-if simulator",
    description: "Slide variables — clear invoices, resolve tickets, apply a discount — and see the projected churn probability drop in real time.",
    position: "left",
  },
  {
    targetSelector: "[data-tour='approve-deploy']",
    title: "Approve & deploy",
    description: "When you find a recovery scenario that works, approve it here. The system registers the term sheet and tracks execution cost vs. net recovery.",
    position: "top",
  },
  {
    targetSelector: "[data-tour='war-room']",
    title: "Revenue war room",
    description: "For accounts that remain blocked, escalate to the War Room. CS, Sales, Finance, and SysAdmin each get a checklist. Check off tasks as a team.",
    position: "right",
  },
];

interface Props {
  steps: TourStep[];
  onComplete: () => void;
}

export function GuidedTour({ steps, onComplete }: Props) {
  const [currentStep, setCurrentStep] = useState(0);
  const [spotlight, setSpotlight] = useState<DOMRect | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ top: 0, left: 0 });
  const overlayRef = useRef<HTMLDivElement>(null);

  const PADDING = 8;
  const TOOLTIP_W = 320;
  const TOOLTIP_H = 160;

  useEffect(() => {
    const step = steps[currentStep];
    const el = document.querySelector(step.targetSelector) as HTMLElement | null;
    if (!el) {
      // If the target element isn't on the current screen, wait or skip step
      // In a multi-page app, the user might need to navigate or we can skip
      return;
    }

    el.scrollIntoView({ behavior: "smooth", block: "center" });

    const update = () => {
      const rect = el.getBoundingClientRect();
      setSpotlight(rect);

      const vw = window.innerWidth;
      const vh = window.innerHeight;
      let top = 0;
      let left = rect.left + rect.width / 2 - TOOLTIP_W / 2;

      if (step.position === "bottom") {
        top = rect.bottom + PADDING + 12;
      } else if (step.position === "top") {
        top = rect.top - TOOLTIP_H - PADDING - 12;
      } else if (step.position === "right") {
        top = rect.top + rect.height / 2 - TOOLTIP_H / 2;
        left = rect.right + PADDING + 12;
      } else {
        top = rect.top + rect.height / 2 - TOOLTIP_H / 2;
        left = rect.left - TOOLTIP_W - PADDING - 12;
      }

      // Clamp to viewport
      left = Math.max(12, Math.min(left, vw - TOOLTIP_W - 12));
      top = Math.max(12, Math.min(top, vh - TOOLTIP_H - 12));
      setTooltipPos({ top, left });
    };

    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, [currentStep, steps]);

  const next = () => {
    if (currentStep < steps.length - 1) setCurrentStep((s) => s + 1);
    else onComplete();
  };

  const skip = () => onComplete();

  const step = steps[currentStep];

  // Spotlight cutout via clip-path polygon (window with hole)
  const getClipPath = (rect: DOMRect) => {
    const p = PADDING;
    const x1 = rect.left - p;
    const y1 = rect.top - p;
    const x2 = rect.right + p;
    const y2 = rect.bottom + p;
    return `polygon(
      0% 0%, 100% 0%, 100% 100%, 0% 100%,
      0% ${y1}px, ${x1}px ${y1}px, ${x1}px ${y2}px, ${x2}px ${y2}px,
      ${x2}px ${y1}px, 0% ${y1}px, 0% 0%
    )`;
  };

  return (
    <div ref={overlayRef} style={{ position: "fixed", inset: 0, zIndex: 9999, pointerEvents: "none" }}>
      {/* Dark overlay with spotlight cutout */}
      {spotlight && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.6)",
            clipPath: getClipPath(spotlight),
            pointerEvents: "all",
            cursor: "default",
          }}
          onClick={skip}
        />
      )}

      {/* Spotlight border ring */}
      {spotlight && (
        <div
          style={{
            position: "fixed",
            top: spotlight.top - PADDING,
            left: spotlight.left - PADDING,
            width: spotlight.width + PADDING * 2,
            height: spotlight.height + PADDING * 2,
            border: "2px solid #60A5FA",
            borderRadius: 8,
            boxSizing: "border-box",
            pointerEvents: "none",
            transition: "all 0.25s ease",
          }}
        />
      )}

      {/* Tooltip card */}
      <div
        style={{
          position: "fixed",
          top: tooltipPos.top,
          left: tooltipPos.left,
          width: TOOLTIP_W,
          background: "#fff",
          color: "#000",
          borderRadius: 12,
          border: "0.5px solid rgba(0,0,0,0.12)",
          padding: "16px 20px",
          boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
          pointerEvents: "all",
          zIndex: 10000,
          transition: "top 0.25s ease, left 0.25s ease",
        }}
      >
        {/* Step counter */}
        <p style={{ margin: "0 0 6px", fontSize: 12, color: "#6B7280", fontWeight: 500 }}>
          Step {currentStep + 1} of {steps.length}
        </p>

        {/* Progress bar */}
        <div style={{ height: 3, background: "#E5E7EB", borderRadius: 2, marginBottom: 12 }}>
          <div
            style={{
              height: "100%",
              width: `${((currentStep + 1) / steps.length) * 100}%`,
              background: "#3B82F6",
              borderRadius: 2,
              transition: "width 0.3s ease",
            }}
          />
        </div>

        <p style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 600, color: "#111827" }}>
          {step.title}
        </p>
        <p style={{ margin: "0 0 16px", fontSize: 14, color: "#4B5563", lineHeight: 1.5 }}>
          {step.description}
        </p>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <button
            onClick={skip}
            style={{
              background: "none",
              border: "none",
              fontSize: 13,
              color: "#9CA3AF",
              cursor: "pointer",
              padding: 0,
            }}
          >
            Skip tour
          </button>
          <button
            onClick={next}
            style={{
              background: "#3B82F6",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "8px 18px",
              fontSize: 14,
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            {currentStep === steps.length - 1 ? "Finish" : "Next →"}
          </button>
        </div>
      </div>
    </div>
  );
}
