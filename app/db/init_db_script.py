import os
import sys
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy import inspect

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

from app.db.database import engine, Base
from app import models  # Import all models

def init_db():
    """Initialize database tables"""
    
    # Enable foreign keys for SQLite
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        # If tables already exist, drop them first
        if table_names:
            print("Dropping existing tables...")
            Base.metadata.drop_all(bind=engine)
        
        # Create tables
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        print(f"Created {len(created_tables)} tables: {', '.join(created_tables)}")
        print("Database setup completed successfully!")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()