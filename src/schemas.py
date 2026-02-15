from pydantic import BaseModel
from typing import List

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

    class Config:
        from_attributes = True

class RoomListOut(BaseModel):
    rooms: List[RoomOut]


# --- Phase 5: Quiz schemas ---
from typing import List

class QuestionCreate(BaseModel):
    text: str

class QuestionOut(BaseModel):
    id: int
    text: str

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
from typing import List

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
