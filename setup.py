"""
Setup script for initializing the voting system
Creates database tables and optionally creates a test admin account
"""
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from database import DATABASE_URL, Base
from models import User, UserRole
from utils.security import hash_password
from database import SessionLocal
import os
from dotenv import load_dotenv

load_dotenv()

def check_database_connection():
    """Check if database connection is working"""
    print("🔍 Checking database connection...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        return True
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease check:")
        print("1. MySQL server is running")
        print("2. Database credentials in .env file are correct")
        print("3. Database exists (run: CREATE DATABASE voting_system;)")
        return False

def create_tables():
    """Create all database tables"""
    print("\n📊 Creating database tables...")
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Print created tables
        inspector = engine.dialect.get_table_names(engine.connect())
        print(f"\n📋 Created tables: {', '.join(inspector)}")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def create_test_admin():
    """Create a test admin account"""
    print("\n👤 Creating test admin account...")
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(
            User.email == "admin@test.com"
        ).first()
        
        if existing_admin:
            print("⚠️  Test admin already exists (admin@test.com)")
            return True
        
        # Create test admin
        test_admin = User(
            name="Test Admin",
            email="admin@test.com",
            password=hash_password("admin123"),
            role=UserRole.ADMIN
        )
        
        db.add(test_admin)
        db.commit()
        
        print("✅ Test admin created successfully!")
        print("\n🔐 Test Admin Credentials:")
        print("   Email: admin@test.com")
        print("   Password: admin123")
        print("\n⚠️  IMPORTANT: Change these credentials in production!")
        return True
    except Exception as e:
        print(f"❌ Error creating test admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_environment():
    """Verify all required environment variables are set"""
    print("🔧 Verifying environment configuration...")
    
    required_vars = [
        "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME",
        "JWT_SECRET_KEY", "SMTP_USERNAME", "SMTP_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please update your .env file with these values")
        return False
    
    print("✅ All required environment variables are set!")
    return True

def main():
    """Main setup function"""
    print("=" * 60)
    print("🗳️  VOTING SYSTEM SETUP")
    print("=" * 60)
    
    # Step 1: Verify environment
    if not verify_environment():
        print("\n❌ Setup failed: Please configure environment variables")
        sys.exit(1)
    
    # Step 2: Check database connection
    if not check_database_connection():
        print("\n❌ Setup failed: Cannot connect to database")
        sys.exit(1)
    
    # Step 3: Create tables
    if not create_tables():
        print("\n❌ Setup failed: Could not create tables")
        sys.exit(1)
    
    # Step 4: Ask about test admin
    print("\n" + "=" * 60)
    create_admin = input("Do you want to create a test admin account? (y/n): ").lower()
    
    if create_admin == 'y':
        create_test_admin()
    
    # Step 5: Success message
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\n🚀 Next steps:")
    print("1. Run the server: python main.py")
    print("2. Visit API docs: http://localhost:8000/docs")
    print("3. Test the endpoints using Swagger UI")
    print("\n📚 For more information, check README.md")
    print("=" * 60)

if __name__ == "__main__":
    main()