import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db_connection(max_retries: int = 5, delay: int = 2):
    """
    Connects to the database with a retry mechanism.
    Executes 'CREATE EXTENSION IF NOT EXISTS vector;' to ensure pgvector is active.
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Connecting to database (Attempt {attempt}/{max_retries})...")
            # Try to connect
            with engine.connect() as conn:
                # Enable pgvector extension
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                print("Successfully connected to PostgreSQL and verified pgvector extension.")
                return True
        except OperationalError as e:
            last_error = e
            print(f"Database connection failed. Retrying in {delay} seconds...")
            time.sleep(delay)
    
    print("Failed to connect to the database after all attempts.")
    if last_error:
        raise last_error
    return False
