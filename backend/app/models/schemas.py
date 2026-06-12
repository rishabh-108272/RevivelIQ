from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, Field

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    email: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "Customer Success"

class UserCreate(UserBase):
    password: str
    organization_name: str  # For signups, creates an org too

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    industry: Optional[str] = None
    revenue: float = 0.0

class CustomerCreate(CustomerBase):
    organization_id: int

class CustomerResponse(CustomerBase):
    id: int
    health_score: float
    churn_probability: float
    revenue_at_risk: float
    risk_level: str
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Contract Schemas
class ContractResponse(BaseModel):
    id: int
    customer_id: int
    title: str
    value: float
    start_date: datetime
    end_date: datetime
    renewal_risk_score: float
    status: str
    risk_explanation: Optional[str] = None

    class Config:
        from_attributes = True

# Invoice Schemas
class InvoiceResponse(BaseModel):
    id: int
    customer_id: int
    invoice_number: str
    amount: float
    issue_date: datetime
    due_date: datetime
    status: str
    payment_risk_score: float
    payment_delay_prediction_days: int

    class Config:
        from_attributes = True

# Communications & Support Ticket Schemas
class EmailResponse(BaseModel):
    id: int
    sender: str
    recipient: str
    subject: str
    body: str
    sentiment: Optional[str] = None
    sentiment_score: float
    date: datetime

    class Config:
        from_attributes = True

class MeetingResponse(BaseModel):
    id: int
    title: str
    summary: str
    sentiment_score: float
    attendees: Optional[List[str]] = None
    date: datetime

    class Config:
        from_attributes = True

class SupportTicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    sentiment_score: float
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True



# Recommendation Schemas
class RecommendationResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    title: str
    description: str
    action_type: str
    priority: str
    status: str
    revenue_impact_estimate: float
    cost_to_execute: float
    net_recovery_value: float
    impact_projection: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RecommendationUpdate(BaseModel):
    status: str  # Pending, Approved, Rejected, Completed

# Detailed Customer Profile Response (for Detail Page)
class CustomerDetailResponse(BaseModel):
    customer: CustomerResponse
    contracts: List[ContractResponse]
    invoices: List[InvoiceResponse]
    emails: List[EmailResponse]
    meetings: List[MeetingResponse]
    support_tickets: List[SupportTicketResponse]
    churn_probability: float
    revenue_at_risk: float
    risk_explanation: Optional[Dict[str, Any]] = None  # Struct explaining scores
    recommendations: List[RecommendationResponse] = []
    microsoft_iq_insights: Optional[Dict[str, Any]] = None

# Simulation Schemas
class SimulationCreate(BaseModel):
    customer_id: int
    query: str  # "What if we resolve all tickets?"
    resolve_tickets: bool = False
    clear_overdue_invoices: bool = False
    apply_renewal_discount: bool = False
    discount_percentage: float = 0.0

class SimulationResponse(BaseModel):
    id: Optional[int] = None
    customer_id: int
    query: str
    variables_modified: Dict[str, Any]
    original_metrics_json: Dict[str, Any]
    simulated_metrics_json: Dict[str, Any]
    explanation: str
    created_at: datetime

    class Config:
        from_attributes = True

# Copilot Query Schema
class CopilotQueryRequest(BaseModel):
    prompt: str

class CopilotQueryResponse(BaseModel):
    response_text: str
    data: Optional[Dict[str, Any]] = None
    adaptive_card: Optional[Dict[str, Any]] = None
    reasoning_trace: Optional[List[str]] = None
    supporting_evidence: Optional[Any] = None

# Analytics & Dashboard Metrics
class DashboardMetrics(BaseModel):
    total_revenue_at_risk: float
    predicted_churn_count: int
    upcoming_renewals_count: int
    overdue_invoices_count: int
    risk_distribution: Dict[str, int]  # e.g., {"High": 10, "Medium": 25, "Low": 65}
    health_trends: List[Dict[str, Any]]  # Month-by-month averages

class ExecutiveBriefingResponse(BaseModel):
    generated_at: datetime
    narrative: str
    top_accounts_at_risk: List[Dict[str, Any]]
    macro_trends: List[str]

# Revenue Rescue Campaign Response
class RevenueRescueCampaignResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    executive_recommendation: str
    customer_success_plan: str
    finance_plan: str
    renewal_strategy: str
    outreach_timeline: List[Dict[str, Any]]
    estimated_revenue_protected: float
    estimated_execution_cost: float
    net_recovery_value: float
    created_at: datetime

    class Config:
        from_attributes = True

# Revenue Crisis Alert Response
class RevenueCrisisAlertResponse(BaseModel):
    id: int
    organization_id: int
    title: str
    severity: str
    potential_revenue_loss: float
    root_cause: str
    confidence: float
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Organization Simulator response
class OrgSimulationRequest(BaseModel):
    scenario: str

class OrgSimulationResponse(BaseModel):
    scenario: str
    projected_churn_reduction: float
    projected_revenue_protected: float
    projected_health_score_improvement: float
    explanation: str
