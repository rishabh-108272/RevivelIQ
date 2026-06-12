from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.models import Customer, Recommendation, Contract, Invoice, SupportTicket, Email

class RevenueRecoveryAgent(BaseAgent):
    """
    Agent 5: Revenue Recovery Agent
    Evaluates individual customer risk indicators and generates actionable recommendations
    with detailed Revenue Impact Estimation (Gross Value, Execution Cost, Net Recovery).
    Outputs: List of generated Recommendation objects stored in the DB.
    """
    
    @property
    def name(self) -> str:
        return "RevenueRecoveryAgent"
        
    def run(self, db: Session, customer_id: int, **kwargs) -> Dict[str, Any]:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"recommendations_generated": 0, "explanation": "Customer not found."}
            
        # Clear existing pending recommendations to prevent duplication
        db.query(Recommendation).filter(
            Recommendation.customer_id == customer_id,
            Recommendation.status == "Pending"
        ).delete()
        
        recs_to_add = []
        
        # Gather context
        contracts = db.query(Contract).filter(Contract.customer_id == customer_id).all()
        invoices = db.query(Invoice).filter(Invoice.customer_id == customer_id).all()
        tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == customer_id).all()
        
        overdue_invoices = [i for i in invoices if i.status == "Overdue"]
        open_tickets = [t for t in tickets if t.status != "Resolved"]
        high_priority_open_tickets = [t for t in open_tickets if t.priority == "High"]
        
        # 1. Action Rule: Contract Renewal Risk (Contract Expiration close)
        active_contracts = [c for c in contracts if c.status == "Active"]
        if active_contracts:
            next_expiring = min(active_contracts, key=lambda c: c.end_date)
            remaining_days = (next_expiring.end_date - datetime.datetime.utcnow()).days
            
            if remaining_days <= 90 and customer.risk_level in ("High", "Medium"):
                # Recommend renewal incentive
                discount_percentage = 0.15 if customer.risk_level == "High" else 0.10
                discount_val = next_expiring.value * discount_percentage
                
                # Revenue Impact calculations
                gross_impact = next_expiring.value
                cost = discount_val + 500.0  # discount cost + administrative labor
                net_recovery = gross_impact - cost
                
                recs_to_add.append(Recommendation(
                    customer_id=customer_id,
                    title="Offer Renewal Incentive & Rate Discount",
                    description=(
                        f"Prepare a renegotiation term sheet offering a {int(discount_percentage * 100)}% "
                        f"discount (${discount_val:,.2f}) on the contract renewal for '{next_expiring.title}' "
                        f"which expires in {remaining_days} days."
                    ),
                    action_type="Discount",
                    priority="High" if customer.risk_level == "High" else "Medium",
                    status="Pending",
                    revenue_impact_estimate=gross_impact,
                    cost_to_execute=cost,
                    net_recovery_value=net_recovery,
                    impact_projection=(
                        f"Secures the renewal window of ${next_expiring.value:,.2f} contract value, "
                        f"offsetting competitor migration incentives by conceding a temporary margin adjustment."
                    )
                ))
                
        # 2. Action Rule: Overdue Invoice Payments
        if overdue_invoices:
            total_overdue = sum(inv.amount for inv in overdue_invoices)
            
            # Revenue Impact calculations
            gross_impact = total_overdue
            cost = 350.0  # accounts receivable outreach time
            net_recovery = gross_impact - cost
            
            recs_to_add.append(Recommendation(
                customer_id=customer_id,
                title="Initiate Priority Collections & Billing Mediation",
                description=(
                    f"Outreach to billing administrators regarding {len(overdue_invoices)} overdue "
                    f"invoice(s) totalling ${total_overdue:,.2f}. Establish a standard payment timeline "
                    "or escalate to mediation."
                ),
                action_type="Priority Outreach",
                priority="High" if total_overdue > 10000 else "Medium",
                status="Pending",
                revenue_impact_estimate=gross_impact,
                cost_to_execute=cost,
                net_recovery_value=net_recovery,
                impact_projection=(
                    f"Recovers ${total_overdue:,.2f} in outstanding receivables, restoring accounts "
                    "receivable cash flow cycles and resolving administrative billing blocks."
                )
            ))
            
        # 3. Action Rule: Unresolved High Priority support tickets
        if high_priority_open_tickets:
            # Revenue Impact calculations
            gross_impact = customer.revenue * 0.25  # Assumed 25% of account revenue protected by tech health
            cost = 1200.0  # Engineering specialized hours
            net_recovery = gross_impact - cost
            
            recs_to_add.append(Recommendation(
                customer_id=customer_id,
                title="Escalate Critical Support Tickets & Assign Engineering Owner",
                description=(
                    f"Escalate {len(high_priority_open_tickets)} unresolved High Priority support ticket(s) "
                    "to engineering leads. Establish a daily update status review with customer stakeholders."
                ),
                action_type="Support",
                priority="High",
                status="Pending",
                revenue_impact_estimate=gross_impact,
                cost_to_execute=cost,
                net_recovery_value=net_recovery,
                impact_projection=(
                    "Restores technical platform reliability trust and addresses functional system blockers, "
                    "preventing reactive contract cancellations due to quality of service."
                )
            ))
            
        # 4. Action Rule: Low Collaboration index (Work IQ gap)
        if len(recs_to_add) == 0 or customer.risk_level in ("High", "Medium"):
            # Recommend an executive review
            gross_impact = customer.revenue * 0.15  # protects 15% account value by re-engaging
            cost = 250.0
            net_recovery = gross_impact - cost
            
            recs_to_add.append(Recommendation(
                customer_id=customer_id,
                title="Schedule Strategic Executive Review (QBR)",
                description=(
                    f"Arrange an Executive Alignment briefing with stakeholders at {customer.name} "
                    "to review platform utilization and check feedback alignment."
                ),
                action_type="Review",
                priority="Medium",
                status="Pending",
                revenue_impact_estimate=gross_impact,
                cost_to_execute=cost,
                net_recovery_value=net_recovery,
                impact_projection=(
                    "Re-establishes key corporate touchpoints and identifies client objectives, "
                    "mitigating relationship silence risks before renewal negotiation cycles."
                )
            ))
            
        for rec in recs_to_add:
            db.add(rec)
            
        db.commit()
        return {
            "recommendations_generated": len(recs_to_add),
            "explanation": f"Generated {len(recs_to_add)} prioritized recovery recommendations for {customer.name}."
        }

import datetime  # Import here inside module file to prevent import dependencies crashes
recovery_agent = RevenueRecoveryAgent()
