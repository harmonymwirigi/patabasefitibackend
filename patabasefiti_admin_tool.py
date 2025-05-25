#!/usr/bin/env python3
"""
Patabasefiti Admin Tool
A command-line tool to create and manage admin users for the Patabasefiti platform.

Usage:
    python patabasefiti_admin_tool.py create-admin
    python patabasefiti_admin_tool.py list-users
    python patabasefiti_admin_tool.py update-user-role
    python patabasefiti_admin_tool.py delete-user
"""

import os
import sys
import argparse
import getpass
from datetime import datetime
from pathlib import Path

# Add the app directory to the Python path
current_dir = Path(__file__).parent
app_dir = current_dir / "app"
sys.path.insert(0, str(current_dir))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import User
    from app.core.security import get_password_hash, verify_password
    from app.db.database import get_db, engine
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Make sure you're running this from the backend directory and all dependencies are installed.")
    sys.exit(1)

class PatabasefitiAdminTool:
    def __init__(self):
        """Initialize the admin tool with database connection."""
        try:
            # Use the existing engine from the app
            self.engine = engine
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            sys.exit(1)
    
    def create_admin(self):
        """Create a new admin user interactively."""
        print("\n🔧 Creating Admin User")
        print("=" * 50)
        
        # Get user input
        email = input("Enter admin email: ").strip()
        if not email:
            print("❌ Email is required")
            return
        
        # Check if user already exists
        existing_user = self.session.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email '{email}' already exists")
            print(f"Current role: {existing_user.role}")
            
            if existing_user.role != 'admin':
                update = input("Would you like to update this user to admin? (y/N): ").strip().lower()
                if update == 'y':
                    existing_user.role = 'admin'
                    existing_user.updated_at = datetime.utcnow()
                    self.session.commit()
                    print(f"✅ User '{email}' updated to admin role")
                else:
                    print("❌ Operation cancelled")
            else:
                print("ℹ️ User is already an admin")
            return
        
        full_name = input("Enter full name: ").strip()
        if not full_name:
            print("❌ Full name is required")
            return
        
        password = getpass.getpass("Enter password: ")
        if not password:
            print("❌ Password is required")
            return
        
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            return
        
        phone_number = input("Enter phone number (optional): ").strip() or None
        
        try:
            # Create admin user
            hashed_password = get_password_hash(password)
            
            admin_user = User(
                email=email,
                full_name=full_name,
                hashed_password=hashed_password,
                phone_number=phone_number,
                role='admin',
                auth_type='email',
                account_status='active',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                notification_preferences='{"email": true, "sms": true, "in_app": true}',
                token_history='[]',
                token_balance=1000  # Give admin some tokens
            )
            
            self.session.add(admin_user)
            self.session.commit()
            
            print(f"\n✅ Admin user created successfully!")
            print(f"📧 Email: {email}")
            print(f"👤 Name: {full_name}")
            print(f"🔑 Role: admin")
            print(f"💰 Token Balance: 1000")
            print(f"📱 Phone: {phone_number or 'Not provided'}")
            
        except Exception as e:
            self.session.rollback()
            print(f"❌ Error creating admin user: {e}")
    
    def list_users(self):
        """List all users in the system."""
        print("\n👥 User List")
        print("=" * 80)
        
        try:
            users = self.session.query(User).order_by(User.created_at.desc()).all()
            
            if not users:
                print("No users found in the database.")
                return
            
            print(f"{'ID':<5} {'Email':<30} {'Name':<25} {'Role':<10} {'Status':<10} {'Created':<12}")
            print("-" * 80)
            
            for user in users:
                created = user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'
                print(f"{user.id:<5} {user.email[:29]:<30} {user.full_name[:24]:<25} {user.role:<10} {user.account_status:<10} {created:<12}")
            
            print(f"\nTotal users: {len(users)}")
            
            # Count by role
            role_counts = {}
            for user in users:
                role_counts[user.role] = role_counts.get(user.role, 0) + 1
            
            print("\nUsers by role:")
            for role, count in role_counts.items():
                print(f"  {role}: {count}")
                
        except Exception as e:
            print(f"❌ Error listing users: {e}")
    
    def update_user_role(self):
        """Update a user's role."""
        print("\n🔄 Update User Role")
        print("=" * 50)
        
        email = input("Enter user email: ").strip()
        if not email:
            print("❌ Email is required")
            return
        
        user = self.session.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User with email '{email}' not found")
            return
        
        print(f"\nCurrent user details:")
        print(f"📧 Email: {user.email}")
        print(f"👤 Name: {user.full_name}")
        print(f"🔑 Current Role: {user.role}")
        print(f"📊 Status: {user.account_status}")
        
        print(f"\nAvailable roles:")
        roles = ['admin', 'owner', 'tenant']
        for i, role in enumerate(roles, 1):
            print(f"  {i}. {role}")
        
        try:
            choice = int(input(f"\nSelect new role (1-{len(roles)}): "))
            if 1 <= choice <= len(roles):
                new_role = roles[choice - 1]
                
                if new_role == user.role:
                    print(f"ℹ️ User already has role '{new_role}'")
                    return
                
                confirm = input(f"Confirm changing role from '{user.role}' to '{new_role}'? (y/N): ").strip().lower()
                if confirm == 'y':
                    user.role = new_role
                    user.updated_at = datetime.utcnow()
                    self.session.commit()
                    print(f"✅ User role updated to '{new_role}'")
                else:
                    print("❌ Operation cancelled")
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Please enter a valid number")
        except Exception as e:
            self.session.rollback()
            print(f"❌ Error updating user role: {e}")
    
    def delete_user(self):
        """Delete a user (with confirmation)."""
        print("\n🗑️ Delete User")
        print("=" * 50)
        print("⚠️ WARNING: This action cannot be undone!")
        
        email = input("Enter user email to delete: ").strip()
        if not email:
            print("❌ Email is required")
            return
        
        user = self.session.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User with email '{email}' not found")
            return
        
        print(f"\nUser to delete:")
        print(f"📧 Email: {user.email}")
        print(f"👤 Name: {user.full_name}")
        print(f"🔑 Role: {user.role}")
        print(f"📊 Status: {user.account_status}")
        
        # Double confirmation for safety
        confirm1 = input(f"\nType 'DELETE' to confirm deletion: ").strip()
        if confirm1 != 'DELETE':
            print("❌ Operation cancelled")
            return
        
        confirm2 = input(f"Are you absolutely sure? Type '{email}' to confirm: ").strip()
        if confirm2 != email:
            print("❌ Operation cancelled")
            return
        
        try:
            self.session.delete(user)
            self.session.commit()
            print(f"✅ User '{email}' deleted successfully")
        except Exception as e:
            self.session.rollback()
            print(f"❌ Error deleting user: {e}")
    
    def test_admin_login(self):
        """Test admin login credentials."""
        print("\n🔐 Test Admin Login")
        print("=" * 50)
        
        email = input("Enter admin email: ").strip()
        password = getpass.getpass("Enter password: ")
        
        user = self.session.query(User).filter(User.email == email).first()
        if not user:
            print("❌ User not found")
            return
        
        if user.role != 'admin':
            print(f"❌ User is not an admin (current role: {user.role})")
            return
        
        if verify_password(password, user.hashed_password):
            print("✅ Login successful!")
            print(f"Welcome, {user.full_name}")
        else:
            print("❌ Invalid password")
    
    def show_database_info(self):
        """Show database information."""
        print("\n📊 Database Information")
        print("=" * 50)
        
        try:
            # Count users by role
            total_users = self.session.query(User).count()
            admins = self.session.query(User).filter(User.role == 'admin').count()
            owners = self.session.query(User).filter(User.role == 'owner').count()
            tenants = self.session.query(User).filter(User.role == 'tenant').count()
            
            print(f"Total Users: {total_users}")
            print(f"  Admins: {admins}")
            print(f"  Owners: {owners}")
            print(f"  Tenants: {tenants}")
            
            # Show database file info
            db_path = "patabasefiti.db"
            if os.path.exists(db_path):
                stat = os.stat(db_path)
                size_mb = stat.st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(stat.st_mtime)
                print(f"\nDatabase File: {db_path}")
                print(f"Size: {size_mb:.2f} MB")
                print(f"Last Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"❌ Error getting database info: {e}")
    
    def close(self):
        """Close database connection."""
        self.session.close()

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Patabasefiti Admin Tool")
    parser.add_argument('command', nargs='?', default='menu', 
                       help='Command to execute (create-admin, list-users, update-user-role, delete-user, test-login, db-info)')
    
    args = parser.parse_args()
    
    # Initialize admin tool
    admin_tool = PatabasefitiAdminTool()
    
    try:
        if args.command == 'create-admin':
            admin_tool.create_admin()
        elif args.command == 'list-users':
            admin_tool.list_users()
        elif args.command == 'update-user-role':
            admin_tool.update_user_role()
        elif args.command == 'delete-user':
            admin_tool.delete_user()
        elif args.command == 'test-login':
            admin_tool.test_admin_login()
        elif args.command == 'db-info':
            admin_tool.show_database_info()
        else:
            # Interactive menu
            while True:
                print("\n🏠 Patabasefiti Admin Tool")
                print("=" * 50)
                print("1. Create Admin User")
                print("2. List All Users")
                print("3. Update User Role")
                print("4. Delete User")
                print("5. Test Admin Login")
                print("6. Database Info")
                print("7. Exit")
                
                try:
                    choice = input("\nSelect option (1-7): ").strip()
                    
                    if choice == '1':
                        admin_tool.create_admin()
                    elif choice == '2':
                        admin_tool.list_users()
                    elif choice == '3':
                        admin_tool.update_user_role()
                    elif choice == '4':
                        admin_tool.delete_user()
                    elif choice == '5':
                        admin_tool.test_admin_login()
                    elif choice == '6':
                        admin_tool.show_database_info()
                    elif choice == '7':
                        print("👋 Goodbye!")
                        break
                    else:
                        print("❌ Invalid choice. Please select 1-7.")
                        
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
    finally:
        admin_tool.close()

if __name__ == "__main__":
    main()