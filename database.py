"""
Database configuration using SQLAlchemy for Aiven MySQL
Handles MySQL connection with SSL for Aiven
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import tempfile

# Load environment variables from .env file
load_dotenv()

# Determine if we're using Aiven (production) or local MySQL
IS_AIVEN = os.getenv("AIVEN_DB_HOST") is not None

if IS_AIVEN:
    # Aiven MySQL configuration
    DB_USER = os.getenv("AIVEN_DB_USER", "avnadmin")
    DB_PASSWORD = os.getenv("AIVEN_DB_PASSWORD")
    DB_HOST = os.getenv("AIVEN_DB_HOST")
    DB_PORT = os.getenv("AIVEN_DB_PORT", "3306")
    DB_NAME = os.getenv("AIVEN_DB_NAME", "defaultdb")
    AIVEN_CA_CERT = os.getenv("AIVEN_CA_CERT")
else:
    # Local MySQL configuration
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "voting_system")

# Create database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SSL configuration for Aiven
connect_args = {}
if IS_AIVEN and AIVEN_CA_CERT:
    try:
        # Handle multi-line certificate by replacing escaped newlines
        cert_content = AIVEN_CA_CERT.replace('\\n', '\n')
        
        # Create temporary CA certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as cert_file:
            cert_file.write(cert_content)
            ca_cert_path = cert_file.name
        
        # For Aiven MySQL, we need to use ssl_ca parameter
        connect_args = {
            "ssl_ca": ca_cert_path
        }
        print(f"✅ SSL certificate configured: {ca_cert_path}")
    except Exception as e:
        print(f"❌ SSL configuration failed: {e}")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
    echo=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Dependency to get database session in route handlers
def get_db():
    """
    Creates a new database session for each request
    Ensures proper cleanup after request is complete
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()