# ReviveIQ – AI Revenue Recovery Agent for Microsoft 365 Copilot

ReviveIQ is an enterprise-grade multi-agent AI decision intelligence platform designed to proactively identify and mitigate corporate revenue risks. Built for Microsoft Enterprise Agents Hackathons, it highlights deep integration with Microsoft 365 Copilot extensibility interfaces, utilizing first-class adapters for Microsoft Work IQ, Foundry IQ, and Graph abstractions.

---

## Core Business Problem

Enterprise organizations leak revenue due to operational disconnects:
- **Invoice delays** go unnoticed, leading to working capital issues.
- **Contract renewals** expire without proactive engagement.
- **Support backlogs** go unresolved, degrading client trust.
- **Negative sentiment** builds silently across emails and sync meetings.

ReviveIQ connects these variables, evaluates risk priorities in real-time, generates explainable reasons, triggers recovery outreach term sheets, and simulates what-if recovery options for account leads.

---

## Architectural & Agent Workflow

### Multi-Agent Pipeline
The system integrates six specialized, cooperative intelligence agents:

```mermaid
graph TD
    A[Contract Intel Agent] -->|renewal_risk_score| D(Revenue Risk Agent)
    B[Payment Intel Agent] -->|payment_risk_score| D
    C[Customer Success Agent] -->|health_score & sentiment| D
    
    E[Microsoft Work IQ] -->|collaboration signals| C
    F[Microsoft Foundry IQ] -->|semantic ticket clustering| C
    
    D -->|churn_probability & revenue_at_risk| G[Revenue Recovery Agent]
    G -->|actionable outreach recommendations| H[Dashboard / Copilot UI]
    
    I[Decision Simulator Agent] -->|what-if recalculations| H
```

1. **Contract Intelligence Agent**: Predicts renewal likelihood based on expiration timelines.
2. **Payment Intelligence Agent**: Monitors aging invoices and projects billing delays.
3. **Customer Success Agent**: Evaluates client emails, ticket queues, and meeting sentiments. Integrates Work IQ collaboration patterns and Foundry IQ semantic ticket clustering.
4. **Revenue Risk Agent**: Synthesizes upstream inputs to compute churn probability, risk category, and exposed revenue.
5. **Revenue Recovery Agent**: Formulates prioritized outreach tasks, computing Gross protected revenue, execution costs, and Net Recovery values.
6. **Decision Simulator Agent**: Calculates in-memory adjustments for what-if scenarios (e.g. resolving tickets or adjusting renewal discounts).

---

## Microsoft 365 Copilot Compatibility

The application is structured to compile as a native Copilot declarative agent:
- **Work IQ Adapter**: Evaluates relationship communication touchpoints and response latency trends.
- **Foundry IQ Adapter**: Provides semantic indexing and pgvector cosine search.
- **Graph Abstractions**: Mock/Azure AD token endpoints reading calendar events and email feeds.
- **Declarative Agent Manifest (`copilot/manifest.json`)**: Configures Copilot's system prompt instructions and scopes.
- **OpenAPI Schema (`copilot/openapi.yaml`)**: Maps secure REST paths for Copilot chat queries.
- **Adaptive Cards Renderer**: Returns responses formatted as interactive Adaptive Cards v1.5.

---

## Local Installation Guide

### Prerequisites
- Python 3.11+
- Node.js v20+ & npm
- Docker Desktop with Compose support
- PostgreSQL database (if running outside Docker)

### Run via Docker Compose (Recommended)
This boots up the complete containerized stack, including the `pgvector` pre-configured database, Redis queue caches, Celery workers, FastAPI server, and Vite client:

```bash
# Clone the repository and navigate to the directory
cd ReviveIQ

# Spin up containers
docker-compose up --build
```
Once healthy, access:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI Documentation (Swagger)**: `http://localhost:8000/docs`

*Note: On first launch, the backend automatically seeds 100 mock customer accounts, 500 invoices, 100 contracts, 1000 interactions, and 500 support tickets, then runs the orchestrator pipeline to populate the dashboard metrics immediately.*

### Running Manually (Local Development)

#### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run Database initialization & seeding (Ensure PostgreSQL is running on port 5432)
# Ensure your environment variables are configured in a .env file
python app/utils/seed.py

# Launch server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000` to interact with the interface.

---

## Developer/Hackathon Quick Login Bypass
The login screen features quick-bypass buttons to simulate role-based authorization scopes:
- **System Admin** (`admin@reviveiq.com`): Full dashboard controls, manual DB reseed triggers.
- **Customer Success Lead** (`cs@reviveiq.com`): Ticket clustering analysis, support escalations approval.
- **Finance Lead** (`finance@reviveiq.com`): Receivable overdue charts, collection outreach approvals.
- **Sales Lead** (`sales@reviveiq.com`): Expiration dates tracker, rate discount approvals.

---

## Production Deployment Guide

### Deploying to Azure Container Apps (ACA)
1. **Azure Container Registry**: Build and push backend and frontend Docker images to Azure Container Registry (ACR).
2. **PostgreSQL on Azure**: Set up Azure Database for PostgreSQL (Flexible Server) and enable the `vector` extension.
3. **Azure Container Apps**: Provision two Container Apps (backend, frontend) and configure env keys (`DATABASE_URL`, `SECRET_KEY`).
4. **Redis cache**: Deploy Azure Cache for Redis and configure Celery.
