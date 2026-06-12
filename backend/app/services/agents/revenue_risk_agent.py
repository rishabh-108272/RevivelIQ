import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.models import Customer, RiskAssessment
from app.services.agents.contract_agent import contract_agent
from app.services.agents.payment_agent import payment_agent
from app.services.agents.cs_agent import cs_agent

class RevenueRiskAgent(BaseAgent):
    """
    Agent 4: Revenue Risk Agent
    Aggregates indicators from the Contract, Payment, and CS Agents to determine
    overall churn probability, revenue at risk, and risk classification.
    Outputs: churn_probability (0.0 to 1.0), revenue_at_risk (float), risk_level (High/Medium/Low)
    """
    
    @property
    def name(self) -> str:
        return "RevenueRiskAgent"
        
    def run(self, db: Session, customer_id: int, **kwargs) -> Dict[str, Any]:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {
                "churn_probability": 0.0,
                "revenue_at_risk": 0.0,
                "risk_level": "Low",
                "explanation": "Customer not found."
            }
            
        # 1. Run upstream agents or read cached database values if already processed
        # For a full fresh run, we invoke them:
        contract_data = contract_agent.run(db, customer_id)
        payment_data = payment_agent.run(db, customer_id)
        cs_data = cs_agent.run(db, customer_id)
        
        renewal_score = contract_data["renewal_risk_score"]
        payment_score = payment_data["payment_risk_score"]
        health_score = cs_data["customer_health_score"]
        sentiment_score = cs_data["sentiment_score"]
        
        # 2. Weighted Churn Probability Model
        # Formula weights: Contract Renewal (35%), Payment Delinquency (25%), CSM Health Index (40%)
        cs_risk = 100.0 - health_score
        weighted_score = (renewal_score * 0.35) + (payment_score * 0.25) + (cs_risk * 0.40)
        
        churn_probability = max(0.0, min(1.0, weighted_score / 100.0))
        
        # 3. Calculate Revenue at Risk
        # Represents estimated exposure value
        revenue_at_risk = round(churn_probability * customer.revenue, 2)
        
        # 4. Classify Risk Level
        if churn_probability >= 0.60:
            risk_level = "High"
        elif churn_probability >= 0.30:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        # 5. Compile Explainability JSON structure
        explainability = {
            "summary_statement": f"Customer is classified as {risk_level} risk with a {int(churn_probability * 100)}% churn probability.",
            "metrics": {
                "contract_renewal_risk": round(renewal_score, 1),
                "payment_delinquency_risk": round(payment_score, 1),
                "customer_health_deficit": round(cs_risk, 1),
                "average_sentiment_score": round(sentiment_score, 2),
                "work_iq_collaboration_strength": round(cs_data["work_iq_collaboration_index"], 1)
            },
            "evidence_flags": [],
            "reasoning_trace": [
                "Step 1: Contract risk evaluated",
                "Step 2: Invoice history analyzed",
                "Step 3: Customer sentiment evaluated",
                "Step 4: Revenue risk calculated",
                "Step 5: Recovery actions generated"
            ]
        }
        
        # Build list of dynamic evidence bullets
        if contract_data.get("remaining_days", 999) <= 45:
            explainability["evidence_flags"].append(
                f"Contract renewal window is critically close ({contract_data['remaining_days']} days remaining)."
            )
        if payment_data.get("overdue_count", 0) > 0:
            explainability["evidence_flags"].append(
                f"Outstanding past due invoicing detected: {payment_data['overdue_count']} invoice(s) totalling ${payment_data['total_overdue_amount']:,.2f} (max {payment_data['max_overdue_days']} days overdue)."
            )
        if cs_data.get("open_tickets_count", 0) > 4:
            explainability["evidence_flags"].append(
                f"High support ticket volume: {cs_data['open_tickets_count']} unresolved tickets outstanding."
            )
        if cs_data.get("high_priority_tickets_count", 0) > 0:
            explainability["evidence_flags"].append(
                f"Urgent tickets: {cs_data['high_priority_tickets_count']} High Priority ticket(s) unresolved."
            )
        if sentiment_score < -0.1:
            explainability["evidence_flags"].append(
                f"Negative client communication sentiment flagged (Sentiment Index: {sentiment_score:+.2f})."
            )
        if cs_data.get("work_iq_collaboration_index", 100) < 60:
            explainability["evidence_flags"].append(
                "Work IQ communication gap: Drop in email activity and meeting touchpoints over the last 30 days."
            )
            
        if not explainability["evidence_flags"]:
            explainability["evidence_flags"].append("No negative signals identified. Account shows stable growth parameters.")
            
        # 6. Save Risk Assessment History
        assessment = RiskAssessment(
            customer_id=customer_id,
            contract_risk_score=renewal_score,
            payment_risk_score=payment_score,
            customer_health_score=health_score,
            sentiment_score=sentiment_score,
            aggregate_churn_prob=churn_probability,
            aggregate_revenue_at_risk=revenue_at_risk,
            risk_level=risk_level,
            explainability_json=explainability
        )
        db.add(assessment)
        
        # 7. Update Customer record cache
        customer.churn_probability = churn_probability
        customer.revenue_at_risk = revenue_at_risk
        customer.risk_level = risk_level
        db.commit()
        
        return {
            "churn_probability": churn_probability,
            "revenue_at_risk": revenue_at_risk,
            "risk_level": risk_level,
            "explainability": explainability
        }

revenue_risk_agent = RevenueRiskAgent()
