import sys, os
sys.path.insert(0, os.path.abspath('.'))
from datetime import datetime, timedelta
from backend.app.database import SessionLocal
from backend.app.models import Permission

db = SessionLocal()
perm = db.query(Permission).filter(Permission.id == 2).first()
print("Before:", perm.expiry_date)
perm.expiry_date = datetime.utcnow() + timedelta(days=30)
db.commit()
db.refresh(perm)
print("After:", perm.expiry_date)
