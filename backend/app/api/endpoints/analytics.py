import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role, require_admin
from app.models.models import Customer, Contract, Invoice, User, AuditLog, RiskAssessment, Recommendation
from app.models.schemas import DashboardMetrics, ExecutiveBriefingResponse
from app.services.agents.executive_briefing_agent import executive_briefing_agent
from app.services.agents.orchestrator import orchestrator
from app.utils.synthetic_generator import generate_synthetic_data

router = APIRouter()

@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Calculates all key summary stats and distributions for the Executive Dashboard."""
    org_id = current_user.organization_id
    
    # 1. Aggregates
    total_at_risk = db.query(func.sum(Customer.revenue_at_risk)).filter(
        Customer.organization_id == org_id
    ).scalar() or 0.0
    
    churn_count = db.query(Customer).filter(
        Customer.organization_id == org_id,
        Customer.risk_level == "High"
    ).count()
    
    # Upcoming renewals (Active contracts expiring in 60 days)
    now = datetime.datetime.utcnow()
    sixty_days_hence = now + datetime.timedelta(days=60)
    
    renewals_count = db.query(Contract).join(Customer).filter(
        Customer.organization_id == org_id,
        Contract.status == "Active",
        Contract.end_date <= sixty_days_hence
    ).count()
    
    # Overdue invoices
    overdue_count = db.query(Invoice).join(Customer).filter(
        Customer.organization_id == org_id,
        Invoice.status == "Overdue"
    ).count()
    
    # 2. Risk Distribution
    high_count = db.query(Customer).filter(Customer.organization_id == org_id, Customer.risk_level == "High").count()
    med_count = db.query(Customer).filter(Customer.organization_id == org_id, Customer.risk_level == "Medium").count()
    low_count = db.query(Customer).filter(Customer.organization_id == org_id, Customer.risk_level == "Low").count()
    
    risk_distribution = {
        "High": high_count,
        "Medium": med_count,
        "Low": low_count
    }
    
    # 3. Health trends (Simulate historical months for display)
    # Average customer health score per month
    health_trends = [
        {"month": "Jan", "health_score": 88.5, "revenue_at_risk": total_at_risk * 0.75},
        {"month": "Feb", "health_score": 87.2, "revenue_at_risk": total_at_risk * 0.82},
        {"month": "Mar", "health_score": 85.9, "revenue_at_risk": total_at_risk * 0.88},
        {"month": "Apr", "health_score": 84.1, "revenue_at_risk": total_at_risk * 0.95},
        {"month": "May", "health_score": 82.8, "revenue_at_risk": total_at_risk * 0.98},
        {"month": "Jun", "health_score": round(db.query(func.avg(Customer.health_score)).filter(Customer.organization_id == org_id).scalar() or 82.5, 1), "revenue_at_risk": total_at_risk}
    ]
    
    return {
        "total_revenue_at_risk": round(total_at_risk, 2),
        "predicted_churn_count": churn_count,
        "upcoming_renewals_count": renewals_count,
        "overdue_invoices_count": overdue_count,
        "risk_distribution": risk_distribution,
        "health_trends": health_trends
    }

@router.get("/executive-briefing", response_model=ExecutiveBriefingResponse)
def get_executive_briefing(
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves synthesized narrative briefing summary across the organization portfolio."""
    res = executive_briefing_agent.run(db, current_user.organization_id)
    return res

@router.post("/reseed")
def reseed_database(
    current_user: User = Depends(require_admin),  # Only Admin can reseed
    db: Session = Depends(get_db)
):
    """Wipes customer database tables and rebuilds 100 fresh synthetic customer profiles."""
    org_id = current_user.organization_id
    
    # 1. Seed customer profiles (invoices, contracts, emails, meetings, support_tickets)
    generate_synthetic_data(db, org_id)
    
    # 2. Trigger orchestrator pipeline to pre-calculate all risk metrics
    orchestrator.run_portfolio_sync(db, org_id, user_id=current_user.id)
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DATABASE_RESEED",
        target_table="organizations",
        target_id=org_id,
        details={"initiated_by": current_user.email}
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Database successfully reseeded and risk indices synchronized."}

@router.get("/war-room")
def get_war_room_data(
    sort_by: str = Query("revenue_at_risk", regex="^(churn_probability|contract_value|revenue_at_risk)$"),
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves top revenue threats ranked and sorted for the Revenue War Room dashboard."""
    org_id = current_user.organization_id
    customers = db.query(Customer).filter(Customer.organization_id == org_id).all()
    
    threats = []
    for c in customers:
        latest_assessment = db.query(RiskAssessment).filter(
            RiskAssessment.customer_id == c.id
        ).order_by(RiskAssessment.generated_at.desc()).first()
        
        reasons = latest_assessment.explainability_json.get("evidence_flags", []) if latest_assessment and latest_assessment.explainability_json else []
        
        recs = db.query(Recommendation).filter(
            Recommendation.customer_id == c.id,
            Recommendation.status == "Pending"
        ).order_by(Recommendation.priority.desc()).all()
        
        rec_action = recs[0].title if recs else "Schedule Strategic QBR Review"
        recovery_val = sum(r.net_recovery_value for r in recs)
        
        contracts = db.query(Contract).filter(Contract.customer_id == c.id, Contract.status == "Active").all()
        contract_val = contracts[0].value if contracts else c.revenue
        
        threats.append({
            "id": c.id,
            "customer_name": c.name,
            "industry": c.industry,
            "risk_score": round(c.churn_probability * 100, 1),
            "churn_probability": c.churn_probability,
            "contract_value": contract_val,
            "revenue_at_risk": c.revenue_at_risk,
            "risk_level": c.risk_level,
            "key_reasons": reasons,
            "recommended_action": rec_action,
            "estimated_recovery_value": recovery_val
        })
        
    if sort_by == "churn_probability":
        threats = sorted(threats, key=lambda x: x["churn_probability"], reverse=True)
    elif sort_by == "contract_value":
        threats = sorted(threats, key=lambda x: x["contract_value"], reverse=True)
    else:
        threats = sorted(threats, key=lambda x: x["revenue_at_risk"], reverse=True)
        
    return threats
