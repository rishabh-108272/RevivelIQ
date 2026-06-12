import sys
import os

# Add root folder to python path so app is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine, init_db_connection
from app.core.security import get_password_hash
from app.models.models import Organization, User
from app.utils.synthetic_generator import generate_synthetic_data
from app.services.agents.orchestrator import orchestrator

def seed_db(db: Session):
    """Initializes and populates the database with default organization, users, and risk analysis."""
    print("Initializing Database tables...")
    # This creates the vector extension (inside init_db_connection) and tables
    Base.metadata.create_all(bind=engine)
    
    # Check if Organization already exists
    org = db.query(Organization).filter(Organization.tenant_id == "m365-ent-100").first()
    if not org:
        print("Creating default organization...")
        org = Organization(
            name="Contoso Microsoft Enterprise",
            tenant_id="m365-ent-100"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    
    # Create default users for each role if they don't exist
    default_users = [
        {"email": "admin@reviveiq.com", "name": "Arianne Admin", "role": "Admin", "password": "admin123"},
        {"email": "finance@reviveiq.com", "name": "Fiona Finance", "role": "Finance", "password": "finance123"},
        {"email": "sales@reviveiq.com", "name": "Sam Sales", "role": "Sales", "password": "sales123"},
        {"email": "cs@reviveiq.com", "name": "Connor Success", "role": "Customer Success", "password": "cs123"}
    ]
    
    for user_info in default_users:
        user = db.query(User).filter(User.email == user_info["email"]).first()
        if not user:
            print(f"Creating default user: {user_info['email']} ({user_info['role']})...")
            user = User(
                email=user_info["email"],
                hashed_password=get_password_hash(user_info["password"]),
                full_name=user_info["name"],
                role=user_info["role"],
                organization_id=org.id
            )
            db.add(user)
    db.commit()
    
    # Generate Synthetic Client Dataset (100 customers, 500 invoices, 100 contracts, 1000 interactions, 500 tickets)
    print("Generating synthetic enterprise dataset (this will take a moment)...")
    customer_count = generate_synthetic_data(db, org.id)
    
    # Run the Multi-Agent Pipeline sync over the seeded portfolio
    # This pre-calculates and caches the health scores, payment delays, churn probabilities, and recovery recommendations!
    print("Syncing multi-agent scores and generating briefings (pre-populating caching layers)...")
    orchestrator.run_portfolio_sync(db, org.id, user_id=None)
    
    print("Database seeding and metrics initialization completed successfully!")

if __name__ == "__main__":
    print("Starting database seeding process...")
    # Wait for DB connection
    if init_db_connection(max_retries=10, delay=3):
        db = SessionLocal()
        try:
            seed_db(db)
        finally:
            db.close()
    else:
        print("Error: Could not connect to database. Seeding aborted.")
        sys.exit(1)
