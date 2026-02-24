"""
Redis Service for caching and real-time data
"""

import redis
import json
import os
import pickle
from typing import Dict, Any, Optional

class RedisService:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        self.connect()
    
    def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=False)
            self.client.ping()
            print("? Connected to Redis")
        except Exception as e:
            print(f"?? Redis connection failed: {e}")
            self.client = None
    
    def set_live_metrics(self, room_id: int, user_id: int, load_score: float, ts: float):
        """Store live metrics in Redis"""
        if not self.client:
            return
        
        key = f"room:{room_id}:metrics"
        # Store as hash
        self.client.hset(
            key,
            str(user_id),
            pickle.dumps({"load_score": load_score, "ts": ts})
        )
        # Set expiry (10 minutes)
        self.client.expire(key, 600)
    
    def get_live_metrics(self, room_id: int) -> Dict[int, Dict[str, float]]:
        """Get live metrics for a room"""
        if not self.client:
            return {}
        
        key = f"room:{room_id}:metrics"
        data = self.client.hgetall(key)
        
        result = {}
        for user_id_bytes, value_bytes in data.items():
            try:
                user_id = int(user_id_bytes.decode())
                value = pickle.loads(value_bytes)
                result[user_id] = value
            except:
                continue
        
        return result
    
    def cache_analytics(self, user_id: int, analytics_data: Dict, ttl: int = 300):
        """Cache user analytics to reduce DB load"""
        if not self.client:
            return
        
        key = f"analytics:user:{user_id}"
        self.client.setex(
            key,
            ttl,
            json.dumps(analytics_data)
        )
    
    def get_cached_analytics(self, user_id: int) -> Optional[Dict]:
        """Get cached analytics"""
        if not self.client:
            return None
        
        key = f"analytics:user:{user_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def store_session(self, session_id: str, session_data: Dict, ttl: int = 3600):
        """Store active session data"""
        if not self.client:
            return
        
        key = f"session:{session_id}"
        self.client.setex(
            key,
            ttl,
            json.dumps(session_data)
        )
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        if not self.client:
            return None
        
        key = f"session:{session_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Increment a counter in Redis"""
        if not self.client:
            return 0
        return self.client.incrby(key, amount)
    
    def get_counter(self, key: str) -> int:
        """Get counter value"""
        if not self.client:
            return 0
        val = self.client.get(key)
        return int(val) if val else 0

# Singleton instance
redis_service = RedisService()
