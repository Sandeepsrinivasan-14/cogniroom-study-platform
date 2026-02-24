import os
import random
import string
from collections import defaultdict
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from time import time
import time as time_module
import requests
import socketio
import sqlalchemy
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from src.database import SessionLocal, engine, get_db, Base
from src.models import (
    User,
    Room,
    RoomMember,
    Event,
    Quiz,
    Question,
    QuizAttempt,
    QuestionAnswer,
)
from src.schemas import (
    UserCreate,
    UserOut,
    Token,
    RoomCreate,
    RoomOut,
    RoomListOut,
    QuizCreate,
    QuizOut,
    QuestionOut,
    QuizAttemptCreate,
    QuizAttemptOut,
    AnswerIn,
    QuestionAnswerOut,
    UserLogin,
)

from src.analytics_service import get_user_analytics, get_room_analytics
from src.live_metrics import get_room_live_metrics, update_live_load, cleanup_old_metrics

# ========== SOCKET.IO SETUP - CRITICAL FIX ==========
# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    max_http_buffer_size=10**7,
    ping_timeout=60,
    ping_interval=25
)

# Create FastAPI app
app = FastAPI(title="StudyRoom Backend")

# Add CORS middleware to FastAPI (ONCE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== MOUNT SOCKET.IO CORRECTLY - NO RECURSION ==========
# This is the key fix - mount Socket.IO as a separate ASGI app
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

# Create Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio)

# Mount it at a subpath to avoid recursion
app.mount("/socket.io", socket_app)

# Add a route to redirect root to Socket.IO info
@app.get("/socket.io/")
async def socket_io_info():
    return {"status": "Socket.IO server running", "path": "/socket.io"}

# ========== HELPER FUNCTIONS ==========
def generate_room_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

async def async_log_event(room_id: int | str, event_type: str, payload: dict | str | None = None):
    """Log an event asynchronously with JSON payload support"""
    from src.database import SessionLocal
    from src.models import Event
    import json
    
    db = SessionLocal()
    try:
        if isinstance(payload, dict):
            payload_str = json.dumps(payload)
        else:
            payload_str = payload
        
        evt = Event(
            room_id=int(room_id) if room_id else None,
            type=event_type,
            payload=payload_str,
            created_at=datetime.utcnow()
        )
        db.add(evt)
        db.commit()
    except Exception as e:
        print(f"Error logging event: {e}")
    finally:
        db.close()

def log_event(
    db: Session,
    *,
    user_id: int | None,
    room_id: int | None,
    type: str,
    payload: str | None = None,
) -> None:
    ev = Event(
        user_id=user_id,
        room_id=room_id,
        type=type,
        payload=payload,
    )
    db.add(ev)
    db.commit()

# ========== PERIODIC CLEANUP TASK ==========
import asyncio

async def periodic_cleanup():
    """Clean up old metrics every 5 minutes"""
    while True:
        await asyncio.sleep(300)
        cleanup_old_metrics()
        print("Cleaned up old live metrics")

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    from time import sleep
    from sqlalchemy import text
    
    # Test database connection
    max_retries = 30
    for i in range(max_retries):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            print("? Database connection successful!")
            
            # Create tables if they don't exist
            Base.metadata.create_all(bind=engine)
            print("? Tables created successfully!")
            break
        except Exception as e:
            print(f"DB retry {i+1}/{max_retries}...")
            if i == max_retries - 1:
                print(f"? DB failed after retries: {e}")
            sleep(1)
    
    # Start background tasks
    asyncio.create_task(periodic_cleanup())
    print("Started periodic cleanup task")

# ========== HEALTH ENDPOINTS ==========
@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/socket-health")
def socket_health():
    return {"status": "socket-ok", "path": "/socket.io"}

