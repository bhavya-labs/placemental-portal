import sys, os
sys.path.insert(0, os.path.abspath('.'))
from datetime import datetime
from backend.app.database import SessionLocal
from backend.app.models import User, Permission

db = SessionLocal()
now = datetime.utcnow()
print("Current UTC now:", now)
perms = db.query(Permission).filter(Permission.user_id == 2).all()
for p in perms:
    print(f"ID: {p.id}, Module: '{p.module}', Action: '{p.action}', Scope: {p.scope}, ScopeVal: {p.scope_value}, Status: {p.status}")
    print(f"  start_date: {p.start_date}, expiry_date: {p.expiry_date}")
    print(f"  is_active: {p.status == 'Active'}, start_ok: {p.start_date <= now}, expiry_ok: {p.expiry_date >= now}")
