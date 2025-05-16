# save as test_registration_minimal.py
import time
import logging
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_minimal")

# Database URL
DATABASE_URL = "sqlite:///./app.db"

# Test user data
TEST_USER = {
    "email": "test_minimal@example.com",
    "full_name": "Test Minimal",
    "password": "test_password",
    "phone_number": "0712345678",
    "role": "tenant"
}

def test_user_creation():
    start_time = time.time()
    logger.info(f"Starting minimal user creation test for {TEST_USER['email']}")
    
    # Create DB connection with explicit timeout
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 5})
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if user exists
        logger.info("Checking if user exists...")
        check_start = time.time()
        query = text("SELECT id FROM users WHERE email = :email")
        result = session.execute(query, {"email": TEST_USER['email']})
        user_exists = result.fetchone() is not None
        logger.info(f"User exists check completed in {time.time() - check_start:.3f}s: {user_exists}")
        
        if user_exists:
            logger.info("User already exists, skipping creation")
            return False
        
        # Hash password
        logger.info("Hashing password...")
        hash_start = time.time()
        hashed_password = bcrypt.hashpw(TEST_USER["password"].encode(), bcrypt.gensalt(rounds=10)).decode()
        logger.info(f"Password hashing completed in {time.time() - hash_start:.3f}s")
        
        # Insert user
        logger.info("Inserting user...")
        insert_start = time.time()
        insert_query = text("""
            INSERT INTO users (
                email, full_name, hashed_password, phone_number, role, 
                auth_type, token_balance, account_status, created_at, updated_at
            )
            VALUES (
                :email, :full_name, :hashed_password, :phone_number, :role,
                'email', 0, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """)
        
        session.execute(insert_query, {
            "email": TEST_USER["email"],
            "full_name": TEST_USER["full_name"],
            "hashed_password": hashed_password,
            "phone_number": TEST_USER["phone_number"],
            "role": TEST_USER["role"]
        })
        
        # Commit transaction
        logger.info("Committing transaction...")
        commit_start = time.time()
        session.commit()
        logger.info(f"Transaction committed in {time.time() - commit_start:.3f}s")
        
        logger.info(f"Total user creation time: {time.time() - start_time:.3f}s")
        return True
        
    except Exception as e:
        logger.error(f"Error in test_user_creation: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    test_user_creation()