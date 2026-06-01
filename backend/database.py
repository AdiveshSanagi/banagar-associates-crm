from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load variables from your .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/banagar_db")

# Create the connection engine for MySQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Checks if connection is alive before sending queries
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to open/close database sessions cleanly
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()