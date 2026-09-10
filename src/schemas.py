from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    email: str
    password: str


class RoomCreate(BaseModel):
    name: str

class RoomOut(BaseModel):
    id: int
    name: str
    code: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RoomListOut(BaseModel):
    rooms: List[RoomOut]


# --- Phase 5: Quiz schemas ---

class QuestionCreate(BaseModel):
    text: str
    correct_answer: Optional[str] = None

class QuestionOut(BaseModel):
    id: int
    text: str
    correct_answer: Optional[str] = None

    class Config:
        from_attributes = True

class QuizCreate(BaseModel):
    title: str
    questions: List[QuestionCreate]

class QuizOut(BaseModel):
    id: int
    room_id: int
    title: str
    questions: List[QuestionOut]

    class Config:
        from_attributes = True


# --- Phase 5B: Quiz attempt schemas ---

class AnswerIn(BaseModel):
    question_id: int
    answer: str

class QuizAttemptCreate(BaseModel):
    answers: List[AnswerIn]

class QuestionAnswerOut(BaseModel):
    question_id: int
    given_answer: str
    is_correct: bool

class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: int
    total_questions: int
    answers: List[QuestionAnswerOut]


# --- Phase 6: Flashcard schemas ---

class FlashcardCreate(BaseModel):
    front: str
    back: str

class FlashcardOut(BaseModel):
    id: int
    front: str
    back: str

    class Config:
        from_attributes = True

class FlashcardDeckCreate(BaseModel):
    title: str
    topic_tag: Optional[str] = None
    flashcards: List[FlashcardCreate] = []

class FlashcardDeckOut(BaseModel):
    id: int
    room_id: int
    title: str
    topic_tag: Optional[str] = None
    created_by: int
    flashcards: List[FlashcardOut] = []

    class Config:
        from_attributes = True

# --- Phase 8: Webcam load schemas ---

class WebcamLoadIn(BaseModel):
    user_id: int
    load_score: float  # 0.0 - 1.0

class WebcamLoadOut(BaseModel):
    id: int
    room_id: int
    user_id: int
    load_score: float
    created_at: datetime

    class Config:
        from_attributes = True

# --- Phase 7: Scheduler schemas ---

class ScheduleItemCreate(BaseModel):
    title: str
    start_time: datetime
    duration_minutes: int

class ScheduleItemOut(BaseModel):
    id: int
    room_id: int
    title: str
    start_time: datetime
    duration_minutes: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class SentimentResponse(BaseModel):
    sentiment_score: int  # -1 negative, 0 neutral, 1 positive
    confidence: float

    class Config:
        from_attributes = True

class AgentMemoryResponse(BaseModel):
    room_id: int
    memory: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class AgentMemoryUpdate(BaseModel):
    memory: Dict[str, Any]

    class Config:
        from_attributes = True
