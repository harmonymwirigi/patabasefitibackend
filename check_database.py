# save as check_database.py
import sqlite3
import logging
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("db_check")

def check_db():
    start_time = time.time()
    logger.info("Testing database connection...")
    
    try:
        # Connect with a timeout
        conn = sqlite3.connect("app.db", timeout=5)
        cursor = conn.cursor()
        
        # Check if we can query the users table
        logger.info("Testing users table query...")
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        logger.info(f"User count: {count}")
        
        # Test a simple insert and delete
        logger.info("Testing write operations...")
        cursor.execute(
            "INSERT INTO users (email, full_name, hashed_password, role, auth_type, account_status) "
            "VALUES ('temp_test@example.com', 'Temp Test', 'not_a_real_hash', 'tenant', 'email', 'active')"
        )
        last_id = cursor.lastrowid
        logger.info(f"Inserted test user with ID: {last_id}")
        
        cursor.execute("DELETE FROM users WHERE id = ?", (last_id,))
        logger.info("Deleted test user")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database check completed successfully in {time.time() - start_time:.3f}s")
        return True
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
        return False

if __name__ == "__main__":
    check_db()