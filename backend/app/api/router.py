from fastapi import APIRouter
from app.api.endpoints import auth, customers, contracts, invoices, risk_assessments, recommendations, simulations, analytics, copilot, campaigns, alerts, reports

api_router = APIRouter()

# Mount endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(risk_assessments.router, prefix="/risk-assessments", tags=["Risk Assessments"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["Simulations"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["Copilot Extensibility"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Crisis Alerts"])
api_router.include_router(reports.router, prefix="/reports", tags=["Executive Reports"])
