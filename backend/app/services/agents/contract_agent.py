import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.models import Contract

class ContractIntelligenceAgent(BaseAgent):
    """
    Agent 1: Contract Intelligence Agent
    Analyzes contracts, detects upcoming renewals, and flags duration risks.
    Outputs: renewal_risk_score (0.0 to 100.0)
    """
    
    @property
    def name(self) -> str:
        return "ContractIntelligenceAgent"
        
    def run(self, db: Session, customer_id: int, **kwargs) -> Dict[str, Any]:
        contracts = db.query(Contract).filter(Contract.customer_id == customer_id).all()
        
        if not contracts:
            return {
                "renewal_risk_score": 40.0,
                "status": "No Active Contracts",
                "explanation": "No contracts found for this customer record. Assumed moderate baseline onboarding/renewal risk."
            }
            
        # Analyze the most critical contract (earliest end date or active contract)
        active_contracts = [c for c in contracts if c.status == "Active"]
        target_contract = None
        
        if active_contracts:
            # Get the one expiring first
            target_contract = min(active_contracts, key=lambda c: c.end_date)
        else:
            # No active, check all contracts
            target_contract = sorted(contracts, key=lambda c: c.end_date, reverse=True)[0]
            
        now = datetime.datetime.utcnow()
        remaining_days = (target_contract.end_date - now).days
        
        # Calculate risk based on time remaining to renew
        if target_contract.status == "Expired":
            renewal_risk_score = 100.0
            explanation = f"Contract '{target_contract.title}' has expired on {target_contract.end_date.strftime('%Y-%m-%d')}."
        elif remaining_days < 0:
            renewal_risk_score = 95.0
            explanation = f"Contract '{target_contract.title}' past end-date by {abs(remaining_days)} days without active renewal status update."
        elif remaining_days <= 30:
            # Critically close
            renewal_risk_score = 85.0 + (30 - remaining_days) * 0.5  # Up to 100
            explanation = f"Contract '{target_contract.title}' expires in {remaining_days} days! Critically short window for renewal negotiation."
        elif remaining_days <= 90:
            # Medium warning
            renewal_risk_score = 50.0 + (90 - remaining_days) * 0.5  # 50 to 80
            explanation = f"Contract '{target_contract.title}' expires in {remaining_days} days. Standard renewal cycle engagement should be initiated."
        elif remaining_days <= 180:
            # Low warning
            renewal_risk_score = 25.0 + (180 - remaining_days) * 0.25  # 25 to 47.5
            explanation = f"Contract '{target_contract.title}' expires in {remaining_days} days. Account is stable but early preparation is recommended."
        else:
            # Safe
            renewal_risk_score = 10.0
            explanation = f"Contract '{target_contract.title}' is secure with {remaining_days} days remaining before expiration."
            
        # Adjust risk score based on contract value (high value = higher operational focus/weighted risk)
        # We increase or decrease slightly to represent attention levels
        if target_contract.value > 100000 and renewal_risk_score > 30:
            renewal_risk_score = min(100.0, renewal_risk_score + 10.0)
            explanation += " (High contract value ($100k+) escalates renewal attention requirements)."
            
        # Cap scores
        renewal_risk_score = max(0.0, min(100.0, float(renewal_risk_score)))
        
        # Save to database
        target_contract.renewal_risk_score = renewal_risk_score
        target_contract.risk_explanation = explanation
        db.commit()
        
        return {
            "renewal_risk_score": renewal_risk_score,
            "contract_title": target_contract.title,
            "contract_value": target_contract.value,
            "remaining_days": remaining_days,
            "explanation": explanation
        }

contract_agent = ContractIntelligenceAgent()
