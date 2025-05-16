from app.db.database import engine, Base

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

if __name__ == "__main__":
    init_db()