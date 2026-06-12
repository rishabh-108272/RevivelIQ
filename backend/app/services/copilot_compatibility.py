from typing import List, Dict, Any
from app.models.models import Customer, Contract, Invoice, Recommendation

class CopilotCompatibilityHelper:
    """
    Transforms backend structures into Microsoft Adaptive Cards JSON formats
    compliant with Microsoft 365 Copilot and Teams extensibility specifications.
    """
    
    def generate_customer_risk_card(self, customer: Customer, contract: Contract, overdue_invoices: List[Invoice]) -> Dict[str, Any]:
        """Generates an Adaptive Card showing a single customer's risk profile."""
        overdue_amt = sum(inv.amount for inv in overdue_invoices)
        overdue_count = len(overdue_invoices)
        
        # Select style color based on risk level
        risk_color = "Attention" if customer.risk_level == "High" else ("Warning" if customer.risk_level == "Medium" else "Good")
        
        facts = [
            {"title": "Industry", "value": customer.industry or "Unknown"},
            {"title": "Risk Level", "value": f"{customer.risk_level} ({int(customer.churn_probability * 100)}%)"},
            {"title": "Revenue at Risk", "value": f"${customer.revenue_at_risk:,.2f}"},
            {"title": "Total Revenue", "value": f"${customer.revenue:,.2f}"}
        ]
        
        if contract:
            facts.append({"title": "Contract Renewal", "value": f"{contract.end_date.strftime('%Y-%m-%d')} (${contract.value:,.2f})"})
            
        facts.append({"title": "Overdue Invoices", "value": f"{overdue_count} invoice(s) totalling ${overdue_amt:,.2f}"})
        
        card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "ReviveIQ - Customer Churn Risk Flag",
                            "weight": "Bolder",
                            "size": "Medium",
                            "color": "Accent"
                        }
                    ]
                },
                {
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"Customer Profile: {customer.name}",
                            "weight": "Bolder",
                            "size": "Large"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Status: Alert state verified. System indicates high probability of revenue leakage.",
                            "isSubtle": True,
                            "wrap": True
                        }
                    ]
                },
                {
                    "type": "FactSet",
                    "facts": facts
                },
                {
                    "type": "Container",
                    "style": risk_color,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"Recommended Action: Review Customer Detail Dashboard and execute recovery plans immediately.",
                            "weight": "Bolder",
                            "wrap": True
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "Open ReviveIQ Dashboard",
                    "url": f"https://reviveiq.azurewebsites.net/customers/{customer.id}"
                }
            ]
        }
        return card

    def generate_executive_briefing_card(self, total_at_risk: float, high_risk_count: int, top_accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generates an Adaptive Card summarizing the corporate-wide risk profile."""
        
        facts = [
            {"title": "Total Revenue at Risk", "value": f"${total_at_risk:,.2f}"},
            {"title": "High Risk Accounts", "value": str(high_risk_count)}
        ]
        
        body_elements = [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "ReviveIQ - Executive Revenue Recovery Briefing",
                        "weight": "Bolder",
                        "size": "Medium",
                        "color": "Accent"
                    }
                ]
            },
            {
                "type": "TextBlock",
                "text": "Corporate Risk Exposure Summary",
                "weight": "Bolder",
                "size": "Large"
            },
            {
                "type": "FactSet",
                "facts": facts
            },
            {
                "type": "TextBlock",
                "text": "Top At-Risk Accounts:",
                "weight": "Bolder",
                "size": "Medium",
                "spacing": "Medium"
            }
        ]
        
        # Add top 3 accounts as bullet items
        for acc in top_accounts[:3]:
            body_elements.append({
                "type": "TextBlock",
                "text": f"• **{acc.get('name')}**: ${acc.get('revenue_at_risk'):,.0f} at risk ({acc.get('risk_level')} risk)",
                "wrap": True
            })
            
        card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": body_elements,
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "Launch Executive Control Panel",
                    "url": "https://reviveiq.azurewebsites.net/dashboard"
                }
            ]
        }
        return card

    def generate_recommendation_card(self, rec: Recommendation) -> Dict[str, Any]:
        """Generates an Adaptive Card for a single recommendation action."""
        
        color_map = {"High": "Attention", "Medium": "Warning", "Low": "Good"}
        priority_color = color_map.get(rec.priority, "Default")
        
        card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "ReviveIQ - Recommendation Outreach Action",
                            "weight": "Bolder",
                            "size": "Medium",
                            "color": "Accent"
                        }
                    ]
                },
                {
                    "type": "TextBlock",
                    "text": rec.title,
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "TextBlock",
                    "text": rec.description,
                    "wrap": True
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "Action Type", "value": rec.action_type},
                        {"title": "Priority", "value": rec.priority},
                        {"title": "Net Recovery Value", "value": f"${rec.net_recovery_value:,.2f}"},
                        {"title": "Estimated Cost", "value": f"${rec.cost_to_execute:,.2f}"}
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Approve Outreach",
                    "data": {
                        "action": "approve_recommendation",
                        "recommendation_id": rec.id
                    }
                }
            ]
        }
        return card

copilot_helper = CopilotCompatibilityHelper()
