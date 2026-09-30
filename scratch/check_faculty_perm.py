import sys, os
sys.path.insert(0, os.path.abspath('.'))
from backend.app.database import SessionLocal
from backend.app.models import User, Permission
from backend.app.auth import verify_permission

db = SessionLocal()
user = db.query(User).filter(User.email == "faculty.cse@platform.edu").first()
print(f"User: {user.id}, email={user.email}, role={user.role}")

perms = db.query(Permission).filter(Permission.user_id == user.id).all()
print("Permissions for faculty.cse:")
for p in perms:
    print(f"  Perm: module={p.module}, action={p.action}, scope={p.scope}, scope_value={p.scope_value}, status={p.status}")

scope_res = verify_permission(user, "Placement Drives", "EDIT", db)
print("verify_permission for 'Placement Drives' 'EDIT':", scope_res)
