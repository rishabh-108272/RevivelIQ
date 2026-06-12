import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Email, Meeting

class MicrosoftWorkIQAdapter:
    """
    Work IQ Integration: Translates organizational collaboration metrics
    (email response times, calendar meeting density, and communication drop-offs)
    into customer risk signals.
    """
    
    def analyze_collaboration(self, db: Session, customer_id: int) -> Dict[str, Any]:
        """
        Retrieves interaction history from the database to evaluate touchpoint density
        and collaboration gaps.
        """
        emails = db.query(Email).filter(Email.customer_id == customer_id).all()
        meetings = db.query(Meeting).filter(Meeting.customer_id == customer_id).all()
        
        total_emails = len(emails)
        total_meetings = len(meetings)
        
        # 1. Calculate Average Response Latency (Mocked or calculated based on email metadata)
        # In a real environment, we compare incoming timestamps to outgoing response timestamps
        avg_latency_hours = self._calculate_latency(emails)
        
        # 2. Touchpoint Density (meetings/emails in last 30 days)
        now = datetime.datetime.utcnow()
        thirty_days_ago = now - datetime.timedelta(days=30)
        
        recent_emails = [e for e in emails if e.date >= thirty_days_ago]
        recent_meetings = [m for m in meetings if m.date >= thirty_days_ago]
        
        recent_activity_count = len(recent_emails) + len(recent_meetings)
        
        # 3. Collaboration index calculation (0-100 score where higher is healthier collaboration)
        base_score = 70.0
        
        # Latency penalty
        if avg_latency_hours > 48:
            base_score -= 20.0
        elif avg_latency_hours > 24:
            base_score -= 10.0
        else:
            base_score += 10.0
            
        # Recent touchpoints bonus/penalty
        if recent_activity_count == 0:
            base_score -= 25.0
            silence_risk = True
        elif recent_activity_count < 3:
            base_score -= 10.0
            silence_risk = False
        else:
            base_score += 15.0
            silence_risk = False
            
        # Keep score inside 0-100 range
        collaboration_index = max(0.0, min(100.0, base_score))
        
        # 4. Generate Narrative Description
        if silence_risk:
            description = "Critical Work IQ alert: No email communications or calendar meetings recorded in the last 30 days."
        elif avg_latency_hours > 36:
            description = f"Elevated latency alert: Average response time to client emails is {avg_latency_hours:.1f} hours, signaling slow resolution rates."
        else:
            description = f"Healthy collaboration status: Regular communications and active meeting syncs detected (Index: {collaboration_index:.1f})."
            
        return {
            "collaboration_index": collaboration_index,
            "avg_latency_hours": avg_latency_hours,
            "recent_activity_count": recent_activity_count,
            "silence_risk": silence_risk,
            "total_emails_analyzed": total_emails,
            "total_meetings_analyzed": total_meetings,
            "description": description
        }
        
    def _calculate_latency(self, emails: List[Email]) -> float:
        """Helper to calculate email response latency in hours."""
        if not emails or len(emails) < 2:
            return 18.5  # Standard baseline delay in hours
            
        # In standard synthetic dataset, we will simulate a reasonable latency variation
        # Higher index/heavier topics tend to yield longer responses
        total_diff_hours = 0.0
        pair_count = 0
        
        # Sort emails by date
        sorted_emails = sorted(emails, key=lambda x: x.date)
        
        for i in range(len(sorted_emails) - 1):
            e1 = sorted_emails[i]
            e2 = sorted_emails[i+1]
            # If e1 is from customer and e2 is from us, it's a response
            if "reviveiq.com" in e2.sender and "reviveiq.com" not in e1.sender:
                diff = e2.date - e1.date
                diff_hours = diff.total_seconds() / 3600.0
                total_diff_hours += diff_hours
                pair_count += 1
                
        if pair_count > 0:
            return total_diff_hours / pair_count
        return 14.2
        
work_iq_adapter = MicrosoftWorkIQAdapter()
