# create_admin.py
from database import SessionLocal, Base, engine
import models
from auth import hash_password

# ensure tables exist
Base.metadata.create_all(bind=engine)

def create_admin():
    db = SessionLocal()
    try:
        email = "admin@example.com"
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            print("Admin already exists:", existing.email)
            return

        admin = models.User(
            name="Admin User",
            email=email,
            role="admin",
            password=hash_password("AdminPass123")  # change password after first login
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("Created admin:", admin.email, "password: AdminPass123")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
