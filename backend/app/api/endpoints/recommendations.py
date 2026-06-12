from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role, require_cs_or_admin
from app.models.models import Recommendation, Customer, User, AuditLog
from app.models.schemas import RecommendationResponse, RecommendationUpdate

router = APIRouter()

@router.get("/", response_model=List[RecommendationResponse])
def get_recommendations(
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves all pending and active recovery recommendations for the organization."""
    recs = db.query(Recommendation).join(Customer).filter(
        Customer.organization_id == current_user.organization_id
    ).order_by(Recommendation.priority.desc()).all()
    
    # Populate the transient customer_name attribute
    results = []
    for r in recs:
        # Pydantic schema will read fields directly. Since we have relationship Customer,
        # we can attach name to schema
        res = RecommendationResponse.model_validate(r)
        res.customer_name = r.customer.name
        results.append(res)
        
    return results

@router.put("/{recommendation_id}", response_model=RecommendationResponse)
def update_recommendation_status(
    recommendation_id: int,
    payload: RecommendationUpdate,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Updates the status (e.g. Approved, Completed) of a specific recommendation."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation record not found."
        )
        
    # Verify client ownership
    customer = db.query(Customer).filter(
        Customer.id == rec.customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to this customer record."
        )
        
    old_status = rec.status
    rec.status = payload.status
    
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_RECOMMENDATION",
        target_table="recommendations",
        target_id=rec.id,
        details={
            "old_status": old_status,
            "new_status": payload.status,
            "title": rec.title
        }
    )
    db.add(audit)
    db.commit()
    
    # Return mapping
    res = RecommendationResponse.model_validate(rec)
    res.customer_name = customer.name
    return res
