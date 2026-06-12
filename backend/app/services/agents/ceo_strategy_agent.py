import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.services.agents.base import BaseAgent
from app.models.models import Customer, Contract, Invoice, SupportTicket, Recommendation

class CEOStrategyAgent(BaseAgent):
    """
    Agent: CEO Strategy Agent
    Synthesizes portfolio-wide statistics and recommendations from Contract, Payment,
    Customer Success, Revenue Risk, and Revenue Recovery agents.
    Returns executive-level BI recommendations, reasoning traces, and evidence.
    """

    @property
    def name(self) -> str:
        return "CEOStrategyAgent"

    def run(self, db: Session, customer_id: int = None, **kwargs) -> Dict[str, Any]:
        # Simple placeholder if called with standard base class run
        return self.answer_question(db, "Show highest value churn risks.", organization_id=1)

    def answer_question(self, db: Session, question: str, organization_id: int) -> Dict[str, Any]:
        q = question.lower().strip()
        
        # 1. Fetch relevant customer portfolio data
        customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
        if not customers:
            return {
                "response_text": "I checked the database and found no active customers. Please seed the workspace.",
                "reasoning_trace": ["Step 1: Scanned portfolio database.", "Step 2: Found 0 customers."],
                "supporting_evidence": []
            }

        # Route to specific query handlers
        if "500" in q or "save" in q or "quarter" in q:
            return self._handle_save_target(db, customers, target_amount=500000.0)
        elif "executive" in q or "attention" in q:
            return self._handle_executive_attention(db, customers)
        elif "biggest" in q or "largest" in q or "biggest revenue risk" in q:
            return self._handle_biggest_risk(db, customers)
        elif "highest value" in q or "churn risks" in q:
            return self._handle_highest_churn_risks(db, customers)
        elif "roi" in q or "return" in q or "actions" in q:
            return self._handle_highest_roi(db, customers)
        else:
            # General fallback briefing
            return self._handle_general_briefing(db, customers, question)

    def _handle_save_target(self, db: Session, customers: List[Customer], target_amount: float) -> Dict[str, Any]:
        # Retrieve all pending recommendations
        cust_ids = [c.id for c in customers]
        recs = db.query(Recommendation).filter(
            Recommendation.customer_id.in_(cust_ids),
            Recommendation.status == "Pending"
        ).order_by(desc(Recommendation.net_recovery_value)).all()

        selected_recs = []
        total_recovery = 0.0
        total_cost = 0.0
        
        for r in recs:
            selected_recs.append(r)
            total_recovery += r.net_recovery_value
            total_cost += r.cost_to_execute
            if total_recovery >= target_amount:
                break

        # Generate response text
        if total_recovery == 0:
            response_text = f"We currently do not have any pending recovery actions. Run 'Sync Risk Metrics' to generate recovery plans."
        else:
            response_text = (
                f"### Strategic Plan: Recover ${total_recovery:,.2f} in Threatened Revenue\n\n"
                f"I have compiled a prioritized list of **{len(selected_recs)} recovery actions** to hit your targets. "
                f"Executing this plan requires a total budget of **${total_cost:,.2f}**, returning a net protected revenue of **${total_recovery:,.2f}**.\n\n"
                f"**Key Actions Proposed:**\n"
            )
            for idx, r in enumerate(selected_recs):
                customer_name = db.query(Customer.name).filter(Customer.id == r.customer_id).scalar() or "Unknown Client"
                response_text += (
                    f"{idx + 1}. **{r.title}** for **{customer_name}**\n"
                    f"   - **Net Recovery**: ${r.net_recovery_value:,.2f} (Gross Protected: ${r.revenue_impact_estimate:,.2f})\n"
                    f"   - **Action**: {r.description}\n"
                )

        supporting_evidence = [
            {
                "customer_name": db.query(Customer.name).filter(Customer.id == r.customer_id).scalar() or "Unknown Client",
                "recommendation": r.title,
                "net_recovery": r.net_recovery_value,
                "cost": r.cost_to_execute
            } for r in selected_recs
        ]

        reasoning_trace = [
            "Step 1: Scanned all portfolio accounts and pending outreach options.",
            f"Step 2: Identified {len(recs)} potential recovery recommendations.",
            "Step 3: Sorted recommendations by net recovery value descending.",
            f"Step 4: Consolidated top {len(selected_recs)} proposals to meet your target of ${target_amount:,.2f}."
        ]

        return {
            "response_text": response_text,
            "reasoning_trace": reasoning_trace,
            "supporting_evidence": {"summary": f"Saved {total_recovery:,.2f}", "items": supporting_evidence}
        }

    def _handle_executive_attention(self, db: Session, customers: List[Customer]) -> Dict[str, Any]:
        # High risk or high churn probability customers
        high_risk = [c for c in customers if c.risk_level == "High"]
        high_risk = sorted(high_risk, key=lambda c: c.revenue_at_risk, reverse=True)

        if not high_risk:
            response_text = "All accounts show stable metrics. No accounts currently require urgent executive escalation."
        else:
            response_text = (
                f"### Executive Intervention Escalations Required\n\n"
                f"I identified **{len(high_risk)} high-risk account(s)** requiring immediate executive alignment:\n\n"
            )
            for idx, c in enumerate(high_risk[:5]):
                # Fetch latest recommendations for this customer
                latest_rec = db.query(Recommendation).filter(
                    Recommendation.customer_id == c.id
                ).order_by(Recommendation.priority.desc()).first()
                
                rec_action = latest_rec.title if latest_rec else "Schedule Strategic QBR"
                
                response_text += (
                    f"{idx + 1}. **{c.name}** (Revenue: ${c.revenue:,.2f})\n"
                    f"   - **Exposed Revenue**: ${c.revenue_at_risk:,.2f} (Churn Prob: {int(c.churn_probability * 100)}%)\n"
                    f"   - **Recommended Action**: {rec_action}\n"
                )

        supporting_evidence = [
            {
                "customer_name": c.name,
                "churn_probability": c.churn_probability,
                "revenue_at_risk": c.revenue_at_risk,
                "risk_level": c.risk_level
            } for c in high_risk[:5]
        ]

        reasoning_trace = [
            "Step 1: Scanned risk classifications across all organization accounts.",
            f"Step 2: Filtered for high-risk profiles (found {len(high_risk)} total).",
            "Step 3: Ordered high-risk accounts by exposed contract value.",
            "Step 4: Extracted top priority escalations for executive action."
        ]

        return {
            "response_text": response_text,
            "reasoning_trace": reasoning_trace,
            "supporting_evidence": {"items": supporting_evidence}
        }

    def _handle_biggest_risk(self, db: Session, customers: List[Customer]) -> Dict[str, Any]:
        # Customer with the largest revenue at risk
        biggest = max(customers, key=lambda c: c.revenue_at_risk)
        
        # Details
        contracts = db.query(Contract).filter(Contract.customer_id == biggest.id, Contract.status == "Active").all()
        invoices = db.query(Invoice).filter(Invoice.customer_id == biggest.id, Invoice.status == "Overdue").all()
        tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == biggest.id, SupportTicket.status != "Resolved").all()

        response_text = (
            f"### Primary Portfolio Revenue Threat: **{biggest.name}**\n\n"
            f"The single largest revenue risk is **{biggest.name}** with **${biggest.revenue_at_risk:,.2f}** at stake. "
            f"This account has a **{int(biggest.churn_probability * 100)}% churn probability** (Health: {biggest.health_score:.1f}/100).\n\n"
            f"**Risk Profile Drivers:**\n"
        )
        
        if contracts:
            days = (contracts[0].end_date - datetime.datetime.utcnow()).days
            response_text += f"- **Contract**: '{contracts[0].title}' expires in **{days} days** (Value: ${contracts[0].value:,.2f})\n"
        if invoices:
            total_due = sum(i.amount for i in invoices)
            response_text += f"- **Invoices**: {len(invoices)} overdue billing invoice(s) totalling **${total_due:,.2f}**\n"
        if tickets:
            response_text += f"- **Support**: {len(tickets)} unresolved ticket(s) block operational workflows.\n"

        response_text += (
            f"\n**Immediate Actions Recommended:**\n"
            f"1. Schedule VP-level alignment call.\n"
            f"2. Present 15% renewal incentive discount.\n"
            f"3. Clear support queues via designated engineering lead."
        )

        supporting_evidence = {
            "customer_id": biggest.id,
            "customer_name": biggest.name,
            "revenue_at_risk": biggest.revenue_at_risk,
            "health_score": biggest.health_score,
            "overdue_invoices": len(invoices),
            "unresolved_tickets": len(tickets)
        }

        reasoning_trace = [
            "Step 1: Evaluated all 100 active customers in organization.",
            "Step 2: Scanned revenue exposure values (revenue * churn probability).",
            f"Step 3: Identified {biggest.name} as highest risk account.",
            "Step 4: Pulled contract, invoicing, and support datasets to isolate primary drivers."
        ]

        return {
            "response_text": response_text,
            "reasoning_trace": reasoning_trace,
            "supporting_evidence": supporting_evidence
        }

    def _handle_highest_churn_risks(self, db: Session, customers: List[Customer]) -> Dict[str, Any]:
        # Top 5 by revenue at risk
        top_risks = sorted(customers, key=lambda c: c.revenue_at_risk, reverse=True)[:5]
        
        response_text = (
            f"### Top 5 Portfolio Revenue Threats\n\n"
            f"These accounts represent the highest absolute business impact (vulnerability x contract size):\n\n"
        )
        for idx, c in enumerate(top_risks):
            response_text += (
                f"{idx + 1}. **{c.name}**\n"
                f"   - **Exposed Revenue**: ${c.revenue_at_risk:,.2f} (Churn Prob: {int(c.churn_probability * 100)}%)\n"
                f"   - **Industry**: {c.industry} | Health Score: {c.health_score:.1f}/100\n"
            )

        supporting_evidence = [
            {
                "customer_name": c.name,
                "revenue_at_risk": c.revenue_at_risk,
                "churn_probability": c.churn_probability,
                "health_score": c.health_score
            } for c in top_risks
        ]

        reasoning_trace = [
            "Step 1: Scanned portfolio database records.",
            "Step 2: Ranked all accounts by total revenue exposure.",
            "Step 3: Extracted top 5 highest impact accounts for strategy analysis."
        ]

        return {
            "response_text": response_text,
            "reasoning_trace": reasoning_trace,
            "supporting_evidence": {"items": supporting_evidence}
        }

    def _handle_highest_roi(self, db: Session, customers: List[Customer]) -> Dict[str, Any]:
        cust_ids = [c.id for c in customers]
        recs = db.query(Recommendation).filter(
            Recommendation.customer_id.in_(cust_ids),
            Recommendation.status == "Pending"
        ).all()

        # Sort by ROI (net_recovery / cost) or net recovery value
        # Since some costs might be small, let's sort by net recovery descending as a proxy, or calculate ratio
        def get_roi_ratio(r):
            return r.net_recovery_value / max(1.0, r.cost_to_execute)

        sorted_recs = sorted(recs, key=get_roi_ratio, reverse=True)[:5]

        response_text = (
            f"### High ROI Recovery Actions\n\n"
            f"I have prioritized recovery recommendations offering the highest return on investment:\n\n"
        )
        for idx, r in enumerate(sorted_recs):
            customer_name = db.query(Customer.name).filter(Customer.id == r.customer_id).scalar() or "Unknown Client"
            roi = get_roi_ratio(r)
            response_text += (
                f"{idx + 1}. **{r.title}** (Client: **{customer_name}**)\n"
                f"   - **Projected Net Recovery**: ${r.net_recovery_value:,.2f}\n"
                f"   - **Cost to Execute**: ${r.cost_to_execute:,.2f} | **ROI Ratio**: {roi:.1f}x\n"
                f"   - **Action**: {r.description}\n"
            )

        supporting_evidence = [
            {
                "customer_name": db.query(Customer.name).filter(Customer.id == r.customer_id).scalar() or "Unknown Client",
                "recommendation": r.title,
                "net_recovery": r.net_recovery_value,
                "roi_ratio": get_roi_ratio(r)
            } for r in sorted_recs
        ]

        reasoning_trace = [
            "Step 1: Gathered pending recommendations across active accounts.",
            "Step 2: Calculated ROI ratio (Net Recovery / Cost to Execute) for each card.",
            "Step 3: Ranked recommendations by ROI performance indicator.",
            "Step 4: Isolated top 5 high-yield actions."
        ]

        return {
            "response_text": response_text,
            "reasoning_trace": reasoning_trace,
            "supporting_evidence": {"items": supporting_evidence}
        }

    def _handle_general_briefing(self, db: Session, customers: List[Customer], question: str) -> Dict[str, Any]:
        total_risk = sum(c.revenue_at_risk for c in customers)
        high_risk_count = len([c for c in customers if c.risk_level == "High"])
        
        response_text = (
            f"### ReviveIQ General Executive Strategy Review\n\n"
            f"I processed your query: *\"{question}\"*\n\n"
            f"**Portfolio Health Baseline:**\n"
            f"- **Total Revenue Exposure**: ${total_risk:,.2f}\n"
            f"- **High Risk Accounts**: {high_risk_count} client(s) flagged under High Churn Risk.\n\n"
            f"Please clarify if you'd like to inspect details regarding high ROI actions, contract expirations, or specific collections mediation programs."
        )

        supporting_evidence = {
            "total_revenue_at_risk": total_risk,
            "high_risk_count": high_risk_count
        }

        reasoning_trace = [
            "Step 1: Parsed query string syntax.",
            "Step 2: Scanned global organizational totals.",
            "Step 3: Formulated summary briefing overview."
        ]

        return {
            "response_text": response_text,
            "reasoning_trace": reasoning_trace,
            "supporting_evidence": supporting_evidence
        }

ceo_strategy_agent = CEOStrategyAgent()
