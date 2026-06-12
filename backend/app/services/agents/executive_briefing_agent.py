import datetime
from typing import Dict, Any, List
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.models import Customer, SupportTicket, Invoice

class ExecutiveBriefingAgent(BaseAgent):
    """
    Agent 6: Executive Briefing Agent
    Synthesizes portfolio-wide statistics, identifies industry sectors under stress,
    aggregates high-value accounts at risk, and writes a narrative markdown briefing.
    Outputs: Narrative summary text, list of top risk accounts, and macro trends list.
    """
    
    @property
    def name(self) -> str:
        return "ExecutiveBriefingAgent"
        
    def run(self, db: Session, organization_id: int, **kwargs) -> Dict[str, Any]:
        # Get all customers for organization
        customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
        
        if not customers:
            return {
                "generated_at": datetime.datetime.utcnow().isoformat(),
                "narrative": "No customer data available to synthesize an executive briefing. Please seed the system database.",
                "top_accounts_at_risk": [],
                "macro_trends": []
            }
            
        total_rev_at_risk = sum(c.revenue_at_risk for c in customers)
        high_risk_customers = [c for c in customers if c.risk_level == "High"]
        med_risk_customers = [c for c in customers if c.risk_level == "Medium"]
        
        # Sort by revenue at risk descending
        top_risk_accounts = sorted(customers, key=lambda c: c.revenue_at_risk, reverse=True)[:5]
        
        # Analyze Sector Trends
        industry_risk = {}
        for c in customers:
            if c.industry:
                if c.industry not in industry_risk:
                    industry_risk[c.industry] = {"total_revenue": 0.0, "at_risk": 0.0, "count": 0}
                industry_risk[c.industry]["total_revenue"] += c.revenue
                industry_risk[c.industry]["at_risk"] += c.revenue_at_risk
                industry_risk[c.industry]["count"] += 1
                
        stressed_sectors = []
        for ind, stats in industry_risk.items():
            ratio = stats["at_risk"] / stats["total_revenue"] if stats["total_revenue"] > 0 else 0
            if ratio > 0.15:  # Over 15% revenue at risk in this sector
                stressed_sectors.append((ind, ratio, stats["at_risk"]))
                
        # Sort sectors by risk value
        stressed_sectors = sorted(stressed_sectors, key=lambda x: x[2], reverse=True)
        
        # Identify macro operational trends
        macro_trends = []
        if stressed_sectors:
            top_stressed = stressed_sectors[0]
            macro_trends.append(
                f"**Industry Stress**: The **{top_stressed[0]}** sector is experiencing the highest risk rate, "
                f"with {int(top_stressed[1] * 100)}% of its portfolio revenue (${top_stressed[2]:,.2f}) flagged as vulnerable."
            )
            
        # Count overdue invoice issues portfolio-wide
        overdue_invoices_count = db.query(Invoice).filter(Invoice.status == "Overdue").count()
        if overdue_invoices_count > 10:
            macro_trends.append(
                f"**Billing Delays**: Portfolio-wide accounts receivable delays are highly active, with **{overdue_invoices_count} past due invoices** outstanding. This indicates a potential systemic administrative lag in collections."
            )
            
        # Count open tickets
        open_tickets_count = db.query(SupportTicket).filter(SupportTicket.status != "Resolved").count()
        if open_tickets_count > 50:
            macro_trends.append(
                f"**Service Backlog**: Customer Support queue pressure is elevated with **{open_tickets_count} unresolved tickets**. Support latency is negatively impacting client satisfaction indices across mid-market accounts."
            )
            
        if not macro_trends:
            macro_trends.append("No major operational risk trends detected. Client portfolio performance indicators are stable.")
            
        # Build Markdown Executive Narrative
        date_str = datetime.datetime.utcnow().strftime("%B %d, %Y")
        
        narrative = (
            f"# ReviveIQ Executive Revenue Intelligence Briefing\n"
            f"**Generated on**: {date_str} | **Scope**: Active Client Portfolios\n\n"
            f"## Executive Summary\n"
            f"As of today, the total active revenue exposure stands at **${total_rev_at_risk:,.2f}** "
            f"across the enterprise client portfolio. There are **{len(high_risk_customers)} accounts** flagged with "
            f"High churn probability and **{len(med_risk_customers)} accounts** at Medium risk level.\n\n"
            f"Immediate intervention is recommended on high-exposure accounts to secure upcoming contract renewal cycles "
            f"and clear outstanding collections backlogs.\n\n"
            f"## Strategic Macro Trends\n"
        )
        
        for trend in macro_trends:
            narrative += f"- {trend}\n"
            
        narrative += "\n## Key Accounts Requiring Immediate Outreach\n"
        for idx, acc in enumerate(top_risk_accounts[:3]):
            narrative += (
                f"{idx+1}. **{acc.name}** ({acc.industry or 'Unknown'})\n"
                f"   - **Revenue Exposure**: ${acc.revenue_at_risk:,.2f} (Churn Prob: {int(acc.churn_probability * 100)}%)\n"
                f"   - **Primary Factor**: "
            )
            # Add details on the main factor
            if acc.churn_probability > 0.6:
                narrative += "Critical combo of upcoming renewal (< 45 days) and unresolved billing disputes.\n"
            else:
                narrative += "Customer relationship shows silence gaps and declining communication sentiment.\n"
                
        narrative += (
            "\n## Action Recommendation Summary\n"
            "1. **Deploy discounts/incentives** for high-risk accounts expiring this quarter.\n"
            "2. **Escalate billing mediation** for invoices overdue by more than 30 days.\n"
            "3. **Assign engineering leads** to clear technical support ticket backlogs on stressed accounts."
        )
        
        return {
            "generated_at": datetime.datetime.utcnow(),
            "narrative": narrative,
            "top_accounts_at_risk": [
                {
                    "id": c.id,
                    "name": c.name,
                    "industry": c.industry,
                    "revenue_at_risk": c.revenue_at_risk,
                    "risk_level": c.risk_level,
                    "churn_probability": c.churn_probability
                }
                for c in top_risk_accounts
            ],
            "macro_trends": macro_trends
        }

executive_briefing_agent = ExecutiveBriefingAgent()
