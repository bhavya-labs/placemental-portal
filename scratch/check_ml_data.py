import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.app.database import SessionLocal
from backend.app.models import Student
import pandas as pd
import numpy as np
from collections import Counter

db = SessionLocal()
try:
    students = db.query(Student).all()
    print(f"Total students: {len(students)}")
    statuses = [s.status for s in students]
    print("Student status counts:", Counter(statuses))
    batches = [s.batch for s in students]
    print("Student batch counts:", Counter(batches))
    
    # Check 2025 vs 2026 status breakdown
    status_by_batch = {}
    for s in students:
        status_by_batch.setdefault(s.batch, []).append(s.status)
    for b, st in status_by_batch.items():
        print(f"Batch {b}: {Counter(st)}")
finally:
    db.close()
