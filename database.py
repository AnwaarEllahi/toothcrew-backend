# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Using SQLite file called test.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# For sqlite we need check_same_thread=False
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Optional: quick test connection when module loads
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connected:", result.scalar())
    except Exception as e:
        print("❌ Database connection failed:", str(e))

test_connection()
