from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import Customer, User, AuditLog
from app.services.agents.contract_agent import contract_agent
from app.services.agents.payment_agent import payment_agent
from app.services.agents.cs_agent import cs_agent
from app.services.agents.revenue_risk_agent import revenue_risk_agent
from app.services.agents.revenue_recovery_agent import recovery_agent
from app.services.agents.executive_briefing_agent import executive_briefing_agent

class AgentOrchestrator:
    """
    Coordinates execution parameters and flow schedules between all ReviveIQ agents.
    Performs full portfolio synchronizations and updates client metrics caches.
    """
    
    def run_customer_pipeline(self, db: Session, customer_id: int, user_id: int = None) -> Dict[str, Any]:
        """
        Runs the full intelligence pipeline for a specific customer.
        1. Contract Agent -> renewal_risk_score
        2. Payment Agent -> payment_risk_score
        3. CS Agent -> customer_health_score, sentiment_score, semantic clusters
        4. Revenue Risk Agent -> Churn probability, Revenue at Risk, Risk level, explainability
        5. Recovery Agent -> Recommended tasks with financial metrics
        """
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "Customer not found."}
            
        print(f"Orchestrator: Starting pipeline execution for Customer ID: {customer_id} ({customer.name})...")
        
        # Execute agents in logical dependency order
        contract_res = contract_agent.run(db, customer_id)
        payment_res = payment_agent.run(db, customer_id)
        cs_res = cs_agent.run(db, customer_id)
        risk_res = revenue_risk_agent.run(db, customer_id)
        recovery_res = recovery_agent.run(db, customer_id)
        
        # Trigger Campaign Generation if risk score (churn_probability) exceeds threshold
        from app.core.config import settings
        from app.services.campaign_generator import generate_rescue_campaign
        if risk_res["churn_probability"] >= settings.RESCUE_CAMPAIGN_THRESHOLD:
            print(f"Orchestrator: Customer ID {customer_id} risk exceeds threshold ({risk_res['churn_probability']:.2f} >= {settings.RESCUE_CAMPAIGN_THRESHOLD:.2f}). Generating Rescue Campaign...")
            generate_rescue_campaign(db, customer_id)
        
        # Add Audit Log entry
        log_entry = AuditLog(
            user_id=user_id,
            action="RUN_RISK_PIPELINE",
            target_table="customers",
            target_id=customer_id,
            details={
                "customer_name": customer.name,
                "risk_level": risk_res["risk_level"],
                "churn_probability": risk_res["churn_probability"],
                "revenue_at_risk": risk_res["revenue_at_risk"]
            }
        )
        db.add(log_entry)
        db.commit()
        
        print(f"Orchestrator: Pipeline execution complete. Risk Level: {risk_res['risk_level']}.")
        
        return {
            "customer_id": customer_id,
            "customer_name": customer.name,
            "contract_analysis": contract_res,
            "payment_analysis": payment_res,
            "customer_success_analysis": cs_res,
            "revenue_risk_analysis": risk_res,
            "recovery_recommendations": recovery_res
        }

    def run_portfolio_sync(self, db: Session, organization_id: int, user_id: int = None) -> Dict[str, Any]:
        """Runs the intelligence pipeline for all customers under the organization, then updates briefings."""
        customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
        
        print(f"Orchestrator: Syncing portfolio for Org ID: {organization_id} ({len(customers)} accounts)...")
        
        sync_results = []
        for cust in customers:
            res = self.run_customer_pipeline(db, cust.id, user_id)
            sync_results.append({
                "customer_id": cust.id,
                "name": cust.name,
                "risk_level": res["revenue_risk_analysis"]["risk_level"]
            })
            
        # Trigger Executive Briefing synthesis
        briefing = executive_briefing_agent.run(db, organization_id)
        
        # Trigger Revenue Crisis portfolio-wide analysis
        from app.services.agents.revenue_crisis_agent import revenue_crisis_agent
        revenue_crisis_agent.run(db, organization_id)
        
        # Add Audit Log entry
        log_entry = AuditLog(
            user_id=user_id,
            action="RUN_PORTFOLIO_SYNC",
            target_table="organizations",
            target_id=organization_id,
            details={"accounts_synced": len(customers)}
        )
        db.add(log_entry)
        db.commit()
        
        return {
            "accounts_synced": len(customers),
            "results": sync_results,
            "executive_briefing": briefing
        }

orchestrator = AgentOrchestrator()
