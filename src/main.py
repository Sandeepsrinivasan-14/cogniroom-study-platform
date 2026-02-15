import os
import random
import string
from collections import defaultdict
from datetime import datetime
from time import time
import time
import requests
import socketio
import sqlalchemy
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from .database import SessionLocal, engine, get_db, Base
from .models import (
    User,
    Room,
    RoomMember,
    Event,
    Quiz,
    Question,
    QuizAttempt,
    QuestionAnswer,
)
from .schemas import (
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

# -------- Socket.IO server --------
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI(title="StudyRoom Backend")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    """Wait for DB + create tables safely"""
    max_retries = 30
    for i in range(max_retries):
        try:
            with SessionLocal() as db:
                # Test connection
                db.execute("SELECT 1")
                db.commit()
                # Create tables
                Base.metadata.create_all(bind=engine)
                print("✅ DB ready + tables created!")
                return
        except Exception:
            print(f"DB retry {i+1}/{max_retries}...")
            time.sleep(1)
    print("❌ DB failed after retries")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/socket-health")
def socket_health():
    return {"status": "socket-ok"}


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
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


# --- Phase 4: Event logging helper ---
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


# -------- Rooms + Membership --------
def generate_room_code(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


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
        role=current_user.role
        if isinstance(current_user.role, str)
        else str(current_user.role),
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

    existing = (
        db.query(RoomMember)
        .filter(
            RoomMember.room_id == room.id,
            RoomMember.user_id == current_user.id,
        )
        .first()
    )
    if not existing:
        membership = RoomMember(
            room_id=room.id,
            user_id=current_user.id,
            role=current_user.role
            if isinstance(current_user.role, str)
            else str(current_user.role),
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
    memberships = (
        db.query(RoomMember).filter(RoomMember.user_id == current_user.id).all()
    )
    room_ids = [m.room_id for m in memberships]
    if not room_ids:
        return {"rooms": []}
    rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
    return {"rooms": rooms}


# --- Phase 4: fetch events for a room ---
@app.get("/rooms/{room_id}/events")
def get_room_events(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500),
):
    membership = (
        db.query(RoomMember)
        .filter(
            RoomMember.room_id == room_id,
            RoomMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    q = (
        db.query(Event)
        .filter(Event.room_id == room_id)
        .order_by(Event.created_at.desc())
        .limit(limit)
    )
    events = q.all()
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


# -------- Socket.IO Events on default namespace "" --------
async def async_log_event(room_id: int | str, event_type: str, payload: str):
    db = SessionLocal()
    try:
        evt = Event(
            room_id=int(room_id),
            type=event_type,
            payload=payload,
        )
        db.add(evt)
        db.commit()
    finally:
        db.close()


@sio.event
async def connect(sid, environ):
    print(f"Client connected on default namespace: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected from default namespace: {sid}")


# ✅ FIXED: Changed from join_room_socket to joinroom, and room_id to roomid
@sio.event
async def joinroom(sid, data):
    room_id = str(data.get("roomid"))  # FIXED: client sends "roomid", not "room_id"
    print(f"joinroom called for sid={sid}, room_id={room_id}")
    await sio.save_session(sid, {"room_id": room_id})
    await sio.enter_room(sid, room=room_id)
    await sio.emit(
        "system_message",
        {"msg": f"User joined room {room_id}"},
        room=room_id,
    )


# ✅ FIXED: Changed from chat_message to chatmessage
@sio.event
async def chatmessage(sid, data):
    session = await sio.get_session(sid)
    room_id = session.get("room_id")
    message = data.get("message")
    print(f"chatmessage from sid={sid} in room={room_id}: {message}")
    # FIXED: Emit "chatmessage" not "chat_message"
    await sio.emit("chatmessage", {"message": message}, room=room_id)


@sio.event
async def whiteboard_update(sid, data):
    session = await sio.get_session(sid)
    room_id = str(data.get("room_id") or session.get("room_id"))
    user_id = data.get("user_id")

    if not room_id or user_id is None:
        return

    await sio.emit(
        "whiteboard_update",
        data,
        room=room_id,
    )

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

    await sio.emit(
        "quiz_start",
        data,
        room=room_id,
    )

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

    await sio.emit(
        "quiz_answer",
        data,
        room=room_id,
    )

    await async_log_event(
        room_id=room_id,
        event_type="quiz_answered",
        payload=(
            f"quiz_id={quiz_id},question_id={question_id},user_id={user_id},"
            f"selected_index={selected_index},response_time_ms={response_time_ms}"
        ),
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


# --- Webcam load + live metrics ---
live_metrics: dict[int, dict[int, dict[str, float]]] = defaultdict(dict)


def update_live_load(room_id: int, user_id: int, load_score: float) -> None:
    live_metrics[room_id][user_id] = {
        "load_score": load_score,
        "ts": time(),
    }


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


# --- Phase 5: Quiz endpoints ---
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

    membership = (
        db.query(RoomMember)
        .filter(
            RoomMember.room_id == room_id,
            RoomMember.user_id == current_user.id,
        )
        .first()
    )
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

    membership = (
        db.query(RoomMember)
        .filter(
            RoomMember.room_id == room_id,
            RoomMember.user_id == current_user.id,
        )
        .first()
    )
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

    result: list[QuizOut] = []
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


# --- Phase 5B: Quiz attempts + scoring ---
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

    room = db.query(Room).filter(Room.id == quiz.room_id).first()
    membership = (
        db.query(RoomMember)
        .filter(
            RoomMember.room_id == quiz.room_id,
            RoomMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    questions_by_id = {q.id: q for q in questions}
    total = len(questions)
    if total == 0:
        raise HTTPException(status_code=400, detail="Quiz has no questions")

    answer_rows: list[QuestionAnswer] = []
    correct = 0
    for ans in attempt_in.answers:
        question = questions_by_id.get(ans.question_id)
        if not question:
            continue
        is_correct = ans.given_answer.strip() == question.text.strip()  # placeholder
        qa = QuestionAnswer(
            question_id=question.id,
            user_id=current_user.id,
            given_answer=ans.given_answer,
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
                payload=(
                    f"quiz_id={quiz.id};question_id={question.id};"
                    f"is_correct={bool(is_correct)}"
                ),
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


# --- Phase 6: user events view ---
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

    events = (
        q.order_by(Event.created_at.desc())
        .limit(limit)
        .all()
    )

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


# --- Phase 6: room quiz stats ---
@app.get("/rooms/{room_id}/stats/quiz")
def get_room_quiz_stats(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = (
        db.query(RoomMember)
        .filter(
            RoomMember.room_id == room_id,
            RoomMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    total_quizzes = (
        db.query(func.count(Quiz.id)).filter(Quiz.room_id == room_id).scalar() or 0
    )

    attempts_q = (
        db.query(
            func.count(QuizAttempt.id).label("attempts"),
            func.avg(
                QuizAttempt.score * 1.0 / QuizAttempt.total_questions
            ).label("avg_ratio"),
        )
        .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
        .filter(Quiz.room_id == room_id)
    ).one()

    total_attempts = attempts_q.attempts or 0
    avg_score_percent: float | None = None
    if attempts_q.avg_ratio is not None:
        avg_score_percent = float(attempts_q.avg_ratio) * 100.0

    return {
        "room_id": room_id,
        "total_quizzes": int(total_quizzes),
        "total_attempts": int(total_attempts),
        "average_score_percent": avg_score_percent,
    }


@app.get("/rooms/{room_id}/metrics/live")
def get_room_live_metrics(
    room_id: int,
    current_user: User = Depends(get_current_user),
):
    room_data = live_metrics.get(room_id, {})
    if not room_data:
        return {
            "room_id": room_id,
            "users": [],
            "group_avg_load": None,
        }

    users = [
        {"user_id": uid, "load_score": v["load_score"]}
        for uid, v in room_data.items()
    ]
    group_avg = sum(v["load_score"] for v in room_data.values()) / len(room_data)

    return {
        "room_id": room_id,
        "users": users,
        "group_avg_load": group_avg,
    }


@app.get("/debug/room/{room_id}/events/raw")
def debug_room_events_raw(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Event)
        .filter(Event.room_id == room_id)
        .order_by(Event.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": e.id,
            "room_id": e.room_id,
            "type": e.type,
            "payload": e.payload,
        }
        for e in rows
    ]


# --- Phase 7: Analytics JSON endpoints ---
@app.get("/analytics/room/{room_id}/activity")
def get_room_activity_analytics(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    membership = (
        db.query(RoomMember)
        .filter(
            RoomMember.room_id == room_id,
            RoomMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    type_rows = (
        db.query(Event.type, func.count(Event.id))
        .filter(Event.room_id == room_id)
        .group_by(Event.type)
        .all()
    )
    by_type = {t: int(c) for (t, c) in type_rows}

    date_rows = (
        db.query(func.date(Event.created_at), func.count(Event.id))
        .filter(Event.room_id == room_id)
        .group_by(func.date(Event.created_at))
        .order_by(func.date(Event.created_at))
        .all()
    )
    by_day = [
        {"date": str(d), "count": int(c)}
        for (d, c) in date_rows
    ]

    user_rows = (
        db.query(Event.user_id, func.count(Event.id))
        .filter(Event.room_id == room_id)
        .group_by(Event.user_id)
        .all()
    )
    by_user = [
        {"user_id": uid, "event_count": int(c)}
        for (uid, c) in user_rows
        if uid is not None
    ]

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
        rows = (
            db.query(Event.type, func.count(Event.id).label("count"))
            .filter(Event.payload.like(f"%user_id={user_id}%"))
            .group_by(Event.type)
            .all()
        )
        by_type = {row.type: row.count for row in rows}
        return {"user_id": user_id, "by_type": by_type}
    finally:
        db.close()


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
        rows = (
            db.query(Event.type, func.count(Event.id).label("count"))
            .filter(Event.payload.like(f"%user_id={body.user_id}%"))
            .group_by(Event.type)
            .all()
        )
        counts = {row.type: row.count for row in rows}
        base = (
            counts.get("quiz_started", 0)
            + counts.get("question_answered", 0)
            + counts.get("webcam_load_update", 0)
        )
        score = min(1.0, base / 10.0)
        return EngagementScoreResponse(
            user_id=body.user_id,
            score=score,
            details=counts,
        )
    finally:
        db.close()


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
                "content": (
                    "You generate short quiz questions with answers. "
                    "Output plain text lines in the format: question || answer."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
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
    questions: list[QuizGenQuestion] = []
    for line in text.splitlines():
        if "||" not in line:
            continue
        q, a = line.split("||", 1)
        q = q.strip("- ").strip()
        a = a.strip()
        if q and a:
            questions.append(QuizGenQuestion(question=q, answer=a))
    return QuizGenResponse(questions=questions)


# ✅ FIXED: Mount Socket.IO correctly at the end
app = socketio.ASGIApp(sio, other_asgi_app=app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)