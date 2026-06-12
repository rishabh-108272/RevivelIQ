from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role
from app.models.models import Invoice, Customer, User
from app.models.schemas import InvoiceResponse

router = APIRouter()

@router.get("/", response_model=List[InvoiceResponse])
def get_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves list of invoices for the organization, optionally filtered by billing status."""
    query = db.query(Invoice).join(Customer).filter(
        Customer.organization_id == current_user.organization_id
    )
    
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
        
    return query.order_by(Invoice.due_date.asc()).all()
