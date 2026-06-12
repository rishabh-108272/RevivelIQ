import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import get_current_user, require_any_role
from app.models.models import Customer, User, Contract, Invoice, Email, Meeting, SupportTicket, RiskAssessment, Recommendation
from app.models.schemas import CustomerResponse, CustomerDetailResponse, RecommendationResponse
from app.services.agents.orchestrator import orchestrator

router = APIRouter()

@router.get("/", response_model=List[CustomerResponse])
def get_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    industry: Optional[str] = None,
    risk_level: Optional[str] = None,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves list of customers matching search and filter conditions, scoped by organization."""
    query = db.query(Customer).filter(Customer.organization_id == current_user.organization_id)
    
    if search:
        query = query.filter(Customer.name.ilike(f"%{search}%"))
    if industry:
        query = query.filter(Customer.industry == industry)
    if risk_level:
        query = query.filter(Customer.risk_level == risk_level)
        
    # Order by revenue at risk descending, then churn probability
    query = query.order_by(Customer.revenue_at_risk.desc(), Customer.churn_probability.desc())
    
    return query.offset(skip).limit(limit).all()

@router.get("/export")
def export_customers_csv(
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Exports portfolio accounts and current risk metrics in CSV format."""
    customers = db.query(Customer).filter(Customer.organization_id == current_user.organization_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Customer ID", "Company Name", "Industry", "Annual Revenue ($)",
        "Customer Health Score (/100)", "Churn Probability (%)", "Revenue at Risk ($)", "Risk Level"
    ])
    
    # Write rows
    for c in customers:
        writer.writerow([
            c.id, c.name, c.industry or "Unknown", c.revenue,
            round(c.health_score, 1), round(c.churn_probability * 100, 0),
            c.revenue_at_risk, c.risk_level
        ])
        
    output.seek(0)
    
    headers = {
        "Content-Disposition": "attachment; filename=reviveiq_portfolio_risk_report.csv",
        "Content-Type": "text/csv"
    }
    
    return StreamingResponse(io.BytesIO(output.getvalue().encode("utf-8")), headers=headers)

@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer_detail(
    customer_id: int,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves comprehensive detailed profile data for a single customer."""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer record not found or access unauthorized."
        )
        
    # Fetch details
    contracts = db.query(Contract).filter(Contract.customer_id == customer_id).all()
    invoices = db.query(Invoice).filter(Invoice.customer_id == customer_id).order_by(Invoice.due_date.desc()).all()
    emails = db.query(Email).filter(Email.customer_id == customer_id).order_by(Email.date.desc()).all()
    meetings = db.query(Meeting).filter(Meeting.customer_id == customer_id).order_by(Meeting.date.desc()).all()
    tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == customer_id).order_by(SupportTicket.created_at.desc()).all()
    
    # Get latest risk assessment explanation
    latest_assessment = db.query(RiskAssessment).filter(
        RiskAssessment.customer_id == customer_id
    ).order_by(RiskAssessment.generated_at.desc()).first()
    
    explainability = latest_assessment.explainability_json if latest_assessment else {}
    
    # Fetch pending recommendations
    recs = db.query(Recommendation).filter(
        Recommendation.customer_id == customer_id
    ).order_by(Recommendation.priority.desc()).all()

    # Calculate Microsoft IQ Insights dynamically
    from app.services.microsoft_work_iq import work_iq_adapter
    from app.services.microsoft_foundry_iq import foundry_iq_adapter
    
    work_iq_data = work_iq_adapter.analyze_collaboration(db, customer_id)
    collab_idx = work_iq_data["collaboration_index"]
    latency = work_iq_data["avg_latency_hours"]
    
    work_insights = []
    if work_iq_data.get("silence_risk"):
        work_insights.append({
            "insight": "Engagement decreased 45% (no meetings or emails in last 30 days).",
            "source_agent": "Work IQ Agent",
            "impact_score": -25
        })
        work_insights.append({
            "insight": "Collaboration index dropped below standard parameters.",
            "source_agent": "Work IQ Agent",
            "impact_score": -10
        })
    elif latency > 36:
        work_insights.append({
            "insight": f"Collaboration index dropped below threshold. Average reply latency is {latency:.1f} hours.",
            "source_agent": "Work IQ Agent",
            "impact_score": -10
        })
    else:
        work_insights.append({
            "insight": f"Healthy relationship collaboration maintained (Index: {collab_idx:.1f}/100).",
            "source_agent": "Work IQ Agent",
            "impact_score": 10
        })

    clustered_tickets = foundry_iq_adapter.cluster_customer_tickets(tickets)
    foundry_insights = []
    
    overdue_invoices = [i for i in invoices if i.status == "Overdue"]
    if overdue_invoices:
        foundry_insights.append({
            "insight": "Billing complaints trending upward due to unpaid invoices.",
            "source_agent": "Foundry IQ Agent",
            "impact_score": -15
        })
        
    if clustered_tickets:
        top_cluster = clustered_tickets[0]
        foundry_insights.append({
            "insight": f"Ticket cluster detected: '{top_cluster['category']}' containing {top_cluster['count']} case(s).",
            "source_agent": "Foundry IQ Agent",
            "impact_score": -8
        })
    else:
        foundry_insights.append({
            "insight": "No ticket cluster anomalies detected.",
            "source_agent": "Foundry IQ Agent",
            "impact_score": 0
        })
        
    iq_insights = {
        "work_iq": work_insights,
        "foundry_iq": foundry_insights
    }
    
    return {
        "customer": customer,
        "contracts": contracts,
        "invoices": invoices,
        "emails": emails,
        "meetings": meetings,
        "support_tickets": tickets,
        "churn_probability": customer.churn_probability,
        "revenue_at_risk": customer.revenue_at_risk,
        "risk_explanation": explainability,
        "recommendations": recs,
        "microsoft_iq_insights": iq_insights
    }

@router.post("/{customer_id}/analyze")
def trigger_customer_analysis(
    customer_id: int,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Manually re-runs multi-agent risk assessment pipeline for a client."""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer record not found or access unauthorized."
        )
        
    pipeline_res = orchestrator.run_customer_pipeline(db, customer_id, user_id=current_user.id)
    return pipeline_res
