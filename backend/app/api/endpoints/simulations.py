from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role
from app.models.models import SimulationResult, Customer, User
from app.models.schemas import SimulationCreate, SimulationResponse, OrgSimulationRequest, OrgSimulationResponse
from app.services.agents.decision_simulator import decision_simulator
from app.services.agents.organization_simulator import org_simulator

router = APIRouter()

@router.post("/", response_model=SimulationResponse)
def run_simulation(
    payload: SimulationCreate,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Executes a custom 'what-if' simulation for a client, recalculating risk metrics."""
    # Verify customer ownership
    customer = db.query(Customer).filter(
        Customer.id == payload.customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer record not found or access unauthorized."
        )
        
    res = decision_simulator.run(
        db,
        customer_id=payload.customer_id,
        query=payload.query,
        resolve_tickets=payload.resolve_tickets,
        clear_overdue_invoices=payload.clear_overdue_invoices,
        apply_renewal_discount=payload.apply_renewal_discount,
        discount_percentage=payload.discount_percentage
    )
    
    if "error" in res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["error"]
        )
        
    return res

@router.get("/customer/{customer_id}", response_model=List[SimulationResponse])
def get_customer_simulations(
    customer_id: int,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves all historical simulation results run for a customer."""
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
        
    sims = db.query(SimulationResult).filter(
        SimulationResult.customer_id == customer_id
    ).order_by(SimulationResult.created_at.desc()).all()
    
    return sims

@router.post("/organization", response_model=OrgSimulationResponse)
def run_org_simulation(
    payload: OrgSimulationRequest,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Executes an organization-level What-If simulation scenario across all customers."""
    res = org_simulator.run_simulation(db, current_user.organization_id, payload.scenario)
    return res
