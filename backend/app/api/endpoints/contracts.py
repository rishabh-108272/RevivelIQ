from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role
from app.models.models import Contract, Customer, User
from app.models.schemas import ContractResponse

router = APIRouter()

@router.get("/", response_model=List[ContractResponse])
def get_contracts(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves list of contracts for the organization, optionally filtered by status."""
    query = db.query(Contract).join(Customer).filter(
        Customer.organization_id == current_user.organization_id
    )
    
    if status_filter:
        query = query.filter(Contract.status == status_filter)
        
    return query.order_by(Contract.end_date.asc()).all()
