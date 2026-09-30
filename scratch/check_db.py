import sqlite3

def check_db():
    conn = sqlite3.connect('placement_portal.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print("Tables:", tables)
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [col[1] for col in cursor.fetchall()]
        print(f"Table {table} columns: {cols}")
    conn.close()

if __name__ == '__main__':
    check_db()
