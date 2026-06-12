import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tenant_id = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="organization", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="Customer Success")  # Admin, Finance, Sales, Customer Success
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    organization = relationship("Organization", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    revenue = Column(Float, default=0.0)
    health_score = Column(Float, default=100.0)  # 0 to 100
    churn_probability = Column(Float, default=0.0)  # 0.0 to 1.0
    revenue_at_risk = Column(Float, default=0.0)
    risk_level = Column(String(50), default="Low")  # High, Medium, Low
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    organization = relationship("Organization", back_populates="customers")
    contracts = relationship("Contract", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="customer", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="customer", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="customer", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="customer", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="customer", cascade="all, delete-orphan")
    simulations = relationship("SimulationResult", back_populates="customer", cascade="all, delete-orphan")
    campaigns = relationship("RevenueRescueCampaign", back_populates="customer", cascade="all, delete-orphan")

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    value = Column(Float, default=0.0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    renewal_risk_score = Column(Float, default=0.0)  # 0.0 to 100.0
    status = Column(String(50), default="Active")  # Active, Renewed, Expired
    risk_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="contracts")

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(50), default="Unpaid")  # Paid, Unpaid, Overdue
    payment_risk_score = Column(Float, default=0.0)  # 0.0 to 100.0
    payment_delay_prediction_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="invoices")

class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    sentiment = Column(String(50), nullable=True)  # Positive, Neutral, Negative
    sentiment_score = Column(Float, default=0.0)  # -1.0 to 1.0
    date = Column(DateTime, nullable=False)
    vector_embedding = Column(Vector(384), nullable=True)  # 384 dimensions for semantic search
    
    customer = relationship("Customer", back_populates="emails")

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    sentiment_score = Column(Float, default=0.0)  # -1.0 to 1.0
    attendees = Column(JSON, nullable=True)  # List of emails
    date = Column(DateTime, nullable=False)
    vector_embedding = Column(Vector(384), nullable=True)
    
    customer = relationship("Customer", back_populates="meetings")

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="Open")  # Open, In Progress, Resolved
    priority = Column(String(50), default="Medium")  # Low, Medium, High
    sentiment_score = Column(Float, default=0.0)  # -1.0 to 1.0
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    vector_embedding = Column(Vector(384), nullable=True)
    
    customer = relationship("Customer", back_populates="support_tickets")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    contract_risk_score = Column(Float, default=0.0)
    payment_risk_score = Column(Float, default=0.0)
    customer_health_score = Column(Float, default=100.0)
    sentiment_score = Column(Float, default=0.0)
    aggregate_churn_prob = Column(Float, default=0.0)
    aggregate_revenue_at_risk = Column(Float, default=0.0)
    risk_level = Column(String(50), default="Low")
    explainability_json = Column(JSON, nullable=True)  # Key reasons and scores
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="risk_assessments")

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    action_type = Column(String(100), nullable=False)  # Review, Discount, Support, Priority Outreach
    priority = Column(String(50), default="Medium")  # High, Medium, Low
    status = Column(String(50), default="Pending")  # Pending, Approved, Rejected, Completed
    revenue_impact_estimate = Column(Float, default=0.0)  # Gross value at stake
    cost_to_execute = Column(Float, default=0.0)
    net_recovery_value = Column(Float, default=0.0)  # Projected recovered value
    impact_projection = Column(Text, nullable=True)  # Qualitative explanation of simulated effect
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="recommendations")

class SimulationResult(Base):
    __tablename__ = "simulation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    query = Column(Text, nullable=False)  # User question e.g. "What if open tickets resolved?"
    variables_modified = Column(JSON, nullable=False)  # modified parameters
    original_metrics_json = Column(JSON, nullable=False)  # Before state
    simulated_metrics_json = Column(JSON, nullable=False)  # After state
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="simulations")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)  # e.g., UPDATE_RECOMMENDATION, LOGIN
    target_table = Column(String(100), nullable=True)
    target_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, nullable=True)
    
    user = relationship("User", back_populates="audit_logs")

class RevenueRescueCampaign(Base):
    __tablename__ = "revenue_rescue_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    
    executive_recommendation = Column(Text, nullable=False)
    customer_success_plan = Column(Text, nullable=False)
    finance_plan = Column(Text, nullable=False)
    renewal_strategy = Column(Text, nullable=False)
    outreach_timeline = Column(JSON, nullable=False)
    
    estimated_revenue_protected = Column(Float, default=0.0)
    estimated_execution_cost = Column(Float, default=0.0)
    net_recovery_value = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    customer = relationship("Customer", back_populates="campaigns")

class RevenueCrisisAlert(Base):
    __tablename__ = "revenue_crisis_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    title = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    potential_revenue_loss = Column(Float, default=0.0)
    root_cause = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
