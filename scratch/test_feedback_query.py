from backend.app.database import SessionLocal
from backend.app.models import Feedback, PlacementActivity
import traceback

db = SessionLocal()
try:
    activity_id = 1
    res = db.query(Feedback).filter(
        Feedback.activity_id == activity_id,
        Feedback.interview_id == None,
        Feedback.id.in_(
            db.query(Feedback.id).join(PlacementActivity).filter(Feedback.activity_id == activity_id).all()
        )
    ).first()
    print("Result:", res)
except Exception as e:
    traceback.print_exc()
finally:
    db.close()
