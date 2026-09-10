import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/studyroom')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Add sentiment_score to webcam_loads if not exists
    conn.execute(text('ALTER TABLE webcam_loads ADD COLUMN IF NOT EXISTS sentiment_score INTEGER;'))
    # Add agent_memory to rooms if not exists (JSONB for Postgres)
    conn.execute(text('ALTER TABLE rooms ADD COLUMN IF NOT EXISTS agent_memory JSONB;'))
    conn.commit()
print('Migration completed')
