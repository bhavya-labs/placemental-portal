import sqlite3

conn = sqlite3.connect("placement_portal.db")
cur = conn.cursor()

# Query 1: Total index count in sqlite_master
cur.execute("SELECT count(*) FROM sqlite_master WHERE type='index'")
total_master = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%'")
total_named = cur.fetchone()[0]

cur.execute("SELECT count(*) FROM sqlite_master WHERE type='index' AND name LIKE 'sqlite_autoindex%'")
total_auto = cur.fetchone()[0]

print(f"Total indexes in sqlite_master: {total_master}")
print(f"  - User & Migration Named Indexes: {total_named}")
print(f"  - SQLite System Auto-Indexes: {total_auto}")
print("=" * 70)

# Query 2: PRAGMA index_list across all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]

pragma_index_count = 0
print(f"{'Table':<26} | {'Index Name':<42} | {'Unique':<6} | {'Origin'}")
print("-" * 85)

for table in tables:
    cur.execute(f"PRAGMA index_list('{table}')")
    rows = cur.fetchall()
    for row in rows:
        pragma_index_count += 1
        idx_seq, idx_name, idx_unique, idx_origin, idx_partial = row
        print(f"{table:<26} | {idx_name:<42} | {str(bool(idx_unique)):<6} | {idx_origin}")

print("=" * 85)
print(f"Total count from PRAGMA index_list across all tables: {pragma_index_count}")
conn.close()
