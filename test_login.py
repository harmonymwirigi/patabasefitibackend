# File: backend/test_login.py
# A script to test the login function directly

import logging
import time
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_login")

# Database URL
DATABASE_URL = "sqlite:///./app.db"  # Adjust to your actual database path

# Test login credentials
TEST_LOGIN = {
    "email": "harmonymwithalii@gmail.com",
    "password": "special_probono_password"
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

def test_login_direct():
    """Test login directly using SQL"""
    logger.info(f"Testing login for email: {TEST_LOGIN['email']}")
    
    start_time = time.time()
    
    # Create engine and connection
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 5})
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get user by email
        logger.info("Getting user by email...")
        query = text("SELECT id, email, hashed_password, full_name, role, account_status FROM users WHERE email = :email")
        result = session.execute(query, {"email": TEST_LOGIN["email"]})
        user = result.fetchone()
        
        if not user:
            logger.error(f"User not found with email: {TEST_LOGIN['email']}")
            return False
        
        logger.info(f"Found user: ID={user[0]}, Email={user[1]}, Role={user[4]}")
        
        # Verify password
        logger.info("Verifying password...")
        is_valid = verify_password(TEST_LOGIN["password"], user[2])
        
        if not is_valid:
            logger.error("Password verification failed")
            return False
        
        logger.info("Password verification succeeded")
        
        # Check if user is active
        if user[5] != "active":
            logger.error(f"User account is not active: {user[5]}")
            return False
        
        logger.info("User account is active")
        
        # Update last login timestamp
        logger.info("Updating last login timestamp...")
        update_query = text("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :id")
        session.execute(update_query, {"id": user[0]})
        session.commit()
        
        duration = time.time() - start_time
        logger.info(f"Login successful in {duration:.3f}s")
        
        return {
            "id": user[0],
            "email": user[1],
            "full_name": user[3],
            "role": user[4]
        }
        
    except Exception as e:
        logger.error(f"Error during login test: {str(e)}")
        return False
    finally:
        session.close()

def check_user_existence():
    """Check if the test user exists in the database"""
    try:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check all users in the database
        logger.info("Checking all users in the database:")
        query = text("SELECT id, email, role, account_status FROM users")
        result = session.execute(query)
        users = result.fetchall()
        
        if not users:
            logger.warning("No users found in the database!")
            return False
        
        for user in users:
            logger.info(f"User: ID={user[0]}, Email={user[1]}, Role={user[2]}, Status={user[3]}")
        
        # Check specifically for the test user
        query = text("SELECT id, email, role, account_status FROM users WHERE email = :email")
        result = session.execute(query, {"email": TEST_LOGIN["email"]})
        user = result.fetchone()
        
        if not user:
            logger.warning(f"Test user with email {TEST_LOGIN['email']} not found!")
            return False
        
        logger.info(f"Test user found: ID={user[0]}, Email={user[1]}, Role={user[2]}, Status={user[3]}")
        return True
        
    except Exception as e:
        logger.error(f"Error checking user existence: {str(e)}")
        return False
    finally:
        session.close()

def create_test_user():
    """Create a test user if it doesn't exist"""
    try:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if user already exists
        query = text("SELECT id FROM users WHERE email = :email")
        result = session.execute(query, {"email": TEST_LOGIN["email"]})
        user = result.fetchone()
        
        if user:
            logger.info(f"Test user already exists with ID: {user[0]}")
            return True
        
        # Create the test user
        logger.info("Creating test user...")
        
        # Hash the password
        hashed_password = bcrypt.hashpw(TEST_LOGIN["password"].encode(), bcrypt.gensalt()).decode()
        
        # Insert the user
        insert_query = text("""
            INSERT INTO users (
                email, full_name, hashed_password, phone_number, role, 
                auth_type, token_balance, account_status, 
                notification_preferences, token_history, created_at, updated_at
            )
            VALUES (
                :email, :full_name, :hashed_password, :phone_number, :role,
                :auth_type, :token_balance, :account_status,
                :notification_preferences, :token_history, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """)
        
        session.execute(insert_query, {
            "email": TEST_LOGIN["email"],
            "full_name": "Test User",
            "hashed_password": hashed_password,
            "phone_number": "0712345678",
            "role": "tenant",
            "auth_type": "email",
            "token_balance": 0,
            "account_status": "active",
            "notification_preferences": '{"email": true, "sms": true, "in_app": true}',
            "token_history": '[]'
        })
        
        session.commit()
        
        logger.info("Test user created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating test user: {str(e)}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Starting login test...")
    
    # Check if bcrypt is installed
    try:
        import bcrypt
    except ImportError:
        logger.error("bcrypt module not found. Install it with: pip install bcrypt")
        sys.exit(1)
    
    # Check if the test user exists
    if not check_user_existence():
        logger.info("Creating a test user...")
        create_test_user()
    
    # Test login
    result = test_login_direct()
    
    if result:
        logger.info("✅ Login test passed!")
        logger.info(f"User: {result}")
    else:
        logger.error("❌ Login test failed!")