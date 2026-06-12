import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import Customer, Contract, Invoice, SupportTicket

class OrganizationSimulator:
    """
    Simulates organization-level operational changes and projects metrics shifts:
    - projected churn reduction
    - projected revenue protected
    - projected health score improvement
    """

    def run_simulation(self, db: Session, organization_id: int, scenario: str) -> Dict[str, Any]:
        customers = db.query(Customer).filter(Customer.organization_id == organization_id).all()
        if not customers:
            return {
                "scenario": scenario,
                "projected_churn_reduction": 0.0,
                "projected_revenue_protected": 0.0,
                "projected_health_score_improvement": 0.0,
                "explanation": "No customer records available to simulate."
            }

        # Scenarios mapping
        # 1. Reduce support response time by 50%
        # 2. Resolve all high priority tickets
        # 3. Improve renewal conversion by 20%
        # 4. Reduce payment delays by 30%

        total_baseline_churn = 0.0
        total_simulated_churn = 0.0
        total_baseline_rev_at_risk = 0.0
        total_simulated_rev_at_risk = 0.0
        total_baseline_health = 0.0
        total_simulated_health = 0.0

        for cust in customers:
            contracts = db.query(Contract).filter(Contract.customer_id == cust.id).all()
            invoices = db.query(Invoice).filter(Invoice.customer_id == cust.id).all()
            tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == cust.id).all()

            # --- Calculate baseline inputs ---
            active_contracts = [c for c in contracts if c.status == "Active"]
            renewal_score = 40.0
            if active_contracts:
                next_expiring = min(active_contracts, key=lambda c: c.end_date)
                remaining_days = (next_expiring.end_date - datetime.datetime.utcnow()).days
                if remaining_days <= 30:
                    renewal_score = 85.0 + (30 - remaining_days) * 0.5
                elif remaining_days <= 90:
                    renewal_score = 50.0 + (90 - remaining_days) * 0.5
                else:
                    renewal_score = 20.0

            overdue_invoices = [i for i in invoices if i.status == "Overdue"]
            payment_score = 0.0
            max_overdue_days = 0
            if overdue_invoices:
                for inv in overdue_invoices:
                    overdue_days = (datetime.datetime.utcnow() - inv.due_date).days
                    if overdue_days > max_overdue_days:
                        max_overdue_days = overdue_days
                payment_score = 85.0 if max_overdue_days > 45 else 50.0
                if sum(i.amount for i in overdue_invoices) > 25000:
                    payment_score += 10.0

            open_tickets = [t for t in tickets if t.status != "Resolved"]
            open_low = len([t for t in open_tickets if t.priority == "Low"])
            open_med = len([t for t in open_tickets if t.priority == "Medium"])
            open_high = len([t for t in open_tickets if t.priority == "High"])

            sentiments = [e.sentiment_score for e in cust.emails] + \
                         [m.sentiment_score for m in cust.meetings] + \
                         [t.sentiment_score for t in tickets]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

            # --- Baseline Health Calculation ---
            health = 100.0
            if avg_sentiment < 0.0:
                health -= abs(avg_sentiment) * 35.0
            else:
                health += avg_sentiment * 10.0
            ticket_penalty = (open_low * 2.0) + (open_med * 4.0) + (open_high * 8.0)
            health -= min(30.0, ticket_penalty)
            baseline_health = max(0.0, min(100.0, float(health)))

            # --- Scenario modifications ---
            sim_renewal_score = renewal_score
            sim_payment_score = payment_score
            sim_open_low = open_low
            sim_open_med = open_med
            sim_open_high = open_high
            sim_avg_sentiment = avg_sentiment
            extra_health_boost = 0.0

            if scenario == "support_time":
                # Reduce response time by 50%: boosts health directly by 6 points on active accounts,
                # representing high resolution speed.
                extra_health_boost = 6.0
                sim_avg_sentiment = min(1.0, sim_avg_sentiment + 0.1)
            elif scenario == "resolve_high":
                # Resolve all high priority tickets: sets open high priority ticket count to 0
                sim_open_high = 0
                sim_avg_sentiment = min(1.0, sim_avg_sentiment + 0.15)
            elif scenario == "improve_renewal":
                # Improve renewal conversion by 20%: reduces renewal risk score by 20%
                sim_renewal_score = max(10.0, renewal_score * 0.8)
            elif scenario == "reduce_payment":
                # Reduce payment delays by 30%: reduces payment risk score by 30%
                sim_payment_score = payment_score * 0.7

            # --- Calculate Simulated Health ---
            sim_health_base = 100.0
            if sim_avg_sentiment < 0.0:
                sim_health_base -= abs(sim_avg_sentiment) * 35.0
            else:
                sim_health_base += sim_avg_sentiment * 10.0
            sim_ticket_penalty = (sim_open_low * 2.0) + (sim_open_med * 4.0) + (sim_open_high * 8.0)
            sim_health_base -= min(30.0, sim_ticket_penalty)
            simulated_health = max(0.0, min(100.0, float(sim_health_base + extra_health_boost)))

            # --- Re-evaluate churn probability ---
            # Churn Probability = 35% Contract, 25% Payment, 40% CS Health Deficit
            baseline_cs_deficit = 100.0 - baseline_health
            sim_cs_deficit = 100.0 - simulated_health

            baseline_weighted = (renewal_score * 0.35) + (payment_score * 0.25) + (baseline_cs_deficit * 0.40)
            sim_weighted = (sim_renewal_score * 0.35) + (sim_payment_score * 0.25) + (sim_cs_deficit * 0.40)

            baseline_churn = max(0.0, min(1.0, baseline_weighted / 100.0))
            simulated_churn = max(0.0, min(1.0, sim_weighted / 100.0))

            baseline_rev_at_risk = baseline_churn * cust.revenue
            simulated_rev_at_risk = simulated_churn * cust.revenue

            # Accumulate
            total_baseline_churn += baseline_churn
            total_simulated_churn += simulated_churn
            total_baseline_rev_at_risk += baseline_rev_at_risk
            total_simulated_rev_at_risk += simulated_rev_at_risk
            total_baseline_health += baseline_health
            total_simulated_health += simulated_health

        # Compute Aggregated Deltas
        n = len(customers)
        avg_baseline_churn = total_baseline_churn / n
        avg_simulated_churn = total_simulated_churn / n
        churn_reduction_pct = (avg_baseline_churn - avg_simulated_churn) * 100.0

        revenue_protected = total_baseline_rev_at_risk - total_simulated_rev_at_risk
        avg_health_improvement = (total_simulated_health - total_baseline_health) / n

        # Write Scenario explanation
        if scenario == "support_time":
            explanation = (
                f"Reducing support response time by 50% boosts customer success scores and collaboration trust. "
                f"This simulates an average health score gain of **{avg_health_improvement:+.1f} points** portfolio-wide, "
                f"decreasing the average churn probability by **{churn_reduction_pct:.1f}%** and shielding **${revenue_protected:,.2f}** in exposed contracts."
            )
        elif scenario == "resolve_high":
            explanation = (
                f"Resolving all high priority tickets resolves critical service blocks immediately. "
                f"This eliminates ticket risk penalties on enterprise accounts, resulting in an average customer health "
                f"increase of **{avg_health_improvement:+.1f} points** and protecting **${revenue_protected:,.2f}** in at-risk revenue."
            )
        elif scenario == "improve_renewal":
            explanation = (
                f"Improving renewal conversion by 20% (via renegotiations, customer loyalty offers, or feature additions) "
                f"stabilizes imminent contract expirations. This reduces contract renew risk, protecting **${revenue_protected:,.2f}** in renewal contract values "
                f"and reducing churn probabilities by **{churn_reduction_pct:.1f}%**."
            )
        else:
            explanation = (
                f"Reducing payment delays by 30% via collection mediation and proactive invoicing reminders "
                f"restores standard billing cash flow cycles. This reduces delinquent payment risk, protecting **${revenue_protected:,.2f}** "
                f"in exposed revenue by stabilizing account billing holds."
            )

        return {
            "scenario": scenario,
            "projected_churn_reduction": round(churn_reduction_pct, 2),
            "projected_revenue_protected": round(revenue_protected, 2),
            "projected_health_score_improvement": round(avg_health_improvement, 2),
            "explanation": explanation
        }

org_simulator = OrganizationSimulator()
