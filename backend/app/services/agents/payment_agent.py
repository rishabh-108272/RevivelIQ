import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.models import Invoice

class PaymentIntelligenceAgent(BaseAgent):
    """
    Agent 2: Payment Intelligence Agent
    Analyzes invoices, identifies unpaid/overdue status, and predicts delay timelines.
    Outputs: payment_risk_score (0.0 to 100.0)
    """
    
    @property
    def name(self) -> str:
        return "PaymentIntelligenceAgent"
        
    def run(self, db: Session, customer_id: int, **kwargs) -> Dict[str, Any]:
        invoices = db.query(Invoice).filter(Invoice.customer_id == customer_id).all()
        
        if not invoices:
            return {
                "payment_risk_score": 0.0,
                "unpaid_count": 0,
                "overdue_count": 0,
                "total_overdue_amount": 0.0,
                "explanation": "No invoices detected. No billing risk recorded."
            }
            
        unpaid_invoices = [i for i in invoices if i.status in ("Unpaid", "Overdue")]
        overdue_invoices = [i for i in invoices if i.status == "Overdue"]
        
        now = datetime.datetime.utcnow()
        
        # Calculate Overdue stats
        total_overdue_amt = sum(inv.amount for inv in overdue_invoices)
        total_unpaid_amt = sum(inv.amount for inv in unpaid_invoices)
        
        max_overdue_days = 0
        for inv in overdue_invoices:
            overdue_days = (now - inv.due_date).days
            if overdue_days > max_overdue_days:
                max_overdue_days = overdue_days
                
        # 1. Base Score calculation on aging and counts
        base_score = 0.0
        
        if overdue_invoices:
            # Overdue invoices present
            if max_overdue_days > 45:
                base_score = 85.0 + min(15.0, (max_overdue_days - 45) * 0.3)
            elif max_overdue_days > 15:
                base_score = 60.0 + (max_overdue_days - 15) * 0.8
            else:
                base_score = 30.0 + max_overdue_days * 2.0
        elif unpaid_invoices:
            # Unpaid but not yet past due
            base_score = 15.0 + len(unpaid_invoices) * 2.0
            
        # Scale score based on the financial weight of overdue invoices
        if total_overdue_amt > 25000:
            base_score = min(100.0, base_score + 10.0)
            
        payment_risk_score = max(0.0, min(100.0, float(base_score)))
        
        # 2. Predict Invoice Payment Delay Days
        # Uses a simulated rule representing accounting delay factors:
        # e.g., large invoice values cause authorization overhead, increasing delay.
        for inv in invoices:
            if inv.status in ("Unpaid", "Overdue"):
                delay_pred = 0
                days_since_issue = (now - inv.issue_date).days
                
                # Base delays based on amount
                if inv.amount > 50000:
                    delay_pred += 14  # Large approvals delay
                elif inv.amount > 20000:
                    delay_pred += 7
                    
                # Add delay if customer already overdue
                if max_overdue_days > 0:
                    delay_pred += min(21, max_overdue_days)
                    
                inv.payment_delay_prediction_days = delay_pred
                inv.payment_risk_score = payment_risk_score
                
        db.commit()
        
        # Build explanation narrative
        if overdue_invoices:
            explanation = (
                f"Customer has {len(overdue_invoices)} overdue invoice(s) totalling ${total_overdue_amt:,.2f}. "
                f"Maximum overdue duration is {max_overdue_days} days. "
                f"Predicted delay for upcoming invoices is up to {max(i.payment_delay_prediction_days for i in unpaid_invoices) if unpaid_invoices else 0} days."
            )
        elif unpaid_invoices:
            explanation = f"Customer has {len(unpaid_invoices)} open invoices awaiting payment ($ {total_unpaid_amt:,.2f}). Accounts are currently within standard credit terms."
        else:
            explanation = "All invoices are fully paid. billing account demonstrates outstanding health status."
            
        return {
            "payment_risk_score": payment_risk_score,
            "unpaid_count": len(unpaid_invoices),
            "overdue_count": len(overdue_invoices),
            "total_overdue_amount": total_overdue_amt,
            "max_overdue_days": max_overdue_days,
            "explanation": explanation
        }

payment_agent = PaymentIntelligenceAgent()
