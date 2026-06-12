import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.models import Customer, Contract, Invoice, SupportTicket, RevenueCrisisAlert

class RevenueCrisisAgent(BaseAgent):
    """
    Agent: Revenue Crisis Agent
    Runs portfolio-wide analysis to detect billing complaint spikes, support issue spikes,
    renewal risk spikes, and churn clusters. Generates and stores alerts in database.
    """

    @property
    def name(self) -> str:
        return "RevenueCrisisAgent"

    def run(self, db: Session, organization_id: int, **kwargs) -> List[RevenueCrisisAlert]:
        print(f"RevenueCrisisAgent: Running portfolio diagnostics for Org ID: {organization_id}...")
        
        # 1. Clear existing alerts to prevent duplication
        db.query(RevenueCrisisAlert).filter(RevenueCrisisAlert.organization_id == organization_id).delete()
        db.commit()

        alerts_to_add = []
        
        # Fetch organization data
        customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
        if not customers:
            return []
            
        cust_ids = [c.id for c in customers]
        invoices = db.query(Invoice).filter(Invoice.customer_id.in_(cust_ids)).all()
        contracts = db.query(Contract).filter(Contract.customer_id.in_(cust_ids)).all()
        tickets = db.query(SupportTicket).filter(SupportTicket.customer_id.in_(cust_ids)).all()

        # ----------------------------------------------------
        # DIAGNOSTIC 1: Billing Complaint & Invoice Delays Spike
        # ----------------------------------------------------
        overdue_invoices = [i for i in invoices if i.status == "Overdue"]
        if len(overdue_invoices) >= 8:
            potential_loss = sum(c.revenue_at_risk for c in customers if any(i.customer_id == c.id for i in overdue_invoices))
            total_overdue_val = sum(i.amount for i in overdue_invoices)
            
            alerts_to_add.append(RevenueCrisisAlert(
                organization_id=organization_id,
                title="Systemic Invoice Collections Delays",
                severity="HIGH" if total_overdue_val > 50000 else "MEDIUM",
                potential_revenue_loss=round(potential_loss, 2),
                root_cause="Increase in billing complaints and unpaid invoicing among enterprise accounts.",
                confidence=0.91,
                description=(
                    f"Identified {len(overdue_invoices)} overdue invoices outstanding, "
                    f"amounting to a collection backlog of ${total_overdue_val:,.2f}. "
                    f"Late payments are impacting key customer relationship scores."
                )
            ))

        # ----------------------------------------------------
        # DIAGNOSTIC 2: Technical Support Tickets backlog
        # ----------------------------------------------------
        open_tickets = [t for t in tickets if t.status != "Resolved"]
        high_priority_open = [t for t in open_tickets if t.priority == "High"]
        
        if len(high_priority_open) >= 5 or len(open_tickets) >= 30:
            potential_loss = sum(c.revenue_at_risk for c in customers if any(t.customer_id == c.id for t in high_priority_open))
            
            alerts_to_add.append(RevenueCrisisAlert(
                organization_id=organization_id,
                title="Critical Support Escalations Backlog",
                severity="CRITICAL" if len(high_priority_open) >= 10 else "HIGH",
                potential_revenue_loss=round(potential_loss, 2),
                root_cause="Spike in high priority technical support ticket queues on key client accounts.",
                confidence=0.88,
                description=(
                    f"Customer support queues are under heavy load with {len(open_tickets)} open tickets, "
                    f"including {len(high_priority_open)} unresolved High Priority cases. "
                    f"Resolution latencies are degrading customer health scores."
                )
            ))

        # ----------------------------------------------------
        # DIAGNOSTIC 3: Contract Renewal Risks
        # ----------------------------------------------------
        now = datetime.datetime.utcnow()
        sixty_days_hence = now + datetime.timedelta(days=60)
        imminent_contracts = [
            c for c in contracts 
            if c.status == "Active" and c.end_date <= sixty_days_hence
        ]
        
        high_risk_imminent = [
            c for c in imminent_contracts 
            if db.query(Customer.risk_level).filter(Customer.id == c.customer_id).scalar() in ("High", "Medium")
        ]
        
        if len(high_risk_imminent) >= 3:
            potential_loss = sum(c.value for c in imminent_contracts if db.query(Customer.risk_level).filter(Customer.id == c.customer_id).scalar() in ("High", "Medium"))
            
            alerts_to_add.append(RevenueCrisisAlert(
                organization_id=organization_id,
                title="Upcoming High-Risk Renewal Deadlines",
                severity="CRITICAL",
                potential_revenue_loss=round(potential_loss, 2),
                root_cause="High-value enterprise agreements expiring within 60 days with unresolved risk factors.",
                confidence=0.95,
                description=(
                    f"Found {len(imminent_contracts)} contracts expiring within the 60-day renewal window. "
                    f"Specifically, {len(high_risk_imminent)} high-value accounts show active churn indicators, "
                    f"posing a severe renewal attrition threat."
                )
            ))

        # ----------------------------------------------------
        # DIAGNOSTIC 4: Industry-Level Churn Clusters
        # ----------------------------------------------------
        industry_groups = {}
        for c in customers:
            if c.industry:
                if c.industry not in industry_groups:
                    industry_groups[c.industry] = []
                industry_groups[c.industry].append(c)

        for industry, Group in industry_groups.items():
            high_count = len([c for c in Group if c.risk_level == "High"])
            pct = (high_count / len(Group)) * 100
            
            if pct >= 25.0 and len(Group) >= 5:  # Over 25% High Risk in an industry with at least 5 accounts
                potential_loss = sum(c.revenue_at_risk for c in Group if c.risk_level == "High")
                
                alerts_to_add.append(RevenueCrisisAlert(
                    organization_id=organization_id,
                    title=f"Stressed Cluster: {industry} Sector",
                    severity="HIGH" if potential_loss > 100000 else "MEDIUM",
                    potential_revenue_loss=round(potential_loss, 2),
                    root_cause=f"Systemic risk cluster identified in the {industry} sector.",
                    confidence=0.85,
                    description=(
                        f"A churn cluster alert was generated for the '{industry}' industry vertical. "
                        f"Currently, {pct:.1f}% of accounts ({high_count} clients) in this sector "
                        f"display high risk parameters, indicating potential industry-specific headwinds."
                    )
                ))

        # ----------------------------------------------------
        # FALLBACK: Create a low-level status alert if no crisis
        # ----------------------------------------------------
        if not alerts_to_add:
            alerts_to_add.append(RevenueCrisisAlert(
                organization_id=organization_id,
                title="System Operational Status Normal",
                severity="LOW",
                potential_revenue_loss=0.0,
                root_cause="Client metrics, billing records, and support SLAs reside in standard parameters.",
                confidence=0.99,
                description="The portfolio-wide diagnostic engine detected no active revenue risk crises."
            ))

        # Add to DB
        for alert in alerts_to_add:
            db.add(alert)
        db.commit()

        print(f"RevenueCrisisAgent: Diagnostics finished. Generated {len(alerts_to_add)} alert(s).")
        return alerts_to_add

revenue_crisis_agent = RevenueCrisisAgent()
