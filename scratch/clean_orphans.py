import sqlite3

conn = sqlite3.connect("d:\\placement portal\\backend\\placement_portal.db")
cursor = conn.cursor()

try:
    print("Deleting orphan notifications...")
    cursor.execute("""
        DELETE FROM notifications 
        WHERE user_id NOT IN (SELECT id FROM users);
    """)
    deleted = cursor.rowcount
    print(f"Deleted {deleted} orphan notification rows.")
    conn.commit()

    print("\nRunning foreign key check again...")
    cursor.execute("PRAGMA foreign_key_check;")
    fk_check = cursor.fetchall()
    print("Foreign Key Violations:", fk_check)

finally:
    conn.close()
