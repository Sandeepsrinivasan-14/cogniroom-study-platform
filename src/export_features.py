import csv
from pathlib import Path

from .database import SessionLocal
from .models import Event

OUT_DIR = Path("ml")
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "user_features.csv"

db = SessionLocal()
try:
    rows = (
        db.query(Event.user_id, Event.type)
        .filter(Event.user_id.isnot(None))
        .all()
    )
finally:
    db.close()

features = {}
for user_id, ev_type in rows:
    if user_id is None or ev_type is None:
        continue
    feats = features.setdefault(int(user_id), {"user_id": int(user_id)})
    key = f"count_{ev_type}"
    feats[key] = feats.get(key, 0) + 1

fieldnames = ["user_id", "count_quiz_started", "count_question_answered", "count_webcam_load_update"]
with OUT_PATH.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for user_id, feat in features.items():
        row = {
            "user_id": user_id,
            "count_quiz_started": feat.get("count_quiz_started", 0),
            "count_question_answered": feat.get("count_question_answered", 0),
            "count_webcam_load_update": feat.get("count_webcam_load_update", 0),
        }
        writer.writerow(row)
print(f"Wrote features to {OUT_PATH}")
