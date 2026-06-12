from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.endpoints.auth import require_any_role
from app.models.models import Customer, RevenueRescueCampaign, User
from app.models.schemas import RevenueRescueCampaignResponse
from app.services.campaign_generator import generate_rescue_campaign

router = APIRouter()

@router.get("/", response_model=List[RevenueRescueCampaignResponse])
def get_all_campaigns(
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves all generated Revenue Rescue Campaigns scoped by organization."""
    campaigns = db.query(RevenueRescueCampaign).join(Customer).filter(
        Customer.organization_id == current_user.organization_id
    ).all()
    
    # Set customer_name dynamically on response
    results = []
    for c in campaigns:
        res = RevenueRescueCampaignResponse.model_validate(c)
        res.customer_name = c.customer.name
        results.append(res)
        
    return results

@router.get("/{id}", response_model=RevenueRescueCampaignResponse)
def get_campaign_by_id(
    id: int,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Retrieves details of a single campaign by ID."""
    campaign = db.query(RevenueRescueCampaign).join(Customer).filter(
        RevenueRescueCampaign.id == id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rescue campaign not found or unauthorized access."
        )
        
    res = RevenueRescueCampaignResponse.model_validate(campaign)
    res.customer_name = campaign.customer.name
    return res

@router.post("/generate/{customer_id}", response_model=RevenueRescueCampaignResponse)
def trigger_campaign_generation(
    customer_id: int,
    current_user: User = Depends(require_any_role),
    db: Session = Depends(get_db)
):
    """Manually forces a campaign generation for the specified customer."""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.organization_id == current_user.organization_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or unauthorized access."
        )
        
    campaign = generate_rescue_campaign(db, customer_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate revenue rescue campaign."
        )
        
    res = RevenueRescueCampaignResponse.model_validate(campaign)
    res.customer_name = customer.name
    return res
