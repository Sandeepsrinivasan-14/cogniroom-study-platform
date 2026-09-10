import json
import requests
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from src.models import Event, User, Room, QuizAttempt
from .analytics_service import get_user_analytics, get_room_analytics
import time

class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.model = "tinyllama"
        self.ollama_url = "http://localhost:11434"
        print(f"?? TEST MODE: Using {self.model}")
    
    def _call_ollama(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 150}
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            print(f"Error: {e}")
        return ""
    
    def _extract_json(self, text: str) -> List[Dict]:
        try:
            return json.loads(text)
        except:
            import re
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return [{"type": "action", "target": "room", "label": "Take a Break", "message": "Consider taking a break.", "severity": "info"}]
    
    def generate_load_actions(self, room_id: int) -> List[Dict]:
        try:
            prompt = "Suggest 2 helpful actions for a study room. Return as JSON array."
            response = self._call_ollama(prompt)
            return self._extract_json(response) if response else self._extract_json("")
        except:
            return self._extract_json("")
    
    def generate_burnout_advice(self, user_id: int) -> List[Dict]:
        return self._extract_json("")
    
    def generate_learning_plan(self, target_type: str, target_id: int) -> List[Dict]:
        return self._extract_json("")
