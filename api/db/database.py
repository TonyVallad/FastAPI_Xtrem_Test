from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from loguru import logger
from pathlib import Path
from sqlalchemy.orm import DeclarativeBase

# Load environment variables
load_dotenv()

# Get database URL from environment variable, default to SQLite if not set
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fastapi_xtrem.db")

# Create directory structure for database files if they don't exist
if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///"):
    db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]
    elif db_path.startswith("/"):
        db_path = db_path[1:]
    
    if "/" in db_path or "\\" in db_path:
        # Extract directory path
        dir_path = Path(os.path.dirname(db_path))
        # Create directories if they don't exist
        dir_path.mkdir(parents=True, exist_ok=True)

# Create SQLAlchemy engine
# For SQLite connect_args needed for multiple threads
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args,
    echo=os.getenv("DEBUG", "False").lower() == "true"  # Echo SQL when DEBUG is True
)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models using SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    pass

# Database Dependency
def get_db():
    """
    Dependency for getting a database session.
    Ensures the session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database by creating all tables.
    """
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.success("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

def close_db():
    """
    Close the database connections.
    """
    logger.info("Closing database connections...") 