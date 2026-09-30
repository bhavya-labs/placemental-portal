import sqlite3
import os

db_path = 'backend/placement_portal.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('=== PRAGMA integrity_check ===')
cursor.execute('PRAGMA integrity_check;')
print(cursor.fetchall())

print('=== PRAGMA foreign_key_check ===')
cursor.execute('PRAGMA foreign_keys = ON;')
cursor.execute('PRAGMA foreign_key_check;')
fks = cursor.fetchall()
print(f'Foreign key violations count: {len(fks)}')
for fk in fks[:20]:
    print(fk)

print('\n=== TABLE ROW COUNTS ===')
tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()]
for t in tables:
    try:
        cnt = cursor.execute(f'SELECT COUNT(*) FROM "{t}";').fetchone()[0]
        print(f'{t:30s}: {cnt}')
    except Exception as e:
        print(f'{t:30s}: ERROR {e}')

conn.close()
