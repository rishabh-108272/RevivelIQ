from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.models import Email, Meeting, SupportTicket, Customer
from app.services.microsoft_work_iq import work_iq_adapter
from app.services.microsoft_foundry_iq import foundry_iq_adapter

class CustomerSuccessAgent(BaseAgent):
    """
    Agent 3: Customer Success Agent
    Analyzes communication sentiment, support tickets backlog, and collaboration telemetry.
    Outputs: customer_health_score (0.0 to 100.0), sentiment_score (-1.0 to 1.0)
    """
    
    @property
    def name(self) -> str:
        return "CustomerSuccessAgent"
        
    def run(self, db: Session, customer_id: int, **kwargs) -> Dict[str, Any]:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {
                "customer_health_score": 50.0,
                "sentiment_score": 0.0,
                "explanation": "Customer not found."
            }
            
        # 1. Retrieve all communication records
        emails = db.query(Email).filter(Email.customer_id == customer_id).all()
        meetings = db.query(Meeting).filter(Meeting.customer_id == customer_id).all()
        tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == customer_id).all()
        
        # 2. Extract Sentiments
        sentiments = []
        for e in emails:
            sentiments.append(e.sentiment_score)
        for m in meetings:
            sentiments.append(m.sentiment_score)
        for t in tickets:
            sentiments.append(t.sentiment_score)
            
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # 3. Analyze Collaboration via Work IQ Adapter
        work_iq_data = work_iq_adapter.analyze_collaboration(db, customer_id)
        collab_index = work_iq_data["collaboration_index"]
        
        # 4. Perform Semantic Ticket Clustering and Trend Detection
        open_tickets = [t for t in tickets if t.status != "Resolved"]
        ticket_trends = foundry_iq_adapter.cluster_customer_tickets(tickets)
        
        # 5. Compute Customer Health Score (0-100)
        # Start at 100.0 and subtract penalties
        health = 100.0
        
        # Sentiment Penalty (neutral = 0, negative subtracts, positive adds)
        # If sentiment is -1.0 (extremely negative), deduct 35 points
        if avg_sentiment < 0.0:
            health -= abs(avg_sentiment) * 35.0
        else:
            health += avg_sentiment * 10.0  # slight boost for positive sentiment
            
        # Open tickets penalty
        open_low_count = len([t for t in open_tickets if t.priority == "Low"])
        open_med_count = len([t for t in open_tickets if t.priority == "Medium"])
        open_high_count = len([t for t in open_tickets if t.priority == "High"])
        
        ticket_penalty = (open_low_count * 2.0) + (open_med_count * 4.0) + (open_high_count * 8.0)
        health -= min(30.0, ticket_penalty)  # Cap ticket penalties at 30 points
        
        # Work IQ Collaboration Penalty (if relationship touchpoints are failing)
        # Low collaboration index deducts up to 25 points
        if collab_index < 70.0:
            health -= (70.0 - collab_index) * 0.5
            
        # Ensure health is in bounds
        customer_health_score = max(0.0, min(100.0, float(health)))
        
        # Save to Customer entity
        customer.health_score = customer_health_score
        db.commit()
        
        # Generate summary description
        explanation = f"CS Agent Evaluation: Customer health is indexed at {customer_health_score:.1f}/100. "
        if customer_health_score < 50.0:
            explanation += "Critical Health Warning! "
        elif customer_health_score < 75.0:
            explanation += "Mild Health Warning. "
        else:
            explanation += "Customer account is in a healthy operational state. "
            
        explanation += (
            f"Average sentiment is {avg_sentiment:+.2f} across {len(emails)} emails, {len(meetings)} meetings, and {len(tickets)} support tickets. "
            f"Currently has {len(open_tickets)} unresolved support ticket(s) (High Priority: {open_high_count}). "
            f"Relationship sync strength is {collab_index:.1f}% based on Work IQ logs."
        )
        
        return {
            "customer_health_score": customer_health_score,
            "sentiment_score": avg_sentiment,
            "open_tickets_count": len(open_tickets),
            "high_priority_tickets_count": open_high_count,
            "work_iq_collaboration_index": collab_index,
            "ticket_trends": ticket_trends,
            "explanation": explanation
        }

cs_agent = CustomerSuccessAgent()
