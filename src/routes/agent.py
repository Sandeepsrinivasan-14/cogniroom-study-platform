from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import Room, RoomMember
from src.auth import get_current_user
from src.schemas import AgentMemoryResponse, AgentMemoryUpdate

router = APIRouter(prefix="/agent", tags=["agent"])

@router.get("/memory/{room_id}", response_model=AgentMemoryResponse)
def get_agent_memory(room_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Verify room membership
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    membership = db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")
    return AgentMemoryResponse(room_id=room_id, memory=room.agent_memory or {})

@router.post("/memory/{room_id}", response_model=AgentMemoryResponse)
def update_agent_memory(room_id: int, payload: AgentMemoryUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    membership = db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")
    # Simple merge update
    existing = room.agent_memory or {}
    existing.update(payload.memory)
    room.agent_memory = existing
    db.add(room)
    db.commit()
    db.refresh(room)
    return AgentMemoryResponse(room_id=room_id, memory=room.agent_memory or {})
