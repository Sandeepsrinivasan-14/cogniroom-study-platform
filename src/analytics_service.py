from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .models import Event, User, Room, RoomMember, QuizAttempt, Quiz
import json
from typing import Dict, Any, List

def safe_json_loads(payload_str: str) -> Dict:
    """Safely parse JSON payload"""
    if not payload_str:
        return {}
    try:
        if isinstance(payload_str, dict):
            return payload_str
        return json.loads(payload_str)
    except:
        return {}

def get_user_analytics(db: Session, user_id: int) -> Dict[str, Any]:
    """Get comprehensive analytics for a user"""
    try:
        # Get user's events (all time)
        events = db.query(Event).filter(Event.user_id == user_id).all()
        
        # Calculate metrics
        total_events = len(events)
        events_by_type = {}
        webcam_loads = []
        
        for e in events:
            events_by_type[e.type] = events_by_type.get(e.type, 0) + 1
            if e.type == "webcam_load_update":
                payload = safe_json_loads(e.payload)
                if "load_score" in payload:
                    webcam_loads.append(float(payload["load_score"]))
        
        # Get quiz performance
        quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).all()
        
        avg_score = 0
        if quiz_attempts:
            avg_score = sum(a.score for a in quiz_attempts) / len(quiz_attempts)
        
        # Calculate average cognitive load
        avg_load = 0
        if webcam_loads:
            avg_load = sum(webcam_loads) / len(webcam_loads)
        
        # Calculate focus score (0-100)
        focus_score = 50  # Base score
        focus_score += min(events_by_type.get("chat_message", 0) * 2, 20)
        focus_score += int(avg_score * 0.3) if avg_score else 0
        if 0.4 <= avg_load <= 0.8:
            focus_score += 10
        elif avg_load > 0.9:
            focus_score -= 10
        focus_score = max(0, min(100, int(focus_score)))
        
        # Calculate burnout risk
        burnout_risk = "low"
        risk_score = 0
        
        # Check late night sessions
        late_nights = 0
        for e in events:
            if e.created_at and e.created_at.hour >= 22:
                late_nights += 1
        if late_nights > 5:
            risk_score += 30
        elif late_nights > 2:
            risk_score += 15
        
        # Check quiz performance decline
        if len(quiz_attempts) >= 2:
            if quiz_attempts[-1].score < quiz_attempts[-2].score * 0.8:
                risk_score += 25
        
        if risk_score >= 50:
            burnout_risk = "high"
        elif risk_score >= 25:
            burnout_risk = "medium"
        
        return {
            "user_id": user_id,
            "focus_score": focus_score,
            "burnout_risk": burnout_risk,
            "avg_cognitive_load": round(avg_load, 2),
            "quiz_performance": round(avg_score, 2),
            "total_events": total_events,
            "messages_sent": events_by_type.get("chat_message", 0),
            "whiteboard_actions": events_by_type.get("whiteboard_update", 0),
            "events_by_type": events_by_type
        }
    except Exception as e:
        # Return error info for debugging
        return {
            "user_id": user_id,
            "error": str(e),
            "focus_score": 50,
            "burnout_risk": "unknown",
            "avg_cognitive_load": 0,
            "quiz_performance": 0,
            "total_events": 0,
            "messages_sent": 0,
            "whiteboard_actions": 0,
            "events_by_type": {}
        }

def get_room_analytics(db: Session, room_id: int) -> Dict[str, Any]:
    """Get analytics for a room"""
    try:
        # Check if room exists
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "Room not found"}
        
        # Get room events
        events = db.query(Event).filter(Event.room_id == room_id).all()
        
        # Get room members
        members = db.query(RoomMember).filter(RoomMember.room_id == room_id).all()
        
        # Calculate metrics
        total_events = len(events)
        events_by_type = {}
        events_by_user = {}
        
        for e in events:
            events_by_type[e.type] = events_by_type.get(e.type, 0) + 1
            if e.user_id:
                events_by_user[e.user_id] = events_by_user.get(e.user_id, 0) + 1
        
        # Get quiz stats
        quizzes = db.query(Quiz).filter(Quiz.room_id == room_id).all()
        quiz_ids = [q.id for q in quizzes]
        
        avg_quiz_score = 0
        total_attempts = 0
        if quiz_ids:
            attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id.in_(quiz_ids)).all()
            total_attempts = len(attempts)
            if attempts:
                avg_quiz_score = sum(a.score for a in attempts) / len(attempts)
        
        return {
            "room_id": room_id,
            "room_name": room.name if room else "Unknown",
            "total_members": len(members),
            "total_events": total_events,
            "events_by_type": events_by_type,
            "events_by_user": events_by_user,
            "total_quizzes": len(quizzes),
            "total_quiz_attempts": total_attempts,
            "avg_quiz_score": round(avg_quiz_score, 2) if avg_quiz_score else None
        }
    except Exception as e:
        return {
            "room_id": room_id,
            "error": str(e),
            "total_members": 0,
            "total_events": 0,
            "events_by_type": {},
            "events_by_user": {}
        }
