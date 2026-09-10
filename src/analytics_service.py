from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from .models import Event, User, Room, RoomMember, QuizAttempt, Quiz
import json
from typing import Dict, Any, List

# Import ML service for model-based predictions
try:
    from .ml.ml_service import ml_service
    ML_AVAILABLE = True
    print("[OK] ML models available for analytics")
except Exception as e:
    ML_AVAILABLE = False
    ml_service = None
    print(f"[WARN] ML models not available, using heuristics: {e}")

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

def _extract_ml_features(events: list, quiz_attempts: list, webcam_loads: list) -> Dict[str, Any]:
    """Extract feature vector for ML models from raw data"""
    # Time-based features
    start_hours = []
    late_night_count = 0
    total_duration_minutes = 0

    if events:
        timestamps = [e.created_at for e in events if e.created_at]
        if timestamps:
            timestamps.sort()
            start_hours = [t.hour for t in timestamps]
            total_duration_minutes = (timestamps[-1] - timestamps[0]).total_seconds() / 60
            late_night_count = sum(1 for h in start_hours if h >= 22 or h <= 4)

    # Event type counts
    event_types = {}
    for e in events:
        event_types[e.type] = event_types.get(e.type, 0) + 1

    # Load features
    avg_load = sum(webcam_loads) / len(webcam_loads) if webcam_loads else 0.5
    max_load = max(webcam_loads) if webcam_loads else 0.5
    load_variance = 0
    if len(webcam_loads) > 1:
        mean = avg_load
        load_variance = sum((x - mean) ** 2 for x in webcam_loads) / len(webcam_loads)

    # Quiz features
    has_quiz = 1 if quiz_attempts else 0
    quiz_score = 0
    if quiz_attempts:
        scores = [a.score / max(a.total_questions, 1) * 100 for a in quiz_attempts]
        quiz_score = sum(scores) / len(scores)

    return {
        "start_hour": start_hours[0] if start_hours else 12,
        "duration_minutes": total_duration_minutes,
        "late_night": late_night_count,
        "avg_load": avg_load,
        "max_load": max_load,
        "load_variance": load_variance,
        "has_quiz": has_quiz,
        "message_count": event_types.get("chat_message", 0),
        "whiteboard_actions": event_types.get("whiteboard_update", 0),
        "quiz_score": quiz_score,
    }


def get_user_analytics(db: Session, user_id: int) -> Dict[str, Any]:
    """Get comprehensive analytics for a user, using ML models when available"""
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
        
        # Average cognitive load
        avg_load = sum(webcam_loads) / len(webcam_loads) if webcam_loads else 0
        
        # Extract ML features
        ml_features = _extract_ml_features(events, quiz_attempts, webcam_loads)
        
        # === ML-POWERED PREDICTIONS (with honest source reporting) ===
        if ML_AVAILABLE and ml_service and ml_service.models_loaded:
            burnout_risk, burnout_confidence, burnout_src = ml_service.predict_burnout(ml_features)
            performance_grade, perf_confidence, perf_src = ml_service.predict_performance(ml_features)
            # Report ml_model only if BOTH predictions actually came from a model
            prediction_source = "ml_model" if burnout_src == "ml_model" and perf_src == "ml_model" else "heuristic"
        else:
            # Fallback to heuristics
            burnout_risk, burnout_confidence = _heuristic_burnout(events, quiz_attempts), 0.5
            performance_grade, perf_confidence = _heuristic_performance(ml_features), 0.5
            prediction_source = "heuristic"
        
        # Calculate focus score (0-100) — always heuristic, enhanced by ML data
        focus_score = 50  # Base score
        focus_score += min(events_by_type.get("chat_message", 0) * 2, 20)
        focus_score += int(avg_score * 0.3) if avg_score else 0
        if 0.4 <= avg_load <= 0.8:
            focus_score += 10
        elif avg_load > 0.9:
            focus_score -= 10
        focus_score = max(0, min(100, int(focus_score)))
        
        return {
            "user_id": user_id,
            "focus_score": focus_score,
            "burnout_risk": burnout_risk,
            "burnout_confidence": round(burnout_confidence, 2),
            "predicted_grade": performance_grade,
            "grade_confidence": round(perf_confidence, 2),
            "prediction_source": prediction_source,
            "avg_cognitive_load": round(avg_load, 2),
            "quiz_performance": round(avg_score, 2),
            "total_events": total_events,
            "messages_sent": events_by_type.get("chat_message", 0),
            "whiteboard_actions": events_by_type.get("whiteboard_update", 0),
            "events_by_type": events_by_type,
            "ml_features": ml_features,
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "error": str(e),
            "focus_score": 50,
            "burnout_risk": "unknown",
            "burnout_confidence": 0,
            "predicted_grade": "N/A",
            "grade_confidence": 0,
            "prediction_source": "error",
            "avg_cognitive_load": 0,
            "quiz_performance": 0,
            "total_events": 0,
            "messages_sent": 0,
            "whiteboard_actions": 0,
            "events_by_type": {},
            "ml_features": {},
        }


