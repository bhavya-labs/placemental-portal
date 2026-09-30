import sqlite3

conn = sqlite3.connect('backend/placement_portal.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", [r[0] for r in cur.fetchall()])

cur.execute("PRAGMA table_info(system_logs);")
print("system_logs cols:", cur.fetchall())

cur.execute("SELECT * FROM system_logs ORDER BY id DESC LIMIT 20;")
for row in cur.fetchall():
    print(row)

cur.execute("""
    SELECT d.id, d.company_id, c.name, d.role, d.status, d.package_lpa, d.location
    FROM placement_drives d
    JOIN companies c ON d.company_id = c.id
    ORDER BY d.id
""")
print("\n--- ALL DRIVES CURRENT STATUS ---")
for row in cur.fetchall():
    print(f"Drive ID {row[0]}: Company {row[1]} ({row[2]}), Role: {row[3]}, Status: {row[4]}, LPA: {row[5]}, Loc: {row[6]}")
