import os
import sys
from pathlib import Path

# Must be set before `src.auth` is imported (it refuses to start without a key).
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_studyroom.db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:1/0")  # unreachable: the service falls back to no-op

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
