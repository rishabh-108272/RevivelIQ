from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role
from app.models.models import RiskAssessment, Customer, User

router = APIRouter()

@router.get("/{customer_id}")
def get_customer_risk_history(
    customer_id: int,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves the full chronological history of risk assessments for a customer."""
    # Verify customer ownership
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer record not found or access unauthorized."
        )
        
    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.customer_id == customer_id
    ).order_by(RiskAssessment.generated_at.desc()).all()
    
    return [
        {
            "id": a.id,
            "contract_risk_score": a.contract_risk_score,
            "payment_risk_score": a.payment_risk_score,
            "customer_health_score": a.customer_health_score,
            "sentiment_score": a.sentiment_score,
            "aggregate_churn_prob": a.aggregate_churn_prob,
            "aggregate_revenue_at_risk": a.aggregate_revenue_at_risk,
            "risk_level": a.risk_level,
            "explainability": a.explainability_json,
            "generated_at": a.generated_at
        }
        for a in assessments
    ]
