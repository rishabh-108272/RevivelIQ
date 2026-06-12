from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, init_db_connection, SessionLocal
from app.api.router import api_router
from app.models.models import Organization
from app.utils.seed import seed_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Multi-agent AI platform identifying customer renewal and late payment risks for Microsoft 365 Copilot."
)

# Set up CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    """Startup initialization: checks database connection, establishes schemas, and auto-seeds if empty."""
    print("Executing startup verification checks...")
    try:
        # 1. Establish connection and enable pgvector extension
        db_connected = init_db_connection(max_retries=5, delay=2)
        if not db_connected:
            print("Warning: Startup database connection failed. Auto-seeding will be deferred.")
            return
            
        # 2. Synchronize schemas
        Base.metadata.create_all(bind=engine)
        
        # 3. Auto-seed if database is empty
        db = SessionLocal()
        try:
            org_count = db.query(Organization).count()
            if org_count == 0:
                print("Database appears empty. Launching automated synthetic seeder...")
                seed_db(db)
            else:
                print("Database state exists. Skipping auto-seeding cycle.")
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error during startup lifecycle: {e}")

@app.get("/reports/board")
def direct_board_report_redirect(format: str = "markdown"):
    """Bypasses API prefix prefix routing and redirects to the official reports endpoint."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/api/reports/board?format={format}")

@app.get("/")
def root_check():
    """Root health verification endpoint."""
    return {
        "status": "healthy",
        "service": "ReviveIQ API Engine",
        "version": "1.0.0",
        "copilot_compatible": True
    }
