import sqlite3

conn = sqlite3.connect("d:\\placement portal\\backend\\placement_portal.db")
cursor = conn.cursor()

try:
    print("Running integrity check...")
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchall()
    print("Integrity Check Result:", integrity)

    print("\nRunning foreign key check...")
    cursor.execute("PRAGMA foreign_key_check;")
    fk_check = cursor.fetchall()
    print("Foreign Key Violations (empty list is good):", fk_check)

    # Let's count some key tables
    print("\nTable row counts:")
    for table in ["users", "students", "parents", "departments", "companies", "placement_drives", "applications", "interviews", "feedbacks"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f" - {table}: {count}")

finally:
    conn.close()
