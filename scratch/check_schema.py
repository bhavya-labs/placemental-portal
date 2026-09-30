import sqlite3

conn = sqlite3.connect('placement_portal.db')
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='feedbacks'")
row = cursor.fetchone()
print(row[0] if row else "Table not found")