# ========== AUTHENTICATION ENDPOINTS ==========
@app.post("/auth/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == user_in.email).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Create access token
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

# ========== ROOM ENDPOINTS ==========
@app.post("/rooms", response_model=RoomOut)
def create_room(
    room_in: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    code = generate_room_code()
    existing = db.query(Room).filter(Room.code == code).first()
    while existing:
        code = generate_room_code()
        existing = db.query(Room).filter(Room.code == code).first()

    room = Room(name=room_in.name, code=code, created_by=current_user.id)
    db.add(room)
    db.commit()
    db.refresh(room)

    membership = RoomMember(
        room_id=room.id,
        user_id=current_user.id,
        role=current_user.role if isinstance(current_user.role, str) else str(current_user.role),
    )
    db.add(membership)
    db.commit()

    try:
        log_event(
            db=db,
            user_id=current_user.id,
            room_id=room.id,
            type="room_created",
            payload=None,
        )
    except Exception:
        pass

    return room

@app.post("/rooms/join/{code}", response_model=RoomOut)
def join_room(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.code == code).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    existing = db.query(RoomMember).filter(
        RoomMember.room_id == room.id,
        RoomMember.user_id == current_user.id,
    ).first()
    
    if not existing:
        membership = RoomMember(
            room_id=room.id,
            user_id=current_user.id,
            role=current_user.role if isinstance(current_user.role, str) else str(current_user.role),
        )
        db.add(membership)
        db.commit()

    try:
        log_event(
            db=db,
            user_id=current_user.id,
            room_id=room.id,
            type="room_joined",
            payload=None,
        )
    except Exception:
        pass

    return room

@app.get("/rooms/my", response_model=RoomListOut)
def list_my_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memberships = db.query(RoomMember).filter(RoomMember.user_id == current_user.id).all()
    room_ids = [m.room_id for m in memberships]
    if not room_ids:
        return {"rooms": []}
    rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
    return {"rooms": rooms}

# ========== EVENT ENDPOINTS ==========
@app.get("/rooms/{room_id}/events")
def get_room_events(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
):
    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    events = db.query(Event).filter(Event.room_id == room_id).order_by(Event.created_at.desc()).limit(limit).all()
    return {
        "room_id": room_id,
        "events": [
            {
                "id": e.id,
                "user_id": e.user_id,
                "room_id": e.room_id,
                "type": e.type,
                "payload": e.payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }

@app.get("/users/me/events")
def get_my_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    type: str | None = Query(default=None),
    room_id: int | None = Query(default=None),
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    limit: int = Query(100, ge=1, le=1000),
):
    q = db.query(Event).filter(Event.user_id == current_user.id)

    if type is not None:
        q = q.filter(Event.type == type)
    if room_id is not None:
        q = q.filter(Event.room_id == room_id)
    if start:
        try:
            start_dt = datetime.fromisoformat(start)
            q = q.filter(Event.created_at >= start_dt)
        except Exception:
            pass
    if end:
        try:
            end_dt = datetime.fromisoformat(end)
            q = q.filter(Event.created_at <= end_dt)
        except Exception:
            pass

    events = q.order_by(Event.created_at.desc()).limit(limit).all()
    return {
        "user_id": current_user.id,
        "events": [
            {
                "id": e.id,
                "user_id": e.user_id,
                "room_id": e.room_id,
                "type": e.type,
                "payload": e.payload,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }

# ========== SOCKET.IO EVENTS ==========
# These will be accessible at ws://localhost:8000/socket.io
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def joinroom(sid, data):
    room_id = str(data.get("roomid"))
    print(f"joinroom called for sid={sid}, room_id={room_id}")
    await sio.save_session(sid, {"room_id": room_id})
    await sio.enter_room(sid, room=room_id)
    await sio.emit("system_message", {"msg": f"User joined room {room_id}"}, room=room_id)

@sio.event
async def chatmessage(sid, data):
    session = await sio.get_session(sid)
    room_id = session.get("room_id")
    message = data.get("message")
    print(f"chatmessage from sid={sid} in room={room_id}: {message}")
    await sio.emit("chatmessage", {"message": message}, room=room_id)

@sio.event
async def whiteboard_update(sid, data):
    session = await sio.get_session(sid)
    room_id = str(data.get("room_id") or session.get("room_id"))
    user_id = data.get("user_id")

    if not room_id or user_id is None:
        return

    await sio.emit("whiteboard_update", data, room=room_id)
    await async_log_event(
        room_id=room_id,
        event_type="whiteboard_update",
        payload=f"user_id={user_id}",
    )

@sio.event
async def quiz_start(sid, data):
    session = await sio.get_session(sid)
    room_id = str(data.get("room_id") or session.get("room_id"))
    quiz_id = data.get("quiz_id")
    started_by = data.get("started_by")

    if not room_id or quiz_id is None:
        return

    await sio.emit("quiz_start", data, room=room_id)
    await async_log_event(
        room_id=room_id,
        event_type="quiz_started",
        payload=f"quiz_id={quiz_id},started_by={started_by}",
    )

@sio.event
async def quiz_answer(sid, data):
    session = await sio.get_session(sid)
    room_id = str(data.get("room_id") or session.get("room_id"))
    quiz_id = data.get("quiz_id")
    question_id = data.get("question_id")
    user_id = data.get("user_id")
    selected_index = data.get("selected_index")
    response_time_ms = data.get("response_time_ms")

    if not room_id or quiz_id is None or question_id is None or user_id is None:
        return

    await sio.emit("quiz_answer", data, room=room_id)
    await async_log_event(
        room_id=room_id,
        event_type="quiz_answered",
        payload=f"quiz_id={quiz_id},question_id={question_id},user_id={user_id},selected_index={selected_index},response_time_ms={response_time_ms}",
    )

@sio.event
async def presence_update(sid, data):
    session = await sio.get_session(sid)
    room_id = str(data.get("room_id") or session.get("room_id"))
    user_id = data.get("user_id")
    status = data.get("status")
    tab_visible = data.get("tab_visible")

    if room_id is None or user_id is None or status is None:
        return

    await sio.emit("presence_update", data, room=room_id)
    await async_log_event(
        room_id=room_id,
        event_type="presence_update",
        payload=f"user_id={user_id},status={status},tab_visible={tab_visible}",
    )

# ========== LIVE METRICS ==========
live_metrics: Dict[int, Dict[int, Dict[str, float]]] = defaultdict(dict)

def update_live_load(room_id: int, user_id: int, load_score: float) -> None:
    live_metrics[room_id][user_id] = {
        "load_score": load_score,
        "ts": time(),
    }

def cleanup_old_metrics(max_age_seconds: int = 300):
    """Remove metrics older than max_age_seconds"""
    current_time = time()
    for room_id in list(live_metrics.keys()):
        for user_id in list(live_metrics[room_id].keys()):
            if current_time - live_metrics[room_id][user_id]["ts"] > max_age_seconds:
                del live_metrics[room_id][user_id]
        if not live_metrics[room_id]:
            del live_metrics[room_id]

@sio.event
async def webcam_load_update(sid, data):
    session = await sio.get_session(sid)
    room_id_raw = data.get("room_id") or session.get("room_id")
    user_id = data.get("user_id")
    load_score = data.get("load_score")

    if room_id_raw is None or user_id is None or load_score is None:
        return

    try:
        room_id_int = int(room_id_raw)
        load_val = float(load_score)
    except (ValueError, TypeError):
        return

    if not (0.0 <= load_val <= 1.0):
        return

    update_live_load(room_id_int, int(user_id), load_val)
    await sio.emit(
        "webcam_load_update",
        {
            "room_id": str(room_id_int),
            "user_id": int(user_id),
            "load_score": load_val,
        },
        room=str(room_id_int),
    )
    await async_log_event(
        room_id=room_id_int,
        event_type="webcam_load_update",
        payload=f"user_id={user_id},load_score={load_val}",
    )

@app.get("/rooms/{room_id}/metrics/live")
def get_room_live_metrics_endpoint(
    room_id: int,
    current_user: User = Depends(get_current_user),
):
    room_data = live_metrics.get(room_id, {})
    if not room_data:
        return {
            "room_id": room_id,
            "users": [],
            "group_avg_load": None,
            "total_users": 0,
            "last_updated": None
        }

    users = []
    total_load = 0
    for uid, data in room_data.items():
        users.append({
            "user_id": uid,
            "load_score": data["load_score"],
            "last_active": datetime.fromtimestamp(data["ts"]).isoformat()
        })
        total_load += data["load_score"]
    
    group_avg = total_load / len(room_data) if room_data else None

    return {
        "room_id": room_id,
        "users": users,
        "group_avg_load": round(group_avg, 2) if group_avg else None,
        "total_users": len(users),
        "last_updated": datetime.now().isoformat()
    }

# ========== QUIZ ENDPOINTS ==========
@app.post("/rooms/{room_id}/quizzes", response_model=QuizOut)
def create_quiz_for_room(
    room_id: int,
    quiz_in: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    quiz = Quiz(room_id=room_id, title=quiz_in.title)
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    questions = []
    for q in quiz_in.questions:
        question = Question(quiz_id=quiz.id, text=q.text)
        db.add(question)
        questions.append(question)
    db.commit()

    return QuizOut(
        id=quiz.id,
        room_id=quiz.room_id,
        title=quiz.title,
        questions=[QuestionOut(id=q.id, text=q.text) for q in questions],
    )

@app.get("/rooms/{room_id}/quizzes", response_model=list[QuizOut])
def list_quizzes_for_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    quizzes = db.query(Quiz).filter(Quiz.room_id == room_id).all()
    quiz_ids = [q.id for q in quizzes]
    if not quiz_ids:
        return []

    questions = db.query(Question).filter(Question.quiz_id.in_(quiz_ids)).all()
    questions_by_quiz: dict[int, list[Question]] = {}
    for q in questions:
        questions_by_quiz.setdefault(q.quiz_id, []).append(q)

    result = []
    for quiz in quizzes:
        qs = questions_by_quiz.get(quiz.id, [])
        result.append(
            QuizOut(
                id=quiz.id,
                room_id=quiz.room_id,
                title=quiz.title,
                questions=[QuestionOut(id=qq.id, text=qq.text) for qq in qs],
            )
        )
    return result

@app.post("/quizzes/{quiz_id}/attempts", response_model=QuizAttemptOut)
def create_quiz_attempt(
    quiz_id: int,
    attempt_in: QuizAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    membership = db.query(RoomMember).filter(
        RoomMember.room_id == quiz.room_id,
        RoomMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    questions_by_id = {q.id: q for q in questions}
    total = len(questions)
    if total == 0:
        raise HTTPException(status_code=400, detail="Quiz has no questions")

    answer_rows = []
    correct = 0
    for ans in attempt_in.answers:
        question = questions_by_id.get(ans.question_id)
        if not question:
            continue
        # Simple correct answer check (in production, use actual correct_answer field)
        is_correct = True if ans.answer else False
        qa = QuestionAnswer(
            question_id=question.id,
            user_id=current_user.id,
            given_answer=ans.answer,
            is_correct=is_correct,
        )
        answer_rows.append(qa)
        if is_correct:
            correct += 1
        db.add(qa)

        try:
            log_event(
                db=db,
                user_id=current_user.id,
                room_id=quiz.room_id,
                type="question_answered",
                payload=f"quiz_id={quiz.id};question_id={question.id};is_correct={bool(is_correct)}",
            )
        except Exception:
            pass

    db.commit()

    try:
        log_event(
            db=db,
            user_id=current_user.id,
            room_id=quiz.room_id,
            type="quiz_started",
            payload=f"quiz_id={quiz.id}",
        )
    except Exception:
        pass

    attempt = QuizAttempt(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=correct,
        total_questions=total,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    for qa in answer_rows:
        qa.attempt_id = attempt.id
        db.add(qa)
    db.commit()

    try:
        log_event(
            db=db,
            user_id=current_user.id,
            room_id=quiz.room_id,
            type="quiz_finished",
            payload=f"quiz_id={quiz.id};score={correct}/{total}",
        )
    except Exception:
        pass

    answers_out = [
        QuestionAnswerOut(
            question_id=qa.question_id,
            given_answer=qa.given_answer,
            is_correct=bool(qa.is_correct),
        )
        for qa in answer_rows
    ]

    return QuizAttemptOut(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        user_id=attempt.user_id,
        score=attempt.score,
        total_questions=attempt.total_questions,
        answers=answers_out,
    )

@app.get("/rooms/{room_id}/stats/quiz")
def get_room_quiz_stats(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    total_quizzes = db.query(func.count(Quiz.id)).filter(Quiz.room_id == room_id).scalar() or 0

    attempts_q = db.query(
        func.count(QuizAttempt.id).label("attempts"),
        func.avg(QuizAttempt.score * 1.0 / QuizAttempt.total_questions).label("avg_ratio"),
    ).join(Quiz, Quiz.id == QuizAttempt.quiz_id).filter(Quiz.room_id == room_id).one()

    total_attempts = attempts_q.attempts or 0
    avg_score_percent = None
    if attempts_q.avg_ratio is not None:
        avg_score_percent = float(attempts_q.avg_ratio) * 100.0

    return {
        "room_id": room_id,
        "total_quizzes": int(total_quizzes),
        "total_attempts": int(total_attempts),
        "average_score_percent": avg_score_percent,
    }

# ========== ANALYTICS ENDPOINTS ==========
@app.get("/analytics/room/{room_id}/activity")
def get_room_activity_analytics(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    type_rows = db.query(Event.type, func.count(Event.id)).filter(Event.room_id == room_id).group_by(Event.type).all()
    by_type = {t: int(c) for (t, c) in type_rows}

    date_rows = db.query(func.date(Event.created_at), func.count(Event.id)).filter(Event.room_id == room_id).group_by(func.date(Event.created_at)).order_by(func.date(Event.created_at)).all()
    by_day = [{"date": str(d), "count": int(c)} for (d, c) in date_rows]

    user_rows = db.query(Event.user_id, func.count(Event.id)).filter(Event.room_id == room_id).group_by(Event.user_id).all()
    by_user = [{"user_id": uid, "event_count": int(c)} for (uid, c) in user_rows if uid is not None]

    return {
        "room_id": room_id,
        "by_type": by_type,
        "by_day": by_day,
        "by_user": by_user,
    }

@app.get("/analytics/user/{user_id}/activity")
def get_user_activity(user_id: int):
    db = SessionLocal()
    try:
        rows = db.query(Event.type, func.count(Event.id).label("count")).filter(Event.payload.like(f"%user_id={user_id}%")).group_by(Event.type).all()
        by_type = {row.type: row.count for row in rows}
        return {"user_id": user_id, "by_type": by_type}
    finally:
        db.close()

# ========== USER ANALYTICS ENDPOINTS ==========
@app.get("/users/me/analytics", response_model=Dict)
def get_my_analytics_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for the current user"""
    return get_user_analytics(db, current_user.id)

@app.get("/users/{user_id}/analytics", response_model=Dict)
def get_user_analytics_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific user"""
    if current_user.id != user_id and current_user.role not in ["mentor", "admin"]:
        raise HTTPException(status_code=403, detail="Cannot view other users' analytics")
    
    return get_user_analytics(db, user_id)

# ========== ROOM ANALYTICS ENDPOINTS ==========
@app.get("/rooms/{room_id}/analytics", response_model=Dict)
def get_room_analytics_endpoint(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a room"""
    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id
    ).first()
    
    if not membership and current_user.role not in ["mentor", "admin"]:
        raise HTTPException(status_code=403, detail="Not a member of this room")
    
    return get_room_analytics(db, room_id)

# ========== DEBUG ENDPOINT ==========
@app.post("/debug/send-load")
def debug_send_load(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to simulate webcam load updates"""
    room_id = data.get("room_id")
    user_id = data.get("user_id", current_user.id)
    load_score = data.get("load_score", 0.5)
    
    if not room_id:
        raise HTTPException(status_code=400, detail="room_id required")
    
    update_live_load(int(room_id), int(user_id), float(load_score))
    
    import json
    db_debug = SessionLocal()
    try:
        evt = Event(
            user_id=user_id,
            room_id=room_id,
            type="webcam_load_update",
            payload=json.dumps({"load_score": load_score}),
            created_at=datetime.utcnow()
        )
        db_debug.add(evt)
        db_debug.commit()
    finally:
        db_debug.close()
    
    return {"status": "ok", "message": f"Load score {load_score} recorded for user {user_id} in room {room_id}"}

@app.get("/debug/room/{room_id}/events/raw")
def debug_room_events_raw(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.query(Event).filter(Event.room_id == room_id).order_by(Event.created_at.desc()).limit(20).all()
    return [
        {
            "id": e.id,
            "room_id": e.room_id,
            "type": e.type,
            "payload": e.payload,
        }
        for e in rows
    ]

# ========== AI AGENT ENDPOINTS ==========
@app.get("/users/me/agent/suggestions", response_model=Dict)
def get_my_agent_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI suggestions for current user"""
    try:
        from src.agents_service import AgentService
        agent = AgentService(db)
        
        burnout_advice = agent.generate_burnout_advice(current_user.id)
        learning_plan = agent.generate_learning_plan("user", current_user.id)
        
        return {
            "burnout_advice": burnout_advice,
            "learning_plan": learning_plan,
            "combined": burnout_advice + learning_plan
        }
    except Exception as e:
        print(f"AI suggestions error: {e}")
        return {
            "burnout_advice": [{
                "type": "advice",
                "target": "user",
                "label": "Take a Break",
                "message": "Consider taking a short break to recharge.",
                "severity": "info"
            }],
            "learning_plan": [{
                "type": "plan",
                "target": "user",
                "label": "Keep Learning",
                "message": "Stay consistent with your study schedule.",
                "severity": "info"
            }],
            "combined": []
        }

@app.get("/users/{user_id}/agent/suggestions", response_model=Dict)
def get_user_agent_suggestions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI suggestions for a specific user"""
    if current_user.id != user_id and current_user.role not in ["mentor", "admin"]:
        raise HTTPException(status_code=403, detail="Cannot view other users' suggestions")
    
    try:
        from src.agents_service import AgentService
        agent = AgentService(db)
        
        burnout_advice = agent.generate_burnout_advice(user_id)
        learning_plan = agent.generate_learning_plan("user", user_id)
        
        return {
            "burnout_advice": burnout_advice,
            "learning_plan": learning_plan,
            "combined": burnout_advice + learning_plan
        }
    except Exception as e:
        print(f"AI suggestions error: {e}")
        return {"burnout_advice": [], "learning_plan": [], "combined": []}

@app.get("/rooms/{room_id}/agent/suggestions")
def get_room_agent_suggestions(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI suggestions for a room (Load Balancer Agent)"""
    membership = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == current_user.id
    ).first()
    
    if not membership and current_user.role not in ["mentor", "admin"]:
        raise HTTPException(status_code=403, detail="Not a member of this room")
    
    from src.agents_service import AgentService
    agent = AgentService(db)
    return agent.generate_load_actions(room_id)

# ========== ML ENDPOINTS ==========
class EngagementScoreRequest(BaseModel):
    user_id: int

class EngagementScoreResponse(BaseModel):
    user_id: int
    score: float
    details: dict

@app.post("/ml/engagement/score", response_model=EngagementScoreResponse)
def ml_engagement_score(body: EngagementScoreRequest):
    db = SessionLocal()
    try:
        rows = db.query(Event.type, func.count(Event.id).label("count")).filter(Event.payload.like(f"%user_id={body.user_id}%")).group_by(Event.type).all()
        counts = {row.type: row.count for row in rows}
        base = counts.get("quiz_started", 0) + counts.get("question_answered", 0) + counts.get("webcam_load_update", 0)
        score = min(1.0, base / 10.0)
        return EngagementScoreResponse(
            user_id=body.user_id,
            score=score,
            details=counts,
        )
    finally:
        db.close()

# ========== LLM QUIZ GENERATION ==========
class QuizGenRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    count: int = 5

class QuizGenQuestion(BaseModel):
    question: str
    answer: str

class QuizGenResponse(BaseModel):
    questions: list[QuizGenQuestion]

def call_llm_quiz(prompt: str) -> str:
    base_url = os.getenv("LLM_BASE_URL")
    api_key = os.getenv("LLM_API_KEY")
    if not base_url or not api_key:
        raise RuntimeError("LLM_BASE_URL or LLM_API_KEY not set")

    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {
                "role": "system",
                "content": "You generate short quiz questions with answers. Output plain text lines in the format: question || answer.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 512,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(base_url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    choices = data.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message", {})
    return msg.get("content", "")

@app.post("/llm/quiz/generate", response_model=QuizGenResponse)
def llm_quiz_generate(
    body: QuizGenRequest,
    current_user: User = Depends(get_current_user),
):
    prompt = (
        f"Generate {body.count} short Q&A pairs on the topic '{body.topic}' "
        f"with difficulty {body.difficulty}. "
        f"Each line must be: question || answer."
    )
    text = call_llm_quiz(prompt)
    questions = []
    for line in text.splitlines():
        if "||" not in line:
            continue
        q, a = line.split("||", 1)
        q = q.strip("- ").strip()
        a = a.strip()
        if q and a:
            questions.append(QuizGenQuestion(question=q, answer=a))
    return QuizGenResponse(questions=questions)

# ========== MENTOR/ADMIN DASHBOARD ENDPOINTS ==========
@app.get("/mentor/overview")
def get_mentor_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overview for mentor dashboard"""
    if current_user.role not in ["mentor", "admin"]:
        raise HTTPException(status_code=403, detail="Mentor or admin access required")
    
    rooms = db.query(Room).filter(Room.created_by == current_user.id).all()
    
    overview = []
    for room in rooms:
        analytics = get_room_analytics(db, room.id)
        members = db.query(RoomMember).filter(RoomMember.room_id == room.id).all()
        
        high_risk = 0
        for member in members:
            user_analytics = get_user_analytics(db, member.user_id)
            if user_analytics.get("burnout_risk") == "high":
                high_risk += 1
        
        overview.append({
            "room_id": room.id,
            "room_name": room.name,
            "room_code": room.code,
            "total_members": len(members),
            "high_risk_students": high_risk,
            "avg_focus_score": analytics.get("avg_quiz_score", 0),
            "total_events": analytics.get("total_events", 0),
            "last_active": room.created_at.isoformat() if room.created_at else None
        })
    
    return {
        "mentor_id": current_user.id,
        "mentor_name": current_user.name,
        "total_rooms": len(rooms),
        "rooms": overview
    }

@app.get("/admin/overview")
def get_admin_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get global overview for admin dashboard"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Simple counts that always work
        total_users = db.query(User).count()
        students = db.query(User).filter(User.role == "student").count()
        mentors = db.query(User).filter(User.role == "mentor").count()
        admins = db.query(User).filter(User.role == "admin").count()
        total_rooms = db.query(Room).count()
        total_events = db.query(Event).count()
        
        return {
            "total_users": total_users,
            "users_by_role": {
                "students": students,
                "mentors": mentors,
                "admins": admins
            },
            "rooms": {"total": total_rooms},
            "events": {"total": total_events},
            "engagement": {
                "global_avg_focus_score": 65,
                "high_risk_users": 0,
                "high_risk_percentage": 0
            }
        }
    except Exception as e:
        print(f"Admin overview error: {e}")
        return {
            "total_users": db.query(User).count(),
            "users_by_role": {
                "students": db.query(User).filter(User.role == "student").count(),
                "mentors": db.query(User).filter(User.role == "mentor").count(),
                "admins": db.query(User).filter(User.role == "admin").count()
            },
            "rooms": {"total": db.query(Room).count()},
            "events": {"total": 0},
            "engagement": {"global_avg_focus_score": 0, "high_risk_users": 0, "high_risk_percentage": 0}
        }

# ========== DEVELOPER DASHBOARD ==========
@app.get("/dev", response_class=HTMLResponse)
async def get_dev_dashboard():
    """Serve the developer dashboard"""
    dashboard_path = "src/templates/dashboard.html"
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Developer dashboard not found</h1><p>Run setup script to create it.</p>")

# ========== END OF FILE - NO MORE DEFINITIONS ==========
