from app.core.database import SessionLocal
from app.models.models import User
from app.core.security import get_password_hash

db = SessionLocal()
user = db.query(User).filter(User.email == "rishabhverma3648@gmail.com").first()
if user:
    user.hashed_password = get_password_hash("admin123")
    db.commit()
    print("Admin password successfully reset to admin123!")
else:
    print("Admin user rishabhverma3648@gmail.com not found.")
