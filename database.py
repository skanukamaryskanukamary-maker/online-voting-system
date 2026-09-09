import sqlite3

# Connect to Database
connection = sqlite3.connect("voters.db")
cursor = connection.cursor()

# ---------------- Voters Table ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS voters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    has_voted INTEGER DEFAULT 0
)
""")

# ---------------- Candidates Table ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    party TEXT NOT NULL,
    symbol TEXT NOT NULL
)
""")

# ---------------- Votes Table ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_id INTEGER,
    candidate_id INTEGER,
    FOREIGN KEY (voter_id) REFERENCES voters(id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
)
""")

# Save Changes
connection.commit()

# Close Database
connection.close()

print("Database Created Successfully")