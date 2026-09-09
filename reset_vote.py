import sqlite3

conn = sqlite3.connect("voters.db")
cursor = conn.cursor()

# Reset all users
cursor.execute("UPDATE voters SET has_voted = 0")

conn.commit()
conn.close()

print("All users can vote again.")