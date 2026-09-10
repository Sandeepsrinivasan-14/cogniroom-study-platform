from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import WebcamLoad, Room, RoomMember, User
from src.schemas import WebcamLoadIn, WebcamLoadOut
from src.auth import get_current_user
from src.live_metrics import update_live_load

router = APIRouter(prefix="/rooms/{room_id}/load", tags=["load"])

@router.post("/", response_model=WebcamLoadOut)
def post_load(
    room_id: int,
    load_in: WebcamLoadIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify room exists and user is a member
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
    # Store load record
    load_record = WebcamLoad(
        room_id=room_id,
        user_id=current_user.id,
        load_score=int(load_in.load_score * 100),  # store as 0-100 integer
    )
    db.add(load_record)
    db.commit()
    db.refresh(load_record)
    # Update live metrics (Redis) for real‑time heatmap
    try:
        update_live_load(room_id, current_user.id, load_in.load_score)
    except Exception as e:
        # non‑critical, just log
        print(f"Failed to update live load: {e}")
    return WebcamLoadOut.from_orm(load_record)
