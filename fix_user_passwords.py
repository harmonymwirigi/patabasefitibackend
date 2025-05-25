# File: fix_user_passwords.py
# Script to fix user passwords and create a working admin user

import sqlite3
import os
import sys
import json
import datetime
import secrets
import hashlib
from passlib.context import CryptContext
from getpass import getpass

# Create password context matching your app's configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    Generate a bcrypt hash of the password - matches FastAPI app's hashing
    """
    return pwd_context.hash(password)

def main():
    # Path to the database file
    db_path = "patabasefiti.db"
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        sys.exit(1)
    
    print("=== Fix User Passwords & Create Admin User ===")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    c = conn.cursor()
    
    # Check if we have any users
    c.execute("SELECT COUNT(*) as count FROM users")
    user_count = c.fetchone()['count']
    
    print(f"Found {user_count} users in the database")
    
    # Options
    print("\nWhat would you like to do?")
    print("1. Create new admin user")
    print("2. Fix existing user passwords")
    print("3. Do both")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice in ['1', '3']:
        create_admin_user(conn)
        
    if choice in ['2', '3']:
        fix_existing_passwords(conn)
    
    conn.close()
    print("\nOperation completed successfully!")

def create_admin_user(conn):
    """Create a new admin user with proper password hashing"""
    print("\n--- Create Admin User ---")
    
    # Get admin user details
    email = input("Email: ")
    full_name = input("Full Name: ")
    
    # Check if the email already exists
    c = conn.cursor()
    c.execute("SELECT id, role FROM users WHERE email = ?", (email,))
    existing_user = c.fetchone()
    
    if existing_user:
        user_id = existing_user['id']
        current_role = existing_user['role']
        
        print(f"User with email {email} already exists (ID: {user_id}, Role: {current_role})")
        
        if current_role == 'admin':
            print("This user is already an admin.")
            reset_password = input("Do you want to reset their password? (y/n): ")
            
            if reset_password.lower() == 'y':
                password = getpass("New Password (min 8 chars): ")
                if len(password) < 8:
                    print("Password too short! Must be at least 8 characters.")
                    return
                
                # Generate bcrypt hash
                hashed_password = get_password_hash(password)
                
                # Update user password
                c.execute(
                    "UPDATE users SET hashed_password = ? WHERE id = ?",
                    (hashed_password, user_id)
                )
                conn.commit()
                print(f"Password updated successfully for user ID: {user_id}")
        else:
            update = input(f"Do you want to promote this user from '{current_role}' to 'admin' role? (y/n): ")
            
            if update.lower() == 'y':
                c.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))
                conn.commit()
                print(f"User updated to admin role successfully!")
                
                reset_password = input("Do you want to reset their password too? (y/n): ")
                
                if reset_password.lower() == 'y':
                    password = getpass("New Password (min 8 chars): ")
                    if len(password) < 8:
                        print("Password too short! Must be at least 8 characters.")
                        return
                    
                    # Generate bcrypt hash
                    hashed_password = get_password_hash(password)
                    
                    # Update user password
                    c.execute(
                        "UPDATE users SET hashed_password = ? WHERE id = ?",
                        (hashed_password, user_id)
                    )
                    conn.commit()
                    print(f"Password updated successfully for user ID: {user_id}")
    else:
        # Create a new admin user
        password = getpass("Password (min 8 chars): ")
        confirm_password = getpass("Confirm Password: ")
        
        if password != confirm_password:
            print("Passwords do not match!")
            return
        
        if len(password) < 8:
            print("Password too short! Must be at least 8 characters.")
            return
        
        # Generate bcrypt hash
        hashed_password = get_password_hash(password)
        
        now = datetime.datetime.utcnow().isoformat()
        notification_prefs = json.dumps({"email": True, "sms": True, "in_app": True})
        token_history = json.dumps([])
        
        c.execute("""
            INSERT INTO users (
                email, auth_type, full_name, hashed_password, 
                role, account_status, created_at, updated_at,
                notification_preferences, token_history, token_balance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            email, 'password', full_name, hashed_password,
            'admin', 'active', now, now,
            notification_prefs, token_history, 1000
        ))
        
        conn.commit()
        user_id = c.lastrowid
        print(f"Admin user created successfully with ID: {user_id}")
        print(f"Initial token balance: 1000")

def fix_existing_passwords(conn):
    """Fix existing user passwords that have incorrect format"""
    print("\n--- Fix Existing User Passwords ---")
    
    c = conn.cursor()
    c.execute("SELECT id, email, full_name, hashed_password, role FROM users")
    users = c.fetchall()
    
    if not users:
        print("No users found in the database.")
        return
    
    print(f"Found {len(users)} users. Checking for password issues...")
    
    fixed_count = 0
    for user in users:
        user_id = user['id']
        email = user['email']
        password_hash = user['hashed_password']
        
        # Check if the hash format is correct (starts with $2b$ for bcrypt)
        # or has incorrect format like "pbkdf2:sha256:salt:hash"
        if password_hash and not password_hash.startswith('$2b$'):
            print(f"\nUser {user_id} ({email}) has incorrect password hash format.")
            print(f"Current role: {user['role']}")
            print(f"Current hash: {password_hash[:15]}...")
            
            fix = input(f"Do you want to reset password for this user? (y/n): ")
            
            if fix.lower() == 'y':
                new_password = input(f"Enter new password for {email} (or press Enter to generate random password): ")
                
                if not new_password:
                    # Generate a random password
                    new_password = secrets.token_urlsafe(12)
                    print(f"Generated random password: {new_password}")
                    print("IMPORTANT: Save this password as it won't be shown again!")
                
                # Hash the new password correctly
                new_hash = get_password_hash(new_password)
                
                # Update the user's password
                c.execute(
                    "UPDATE users SET hashed_password = ? WHERE id = ?",
                    (new_hash, user_id)
                )
                conn.commit()
                fixed_count += 1
                print(f"Password updated successfully for {email}")
    
    if fixed_count == 0:
        print("No password issues found or fixed.")
    else:
        print(f"\nFixed passwords for {fixed_count} users.")

if __name__ == "__main__":
    try:
        # Try importing passlib - required for password hashing
        import passlib
    except ImportError:
        print("The 'passlib' package is required for correct password hashing.")
        print("Please install it with: pip install passlib[bcrypt]")
        sys.exit(1)
    
    main()