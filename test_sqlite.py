# test_sqlite.py
import sqlite3
import os
import time

# Print SQLite version and check if driver is working
print(f"SQLite version: {sqlite3.sqlite_version}")

# Try to create and use a test database
db_path = "test_sqlite.db"
print(f"Creating test database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create a simple table
cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, value TEXT)")

# Insert a value
for i in range(5):
    print(f"Inserting value {i}")
    cursor.execute("INSERT INTO test (value) VALUES (?)", (f"test_{i}",))
    conn.commit()
    time.sleep(1)  # Sleep to show the database should be locked

# Query the table
print("Querying test table")
cursor.execute("SELECT * FROM test")
rows = cursor.fetchall()
print(f"Query result: {rows}")

# Keep connection open
print("Keeping connection open for 10 seconds")
time.sleep(10)

# Close connection
cursor.close()
conn.close()
print("Connection closed")

# Try to delete the file
try:
    os.remove(db_path)
    print(f"Successfully deleted {db_path}")
except Exception as e:
    print(f"Could not delete {db_path}: {e}")