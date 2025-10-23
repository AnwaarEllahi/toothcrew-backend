import sqlite3

# Connect to your database file
conn = sqlite3.connect("test.db")
cursor = conn.cursor()
# 1. Rename the old table
cursor.execute("ALTER TABLE services RENAME TO services_old;")

# 2. Create the new 'services' table matching your SQLAlchemy model
cursor.execute("""
CREATE TABLE services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price_amount INTEGER,
    price_text TEXT,
    currency TEXT DEFAULT 'PKR',
    category_id INTEGER NOT NULL REFERENCES categories(id),
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
""")

# 3. Copy over compatible data from the old table (if needed)
cursor.execute("""
INSERT INTO services (id, name, is_active, created_at)
SELECT id, name, 1, CURRENT_TIMESTAMP FROM services_old;
""")

# 4. Drop the old table
cursor.execute("DROP TABLE services_old;")

conn.commit()
conn.close()

print("✅ Table 'services' rebuilt successfully without the old 'price' column.")