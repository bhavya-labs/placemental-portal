import sqlite3
import os
import datetime

files = [
    'scratch/placement_portal.db.bak',
    'backend/placement_portal.db.backup',
    'placement_portal.db',
    'backups/placement_portal_pre_migration.db.bak',
    'backups/placement_portal_current.db.bak'
]

for f in files:
    if os.path.exists(f):
        stat = os.stat(f)
        mtime_str = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
        conn = sqlite3.connect(f)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        has_alembic = 'alembic_version' in tables
        alembic_ver = None
        if has_alembic:
            try:
                cur.execute('SELECT version_num FROM alembic_version')
                row = cur.fetchone()
                alembic_ver = row[0] if row else None
            except Exception as e:
                alembic_ver = str(e)
        cur.execute("SELECT count() FROM sqlite_master WHERE type='index'")
        idx_count = cur.fetchone()[0]
        cur.execute("SELECT count() FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%'")
        named_idx_count = cur.fetchone()[0]
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%'")
        named_indexes = [r[0] for r in cur.fetchall()]
        conn.close()
        print(f"File: {f}")
        print(f"  Size: {stat.st_size} bytes")
        print(f"  Modified Time: {mtime_str}")
        print(f"  Total Tables: {len(tables)}")
        print(f"  Has alembic_version: {has_alembic} (version: {alembic_ver})")
        print(f"  Total SQLite indexes: {idx_count}")
        print(f"  Non-autoindex (user/alembic created) indexes: {named_idx_count}")
        print(f"  Sample non-auto indexes: {named_indexes[:5]}")
        print("-" * 60)
