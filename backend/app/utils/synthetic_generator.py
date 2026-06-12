import random
import datetime
from sqlalchemy.orm import Session
from app.models.models import Customer, Contract, Invoice, Email, Meeting, SupportTicket, RevenueRescueCampaign, RevenueCrisisAlert, RiskAssessment, SimulationResult
from app.services.microsoft_foundry_iq import foundry_iq_adapter

# Seed lists for data realism
INDUSTRIES = ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Energy", "Logistics", "Media"]
COMPANY_SUFFIXES = ["Corp", "Inc", "Systems", "Solutions", "Technologies", "Global", "Group", "Partners"]
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

EMAIL_TEMPLATES_NEGATIVE = [
    ("Unresolved service outages", "Hi CSM team, we are experiencing repeated outages on our production database sync since the update. This is halting our logistics schedules. Can you prioritize this?"),
    ("Billing dispute on user licenses", "Dear accounts team, we were billed for 150 seats this month, but we only have 120 active logins. We are withholding payment of invoice {inv_num} until this is corrected."),
    ("Contract renewal terms conflict", "Hi, we received the contract renewal proposal. The 10% rate hike is unacceptable given the platform downtime we faced in Q3. We are looking at alternative tools if the pricing is non-negotiable."),
    ("Support tickets response delay", "Hello, we opened an urgent ticket 48 hours ago and have had no response. This delay is costing us operational hours. We need an escalation manager immediately.")
]

EMAIL_TEMPLATES_POSITIVE = [
    ("Great execution on API migration", "Hi CS team, just wanted to thank you for the support during our API migration last week. The throughput has doubled and the response times are excellent."),
    ("Product adoption review notes", "Hi, our teams have adopted the dashboard tool successfully. We've seen a 30% increase in weekly active users. Looking forward to discussing scale expansions next quarter."),
    ("Invoice confirmation", "Hi billing, we have approved the payment for the latest invoice. The wire transfer should hit your account in 2 business days. Thanks."),
    ("Strategic planning sync request", "Hello, we are planning our tech roadmap for next fiscal year and want to see how we can expand our licensing scope with you. Let's schedule a meeting next week.")
]

EMAIL_TEMPLATES_NEUTRAL = [
    ("Monthly adoption report delivery", "Please find attached our monthly export log for user logins and report generations. Everything is running within normal parameters."),
    ("Schedule update request", "Hi, can we reschedule our upcoming sync to Thursday at 2 PM instead? Some of our engineering leads have a conflict. Thanks."),
    ("Query regarding standard APIs", "Hello, does the enterprise API support webhooks for user group updates? Please point me to the relevant developer guides.")
]

TICKET_TEMPLATES = [
    ("Billing: Overcharge on subscription", "The invoice shows charges for premium support package which we did not opt for. Please refund.", "Billing", "High", -0.5),
    ("System: Integration sync error", "The CRM data connector is throwing a token timeout exception. High frequency logs failure.", "System", "High", -0.7),
    ("UI: Button alignment off in Safari", "On Safari, the export table button overlays the filter input. Low priority layout bug.", "UI", "Low", -0.1),
    ("API: Webhook latency issue", "Webhook events for contract signatures are taking up to 45 seconds to deliver. Needs latency optimization.", "API", "Medium", -0.4),
    ("Access: SSO Login Failures", "Users cannot login via Azure SSO wrapper. Getting redirected to login failures loop.", "Access", "High", -0.8),
    ("General: Documentation request", "Where is the API reference for the bulk uploads schema? Link is missing in developer hub.", "Docs", "Low", 0.0),
    ("Reporting: CSV Export fails", "When exporting records over 10k lines, the server yields a 504 Gateway Timeout.", "Reporting", "Medium", -0.3),
    ("Integration: Teams integration down", "The Microsoft Teams bot connector fails to send alerts on customer risk updates.", "SSO", "Medium", -0.4)
]

MEETING_TEMPLATES = [
    ("Monthly Technical Status Review", "Reviewed core product integration status. Resolved CRM sync bugs. Client requested status updates on their feature requests.", 0.2),
    ("Contract Renewal and Growth Alignment", "Discussed renewal timeline. Customer raised concerns about budget cuts and requested a 15% rate discount to continue.", -0.3),
    ("Billing Dispute Mediation Sync", "Aligned on license discrepancy count. Agreed to reissue invoice with adjusted credits. Customer will clear payment upon receipt.", 0.1),
    ("Quarterly Business Review - Adoption", "Presented user adoption slides. Client was highly impressed by the 40% adoption hike in Sales division. Discussed future roadmap.", 0.8)
]

