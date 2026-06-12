from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role
from app.models.models import RevenueCrisisAlert, User
from app.models.schemas import RevenueCrisisAlertResponse

router = APIRouter()

@router.get("/", response_model=List[RevenueCrisisAlertResponse])
def get_crisis_alerts(
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves all active Revenue Crisis alerts for the organization portfolio."""
    alerts = db.query(RevenueCrisisAlert).filter(
        RevenueCrisisAlert.organization_id == current_user.organization_id
    ).order_by(RevenueCrisisAlert.created_at.desc()).all()
    
    return alerts
