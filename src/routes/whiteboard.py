from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, Room, RoomMember
from src.auth import get_current_user
import base64
import io
from PIL import Image
import numpy as np

router = APIRouter(prefix="/whiteboard", tags=["whiteboard"])

@router.post("/clean", response_model=dict)
async def clean_whiteboard(
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

    # Read image bytes
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    # Placeholder: simple thresholding as dummy cleaning (replace with TF/MediaPipe model)
    arr = np.array(image)
    # Simple noise reduction: median filter (placeholder)
    cleaned_arr = arr  # No-op for now
    cleaned_image = Image.fromarray(cleaned_arr)
    buffered = io.BytesIO()
    cleaned_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return {"cleaned_image_base64": img_str}
