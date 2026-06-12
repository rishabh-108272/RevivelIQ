from typing import Dict, Any
import datetime
from sqlalchemy.orm import Session
from app.services.agents.base import BaseAgent
from app.models.models import Customer, Contract, Invoice, SupportTicket, SimulationResult

class DecisionSimulatorAgent(BaseAgent):
    """
    Agent 6: Decision Simulator Agent
    Allows users to run "what-if" scenarios (e.g., resolving tickets, paying invoices,
    applying discounts) and projects the revised health and revenue risk indicators.
    """
    
    @property
    def name(self) -> str:
        return "DecisionSimulatorAgent"
        
    def run(self, db: Session, customer_id: int, **kwargs) -> Dict[str, Any]:
        # Gather inputs
        query = kwargs.get("query", "Custom Simulation")
        resolve_tickets = kwargs.get("resolve_tickets", False)
        clear_overdue_invoices = kwargs.get("clear_overdue_invoices", False)
        apply_renewal_discount = kwargs.get("apply_renewal_discount", False)
        discount_percentage = kwargs.get("discount_percentage", 0.0)
        
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "Customer not found."}
            
        contracts = db.query(Contract).filter(Contract.customer_id == customer_id).all()
        invoices = db.query(Invoice).filter(Invoice.customer_id == customer_id).all()
        tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == customer_id).all()
        
        # 1. Capture original (baseline) state
        orig_health = customer.health_score
        orig_churn = customer.churn_probability
        orig_rev_at_risk = customer.revenue_at_risk
        
        orig_metrics = {
            "health_score": round(orig_health, 1),
            "churn_probability": round(orig_churn, 2),
            "revenue_at_risk": round(orig_rev_at_risk, 2),
            "risk_level": customer.risk_level
        }
        
        # 2. Simulate Contract Renewal Risk
        # Find active contract
        active_contracts = [c for c in contracts if c.status == "Active"]
        renewal_score = 40.0
        contract_val = customer.revenue
        
        if active_contracts:
            target_contract = min(active_contracts, key=lambda c: c.end_date)
            contract_val = target_contract.value
            remaining_days = (target_contract.end_date - datetime.datetime.utcnow()).days
            
            # Baseline renewal risk
            if remaining_days <= 30:
                renewal_score = 85.0 + (30 - remaining_days) * 0.5
            elif remaining_days <= 90:
                renewal_score = 50.0 + (90 - remaining_days) * 0.5
            else:
                renewal_score = 20.0
                
            # Apply discount variable
            if apply_renewal_discount and discount_percentage > 0.0:
                # Offering discount reduces renewal risk
                reduction = discount_percentage * 150.0  # 10% discount -> 15 points reduction
                renewal_score = max(10.0, renewal_score - reduction)
                contract_val = contract_val * (1.0 - (discount_percentage / 100.0))
        
        # 3. Simulate Payment Overdue Risk
        overdue_invoices = [i for i in invoices if i.status == "Overdue"]
        payment_score = 0.0
        max_overdue_days = 0
        total_overdue_amt = sum(inv.amount for inv in overdue_invoices)
        
        if overdue_invoices and not clear_overdue_invoices:
            # Baseline overdue indicators
            for inv in overdue_invoices:
                overdue_days = (datetime.datetime.utcnow() - inv.due_date).days
                if overdue_days > max_overdue_days:
                    max_overdue_days = overdue_days
            if max_overdue_days > 45:
                payment_score = 85.0
            else:
                payment_score = 50.0
            if total_overdue_amt > 25000:
                payment_score += 10.0
        # If clear_overdue_invoices is True, payment_score stays 0.0!
        
        # 4. Simulate Customer Success Health
        # Baseline inputs
        sentiments = [e.sentiment_score for e in customer.emails] + \
                     [m.sentiment_score for m in customer.meetings] + \
                     [t.sentiment_score for t in customer.support_tickets]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        open_tickets = [t for t in tickets if t.status != "Resolved"]
        collab_index = 80.0  # baseline
        
        if resolve_tickets:
            # Resolve all open tickets simulation
            open_tickets = []
            # Boost sentiment slightly due to issues solved
            avg_sentiment = min(1.0, avg_sentiment + 0.15)
            
        health = 100.0
        if avg_sentiment < 0.0:
            health -= abs(avg_sentiment) * 35.0
        else:
            health += avg_sentiment * 10.0
            
        # Open tickets penalty
        open_low = len([t for t in open_tickets if t.priority == "Low"])
        open_med = len([t for t in open_tickets if t.priority == "Medium"])
        open_high = len([t for t in open_tickets if t.priority == "High"])
        health -= min(30.0, (open_low * 2.0) + (open_med * 4.0) + (open_high * 8.0))
        
        # Collaboration health
        if collab_index < 70.0:
            health -= (70.0 - collab_index) * 0.5
            
        simulated_health = max(0.0, min(100.0, float(health)))
        
        # 5. Recalculate Churn Probability and Revenue at Risk
        cs_risk = 100.0 - simulated_health
        weighted_score = (renewal_score * 0.35) + (payment_score * 0.25) + (cs_risk * 0.40)
        simulated_churn = max(0.0, min(1.0, weighted_score / 100.0))
        
        # Simulated revenue at risk
        simulated_rev_at_risk = round(simulated_churn * contract_val, 2)
        
        sim_risk_level = "Low"
        if simulated_churn >= 0.60:
            sim_risk_level = "High"
        elif simulated_churn >= 0.30:
            sim_risk_level = "Medium"
            
        simulated_metrics = {
            "health_score": round(simulated_health, 1),
            "churn_probability": round(simulated_churn, 2),
            "revenue_at_risk": round(simulated_rev_at_risk, 2),
            "risk_level": sim_risk_level
        }
        
        # 6. Generate Explanation Narrative
        deltas = []
        if resolve_tickets:
            deltas.append("resolving all unresolved support tickets")
        if clear_overdue_invoices:
            deltas.append("clearing all overdue invoices")
        if apply_renewal_discount:
            deltas.append(f"offering a {discount_percentage}% contract renewal discount")
            
        delta_str = " + ".join(deltas) if deltas else "no actions taken"
        
        health_diff = simulated_metrics["health_score"] - orig_metrics["health_score"]
        churn_diff = (simulated_metrics["churn_probability"] - orig_metrics["churn_probability"]) * 100
        rev_diff = simulated_metrics["revenue_at_risk"] - orig_metrics["revenue_at_risk"]
        
        explanation = (
            f"Simulated impact of {delta_str}:\n"
            f"• Customer Health Score changes by **{health_diff:+.1f}** points (from {orig_metrics['health_score']} to {simulated_metrics['health_score']}).\n"
            f"• Churn Probability changes by **{churn_diff:+.0f}%** (from {int(orig_metrics['churn_probability']*100)}% to {int(simulated_metrics['churn_probability']*100)}%).\n"
            f"• Revenue at Risk changes by **${rev_diff:+,.2f}** (from ${orig_metrics['revenue_at_risk']:,.2f} to ${simulated_metrics['revenue_at_risk']:,.2f})."
        )
        
        # Save Simulation Result in Database
        sim_record = SimulationResult(
            customer_id=customer_id,
            query=query,
            variables_modified={
                "resolve_tickets": resolve_tickets,
                "clear_overdue_invoices": clear_overdue_invoices,
                "apply_renewal_discount": apply_renewal_discount,
                "discount_percentage": discount_percentage
            },
            original_metrics_json=orig_metrics,
            simulated_metrics_json=simulated_metrics,
            explanation=explanation
        )
        db.add(sim_record)
        db.commit()
        
        # Ensure we return the ID too
        return {
            "id": sim_record.id,
            "customer_id": customer_id,
            "query": query,
            "variables_modified": sim_record.variables_modified,
            "original_metrics_json": orig_metrics,
            "simulated_metrics_json": simulated_metrics,
            "explanation": explanation,
            "created_at": sim_record.created_at
        }

decision_simulator = DecisionSimulatorAgent()
