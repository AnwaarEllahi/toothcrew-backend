# database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL connection URL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:pakistan@localhost:5432/myappdb"

# Create PostgreSQL engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session and base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Optional: test database connection
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ PostgreSQL connected:", result.scalar())
    except Exception as e:
        print("❌ Database connection failed:", str(e))

test_connection()
