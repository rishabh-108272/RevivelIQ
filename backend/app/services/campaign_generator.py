import datetime
from sqlalchemy.orm import Session
from app.models.models import Customer, Contract, Invoice, SupportTicket, RevenueRescueCampaign
from app.core.config import settings

def generate_rescue_campaign(db: Session, customer_id: int) -> RevenueRescueCampaign:
    """
    Generates a complete, tailored Revenue Rescue Campaign for a customer and stores it in the database.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return None

    # Clear existing campaign for this customer
    db.query(RevenueRescueCampaign).filter(RevenueRescueCampaign.customer_id == customer_id).delete()
    db.commit()

    # Gather context
    contracts = db.query(Contract).filter(Contract.customer_id == customer_id, Contract.status == "Active").all()
    invoices = db.query(Invoice).filter(Invoice.customer_id == customer_id, Invoice.status == "Overdue").all()
    tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == customer_id, SupportTicket.status != "Resolved").all()

    # 1. Executive escalation recommendation
    executive_rec = (
        f"Escalate relationship status for {customer.name}. Recommend direct alignment outreach by our Executive Sponsor "
        f"to the VP of Procurement at {customer.name} to address outstanding billing disputes and contract renegotiations."
    )

    # 2. Customer success recovery plan
    open_tickets_count = len(tickets)
    if open_tickets_count > 0:
        cs_plan = (
            f"Assign a senior customer success engineer to resolve the {open_tickets_count} pending support ticket(s) "
            f"within a fast-tracked 72-hour window. Establish daily status syncs with their tech lead."
        )
    else:
        cs_plan = (
            f"Establish a proactive technical health check and quarterly business review (QBR) schedule with the client's "
            f"engineering team to increase platform utilization metrics."
        )

    # 3. Finance recovery plan
    if invoices:
        total_overdue = sum(inv.amount for inv in invoices)
        finance_plan = (
            f"Initiate priority collections mediation regarding {len(invoices)} overdue invoice(s) totalling ${total_overdue:,.2f}. "
            f"Propose a structured 45-day payment installment plan and waive any accumulated administrative late fees."
        )
    else:
        finance_plan = (
            "Conduct invoice billing review to verify billing address alignment, invoice dispatch confirmations, "
            "and seat credit application."
        )

    # 4. Renewal strategy
    if contracts:
        contract_title = contracts[0].title
        discount_percentage = 12 if customer.risk_level == "High" else 8
        discount_val = contracts[0].value * (discount_percentage / 100.0)
        renewal_strategy = (
            f"Offer a renegotiated 2-year contract extension for agreement '{contract_title}' "
            f"with a {discount_percentage}% rate discount (${discount_val:,.2f}) to secure the renewal window."
        )
        est_revenue_protected = contracts[0].value
        est_execution_cost = discount_val + 1000.0  # discount cost + administrative labor
    else:
        renewal_strategy = (
            "Offer a renegotiated contract pricing structure with a 5% loyalty discount on future monthly seat licensing."
        )
        est_revenue_protected = customer.revenue
        est_execution_cost = 1500.0

    net_recovery = est_revenue_protected - est_execution_cost

    # 5. Suggested outreach timeline
    outreach_timeline = [
        {
            "step": 1,
            "action": "Executive Alignment",
            "timeframe": "Day 1",
            "description": "Executive sponsor delivers alignment outreach email to the VP of Procurement."
        },
        {
            "step": 2,
            "action": "Technical SLA Triage",
            "timeframe": "Day 3",
            "description": "Designated customer success lead conducts a call to resolve ticket backlog."
        },
        {
            "step": 3,
            "action": "Billing Mediation Call",
            "timeframe": "Day 5",
            "description": "Finance representative holds call to structure overdue invoice installment schedule."
        },
        {
            "step": 4,
            "action": "Renegotiated Contract Delivery",
            "timeframe": "Day 10",
            "description": "Account manager delivers renegotiated contract terms containing renewal discount incentives."
        }
    ]

    campaign = RevenueRescueCampaign(
        customer_id=customer_id,
        executive_recommendation=executive_rec,
        customer_success_plan=cs_plan,
        finance_plan=finance_plan,
        renewal_strategy=renewal_strategy,
        outreach_timeline=outreach_timeline,
        estimated_revenue_protected=round(est_revenue_protected, 2),
        estimated_execution_cost=round(est_execution_cost, 2),
        net_recovery_value=round(net_recovery, 2)
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign
