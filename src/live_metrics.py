"""
Live metrics management with Redis
"""

from typing import Dict, Optional
from time import time
from datetime import datetime
from src.redis_service import redis_service

def update_live_load(room_id: int, user_id: int, load_score: float):
    """Update live load score for a user in a room using Redis"""
    redis_service.set_live_metrics(room_id, user_id, load_score, time())

def get_room_live_metrics(room_id: int) -> Dict:
    """Get live metrics for a room from Redis"""
    room_data = redis_service.get_live_metrics(room_id)
    
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
    latest_ts = 0
    
    for uid, data in room_data.items():
        users.append({
            "user_id": uid,
            "load_score": data["load_score"],
            "last_active": datetime.fromtimestamp(data["ts"]).isoformat()
        })
        total_load += data["load_score"]
        latest_ts = max(latest_ts, data["ts"])
    
    group_avg = total_load / len(room_data) if room_data else None
    
    return {
        "room_id": room_id,
        "users": users,
        "group_avg_load": round(group_avg, 2) if group_avg else None,
        "total_users": len(users),
        "last_updated": datetime.fromtimestamp(latest_ts).isoformat() if latest_ts else None
    }

def cleanup_old_metrics(max_age_seconds: int = 300):
    """Redis handles expiry automatically"""
    pass
