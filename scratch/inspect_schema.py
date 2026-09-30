import sqlite3

def check_db():
    conn = sqlite3.connect("placement_portal.db")
    cur = conn.cursor()
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"Total tables: {len(tables)}")
    for name, sql in tables:
        if name in ['feedbacks', 'placement_drives', 'students', 'notifications', 'alembic_version']:
            print(f"--- Table: {name} ---")
            print(sql)
            print()

    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cur.fetchall()]
    print(f"Total indexes: {len(indexes)}")
    print("Existing custom indexes:")
    for idx in sorted(indexes):
        if not idx.startswith("sqlite_autoindex"):
            print("  ", idx)

if __name__ == "__main__":
    check_db()
