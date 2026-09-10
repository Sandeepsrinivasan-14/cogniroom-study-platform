from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, Room, RoomMember
from src.auth import get_current_user
import base64
import io
from pydantic import BaseModel

router = APIRouter(prefix="/audio", tags=["audio"])

class SentimentResponse(BaseModel):
    sentiment_score: int  # -1 negative, 0 neutral, 1 positive
    confidence: float

@router.post("/sentiment", response_model=SentimentResponse)
async def audio_sentiment(
    room_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify membership
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    membership = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room_id, RoomMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    # Read audio bytes (placeholder implementation)
    contents = await file.read()
    # Mock sentiment analysis: simple length-based heuristic
    # In real implementation, integrate an ML model.
    length = len(contents)
    # For demo: short clips -> neutral, longer -> positive, very long -> negative
    if length < 20000:
        sentiment = 0
        confidence = 0.6
    elif length < 50000:
        sentiment = 1
        confidence = 0.8
    else:
        sentiment = -1
        confidence = 0.7

    # Store sentiment_score in WebcamLoad if needed (optional)
    # Return result
    return SentimentResponse(sentiment_score=sentiment, confidence=confidence)
