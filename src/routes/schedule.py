from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.models import ScheduleItem, Room, RoomMember, User
from src.schemas import ScheduleItemCreate, ScheduleItemOut
from src.auth import get_current_user
from src.main import sio

router = APIRouter(prefix="/rooms/{room_id}/schedule", tags=["schedule"])

@router.post("/", response_model=ScheduleItemOut)
async def create_schedule_item(
    room_id: int,
    item_in: ScheduleItemCreate,
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
    schedule_item = ScheduleItem(
        room_id=room_id,
        title=item_in.title,
        start_time=item_in.start_time,
        duration_minutes=item_in.duration_minutes,
        created_by=current_user.id,
    )
    db.add(schedule_item)
    db.commit()
    db.refresh(schedule_item)
    # Emit timer update to participants via Socket.IO
    remaining = int(schedule_item.duration_minutes * 60)
    await sio.emit(
        "timer_update",
        {"room_id": str(room_id), "timers": [{"id": schedule_item.id, "remaining": remaining}]},
    )
    return ScheduleItemOut.from_orm(schedule_item)

@router.get("/", response_model=List[ScheduleItemOut])
def list_schedule_items(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify membership
    membership = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room_id, RoomMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")
    items = db.query(ScheduleItem).filter(ScheduleItem.room_id == room_id).all()
    return [ScheduleItemOut.from_orm(i) for i in items]

@router.delete("/{item_id}", response_model=dict)
def delete_schedule_item(
    room_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify membership and ownership
    membership = (
        db.query(RoomMember)
        .filter(RoomMember.room_id == room_id, RoomMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")
    item = (
        db.query(ScheduleItem)
        .filter(ScheduleItem.id == item_id, ScheduleItem.room_id == room_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    if item.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can delete")
    db.delete(item)
    db.commit()
    return {"detail": "Deleted"}
