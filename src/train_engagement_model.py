from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression

DATA_PATH = Path("ml") / "user_features.csv"
OUT_PATH = Path("ml") / "engagement_model.pkl"

if not DATA_PATH.exists():
    raise SystemExit(f"Data file not found: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

if df.empty:
    raise SystemExit("No rows in user_features.csv")

# Simple target: high_engagement = 1 if total events >= 3 else 0
df["total"] = (
    df["count_quiz_started"] +
    df["count_question_answered"] +
    df["count_webcam_load_update"]
)
df["high_engagement"] = (df["total"] >= 3).astype(int)

X = df[["count_quiz_started", "count_question_answered", "count_webcam_load_update"]]
y = df["high_engagement"]

model = LogisticRegression()
model.fit(X, y)

OUT_PATH.parent.mkdir(exist_ok=True)
joblib.dump(model, OUT_PATH)
print(f"Saved model to {OUT_PATH}")