def _heuristic_burnout(events: list, quiz_attempts: list) -> str:
    """Fallback heuristic burnout detection when ML models are unavailable"""
    risk_score = 0
    late_nights = sum(1 for e in events if e.created_at and e.created_at.hour >= 22)
    if late_nights > 5:
        risk_score += 30
    elif late_nights > 2:
        risk_score += 15
    if len(quiz_attempts) >= 2:
        if quiz_attempts[-1].score < quiz_attempts[-2].score * 0.8:
            risk_score += 25
    if risk_score >= 50:
        return "high"
    elif risk_score >= 25:
        return "medium"
    return "low"


def _heuristic_performance(features: Dict[str, Any]) -> str:
    """Fallback heuristic performance prediction"""
    score = 50
    if features.get("has_quiz", 0) > 0:
        score += features.get("quiz_score", 50) * 0.3
    if features.get("load_variance", 0) < 0.05:
        score += 15
    if score >= 80:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 50:
        return "C"
    return "D"


def get_room_analytics(db: Session, room_id: int) -> Dict[str, Any]:
    """Get analytics for a room, with ML-powered per-member insights"""
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "Room not found"}
        
        events = db.query(Event).filter(Event.room_id == room_id).all()
        members = db.query(RoomMember).filter(RoomMember.room_id == room_id).all()
        
        total_events = len(events)
        events_by_type = {}
        events_by_user = {}
        room_loads = []

        for e in events:
            events_by_type[e.type] = events_by_type.get(e.type, 0) + 1
            if e.user_id:
                events_by_user[e.user_id] = events_by_user.get(e.user_id, 0) + 1
            if e.type == "webcam_load_update":
                payload = safe_json_loads(e.payload)
                if "load_score" in payload:
                    try:
                        room_loads.append(float(payload["load_score"]))
                    except (TypeError, ValueError):
                        pass

        avg_cognitive_load = round(sum(room_loads) / len(room_loads), 2) if room_loads else 0

        # Quiz stats
        quizzes = db.query(Quiz).filter(Quiz.room_id == room_id).all()
        quiz_ids = [q.id for q in quizzes]
        
        avg_quiz_score = 0
        total_attempts = 0
        if quiz_ids:
            attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id.in_(quiz_ids)).all()
            total_attempts = len(attempts)
            if attempts:
                avg_quiz_score = sum(a.score for a in attempts) / len(attempts)
        
        # Per-member risk summary (ML-powered)
        at_risk_members = []
        for member in members:
            try:
                user_analytics = get_user_analytics(db, member.user_id)
                if user_analytics.get("burnout_risk") in ["medium", "high"]:
                    at_risk_members.append({
                        "user_id": member.user_id,
                        "burnout_risk": user_analytics["burnout_risk"],
                        "focus_score": user_analytics["focus_score"],
                    })
            except:
                pass
        
        return {
            "room_id": room_id,
            "room_name": room.name if room else "Unknown",
            "total_members": len(members),
            "total_events": total_events,
            "events_by_type": events_by_type,
            "events_by_user": events_by_user,
            "total_quizzes": len(quizzes),
            "total_quiz_attempts": total_attempts,
            "avg_quiz_score": round(avg_quiz_score, 2) if avg_quiz_score else None,
            "avg_cognitive_load": avg_cognitive_load,
            "at_risk_members": at_risk_members,
            "ml_powered": ML_AVAILABLE,
        }
    except Exception as e:
        return {
            "room_id": room_id,
            "error": str(e),
            "total_members": 0,
            "total_events": 0,
            "events_by_type": {},
            "events_by_user": {},
        }