def clear_synthetic_data(db: Session, organization_id: int):
    """Clears existing customers, invoices, contracts, support tickets, emails, meetings, campaigns, and alerts."""
    customer_ids = [c.id for c in db.query(Customer).filter(Customer.organization_id == organization_id).all()]
    # Clear organization alerts
    db.query(RevenueCrisisAlert).filter(RevenueCrisisAlert.organization_id == organization_id).delete(synchronize_session=False)
    if customer_ids:
        db.query(RevenueRescueCampaign).filter(RevenueRescueCampaign.customer_id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(RiskAssessment).filter(RiskAssessment.customer_id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(SimulationResult).filter(SimulationResult.customer_id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(Invoice).filter(Invoice.customer_id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(Contract).filter(Contract.customer_id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(Email).filter(Email.customer_id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(Meeting).filter(Meeting.customer_id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(SupportTicket).filter(SupportTicket.customer_id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(Customer).filter(Customer.organization_id == organization_id).delete(synchronize_session=False)
        db.commit()

def generate_synthetic_data(db: Session, organization_id: int) -> int:
    """
    Generates:
    - 100 Customers
    - 100 Contracts (1 per customer)
    - 500 Invoices (5 per customer)
    - 500 Support Tickets (spread among customers)
    - 800 Emails + 200 Meetings = 1000 Interactions (spread among customers)
    
    Ensures pre-computed embeddings are set on emails, meetings, and tickets.
    """
    # Clear existing data first
    clear_synthetic_data(db, organization_id)
    
    print("Generating 100 realistic customers...")
    customers = []
    
    # Pre-generate customer list
    # We will explicitly make some accounts high risk, some medium risk, and some healthy
    for i in range(100):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} {random.choice(COMPANY_SUFFIXES)}"
        # Check for unique names
        while name in [c.name for c in customers]:
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} {random.choice(COMPANY_SUFFIXES)}"
            
        industry = random.choice(INDUSTRIES)
        revenue = round(random.uniform(12000.0, 480000.0), 2)
        
        # We start with basic low-risk values. Orchestrator pipelines will calculate exact risk scores later.
        cust = Customer(
            name=name,
            industry=industry,
            revenue=revenue,
            health_score=100.0,
            churn_probability=0.0,
            revenue_at_risk=0.0,
            risk_level="Low",
            organization_id=organization_id
        )
        db.add(cust)
        customers.append(cust)
        
    db.commit()  # Flush so customer IDs are generated
    
    # Map index profiles (we designate 15% high-risk, 25% medium-risk, 60% low-risk)
    # High risk indices: 0 to 14
    # Med risk indices: 15 to 39
    # Low risk indices: 40 to 99
    
    print("Generating 100 contracts...")
    now = datetime.datetime.utcnow()
    for idx, cust in enumerate(customers):
        # Determine end date based on risk profiles
        if idx < 15:
            # High Risk: Contract expires in 15 to 45 days
            days_to_end = random.randint(15, 45)
        elif idx < 40:
            # Medium Risk: Expires in 46 to 90 days
            days_to_end = random.randint(46, 90)
        else:
            # Low Risk: Expires in 120 to 500 days
            days_to_end = random.randint(120, 500)
            
        start_date = now - datetime.timedelta(days=random.randint(180, 300))
        end_date = now + datetime.timedelta(days=days_to_end)
        
        contract = Contract(
            customer_id=cust.id,
            title=f"Enterprise Software License - {cust.name}",
            value=cust.revenue,
            start_date=start_date,
            end_date=end_date,
            renewal_risk_score=0.0,
            status="Active"
        )
        db.add(contract)
        
    # Generate 500 invoices (5 per customer)
    print("Generating 500 invoices...")
    for idx, cust in enumerate(customers):
        for invoice_idx in range(5):
            # Calculate due dates and issues dates
            # Standard monthly invoices, monthly intervals backwards
            issue_delay = (invoice_idx * 30) + 10
            issue_date = now - datetime.timedelta(days=issue_delay)
            due_date = issue_date + datetime.timedelta(days=30)
            
            # Determine invoice status based on due date and risk profile
            invoice_num = f"INV-2026-{cust.id:04d}-{invoice_idx:02d}"
            amount = round(cust.revenue / 12.0, 2)
            
            if due_date < now:
                # Invoice is in the past
                if idx < 15 and invoice_idx == 0:
                    # High risk customer: latest invoice is unpaid (Overdue)
                    status = "Overdue"
                elif idx < 40 and invoice_idx == 0 and random.random() > 0.4:
                    # Med risk customer: sometimes overdue
                    status = "Overdue"
                else:
                    status = "Paid"
            else:
                # Invoice due in the future
                status = "Unpaid"
                
            inv = Invoice(
                customer_id=cust.id,
                invoice_number=invoice_num,
                amount=amount,
                issue_date=issue_date,
                due_date=due_date,
                status=status,
                payment_risk_score=0.0
            )
            db.add(inv)
            
    # Generate 500 Support Tickets
    print("Generating 500 support tickets...")
    ticket_count = 0
    while ticket_count < 500:
        # High-risk accounts get more open tickets, low-risk accounts get mostly resolved tickets
        cust_idx = random.randint(0, 99)
        cust = customers[cust_idx]
        
        subj_tmpl, body_tmpl, category, priority, sent_val = random.choice(TICKET_TEMPLATES)
        
        # High-risk accounts are more likely to have open high-priority tickets
        if cust_idx < 15:
            status = "Open" if random.random() > 0.1 else "In Progress"
            priority = random.choice(["High", "Medium"])
        elif cust_idx < 40:
            status = random.choice(["Open", "In Progress", "Resolved"])
        else:
            status = "Resolved"
            priority = "Low"
            
        created_delay = random.randint(5, 60)
        created_at = now - datetime.timedelta(days=created_delay)
        resolved_at = None
        
        if status == "Resolved":
            resolved_at = created_at + datetime.timedelta(days=random.randint(1, 4))
            sent_val = min(1.0, sent_val + 0.5)  # resolving tickets improves sentiment
            
        desc_text = f"Customer reported ticket regarding {category}. {body_tmpl}"
        
        # Generate semantic embedding
        vec_emb = foundry_iq_adapter.get_embedding(f"{subj_tmpl} {desc_text}")
        
        ticket = SupportTicket(
            customer_id=cust.id,
            title=subj_tmpl,
            description=desc_text,
            status=status,
            priority=priority,
            sentiment_score=sent_val,
            created_at=created_at,
            resolved_at=resolved_at,
            vector_embedding=vec_emb
        )
        db.add(ticket)
        ticket_count += 1
        
    # Generate 800 Emails and 200 Meetings (Total 1000 interactions)
    print("Generating 800 emails...")
    email_count = 0
    while email_count < 800:
        cust_idx = random.randint(0, 99)
        cust = customers[cust_idx]
        cust_domain = f"{cust.name.split()[0].lower()}.com"
        
        # Sentiment selection based on risk profile
        if cust_idx < 15:
            # High risk: mostly negative templates
            subj, body = random.choice(EMAIL_TEMPLATES_NEGATIVE)
            sentiment = "Negative"
            sent_score = random.uniform(-0.95, -0.45)
            sender = f"pointofcontact@{cust_domain}"
            recipient = "csm@reviveiq.com"
        elif cust_idx < 40:
            # Med risk: mixed templates
            subj, body = random.choice(EMAIL_TEMPLATES_NEUTRAL + EMAIL_TEMPLATES_NEGATIVE)
            sentiment = "Negative" if subj in [e[0] for e in EMAIL_TEMPLATES_NEGATIVE] else "Neutral"
            sent_score = random.uniform(-0.45, 0.1)
            sender = f"pointofcontact@{cust_domain}"
            recipient = "csm@reviveiq.com"
        else:
            # Healthy: positive or neutral templates
            subj, body = random.choice(EMAIL_TEMPLATES_POSITIVE + EMAIL_TEMPLATES_NEUTRAL)
            sentiment = "Positive" if subj in [e[0] for e in EMAIL_TEMPLATES_POSITIVE] else "Neutral"
            sent_score = random.uniform(0.1, 0.95)
            # Mix sender us/them
            if random.random() > 0.5:
                sender = "csm@reviveiq.com"
                recipient = f"pointofcontact@{cust_domain}"
            else:
                sender = f"pointofcontact@{cust_domain}"
                recipient = "csm@reviveiq.com"
                
        # Customize variables if present
        body = body.format(inv_num=f"INV-2026-{cust.id:04d}-00")
        
        date = now - datetime.timedelta(days=random.randint(1, 90))
        vec_emb = foundry_iq_adapter.get_embedding(f"{subj} {body}")
        
        email = Email(
            customer_id=cust.id,
            sender=sender,
            recipient=recipient,
            subject=subj,
            body=body,
            sentiment=sentiment,
            sentiment_score=sent_score,
            date=date,
            vector_embedding=vec_emb
        )
        db.add(email)
        email_count += 1
        
    print("Generating 200 meetings...")
    meeting_count = 0
    while meeting_count < 200:
        cust_idx = random.randint(0, 99)
        cust = customers[cust_idx]
        cust_domain = f"{cust.name.split()[0].lower()}.com"
        
        # Pick template
        title, summary, base_sent = random.choice(MEETING_TEMPLATES)
        
        # Adjust sentiment slightly based on risk
        if cust_idx < 15:
            sent_score = max(-1.0, base_sent - 0.4)
        elif cust_idx < 40:
            sent_score = max(-1.0, base_sent - 0.1)
        else:
            sent_score = min(1.0, base_sent + 0.2)
            
        attendees = ["csm@reviveiq.com", f"exec@{cust_domain}", f"finance@{cust_domain}"]
        date = now - datetime.timedelta(days=random.randint(2, 90))
        
        vec_emb = foundry_iq_adapter.get_embedding(f"{title} {summary}")
        
        meeting = Meeting(
            customer_id=cust.id,
            title=title,
            summary=summary,
            sentiment_score=sent_score,
            attendees=attendees,
            date=date,
            vector_embedding=vec_emb
        )
        db.add(meeting)
        meeting_count += 1
        
    db.commit()
    print("Synthetic database generated successfully.")
    return len(customers)
