import os
import sqlite3

def init_db():
    # Locate schema.sql inside resources
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, "resources", "schema.sql")

    # Connect to SQLite database (creates it if not exists)
    db_path = os.path.join(base_dir, "database.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Run schema.sql
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)

    conn.commit()
    conn.close()

    print("✅ Database initialized successfully at:", db_path)

if __name__ == "__main__":
    init_db()
