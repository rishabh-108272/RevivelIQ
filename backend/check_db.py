from app.core.database import SessionLocal
from app.models.models import User

db = SessionLocal()
users = db.query(User).all()
print(f"Total users found: {len(users)}")
for u in users:
    print(f"ID: {u.id} | Email: {u.email} | Role: {u.role} | Org: {u.organization_id}")
