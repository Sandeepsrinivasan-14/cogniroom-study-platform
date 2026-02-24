import json
import requests
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from .models import Event, User, Room, QuizAttempt
from .analytics_service import get_user_analytics, get_room_analytics
import time
import os

class AgentService:
    """Multi-agent AI service with automatic failover between models"""
    
    def __init__(self, db: Session):
        self.db = db
        # Primary model: deepseek-r1:8b (excellent for reasoning)
        self.primary_model = "deepseek-r1:8b"
        # Fallback model: tinyllama (ultra fast, small footprint)
        self.fallback_model = "tinyllama"
        self.ollama_url = "http://172.26.96.1:11434"
        
        # Track which model we're using
        self.current_model = self.primary_model
        self.fallback_count = 0
        self.max_fallbacks = 3  # After 3 fallbacks, try primary again
        
        print(f"?? AI Agent Service initialized")
        print(f"   Primary: {self.primary_model}")
        print(f"   Fallback: {self.fallback_model}")
    
    def _call_ollama(self, prompt: str, use_fallback: bool = False) -> str:
        """Call Ollama API with automatic failover"""
        model = self.fallback_model if use_fallback else self.current_model
        
        # Different settings for different models
        if model == "deepseek-r1:8b":
            max_tokens = 300
            timeout = 25
        else:  # tinyllama - faster, smaller responses
            max_tokens = 150
            timeout = 15
        
        for attempt in range(2):  # Try twice
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": max_tokens,
                            "top_k": 40,
                            "top_p": 0.9
                        }
                    },
                    timeout=timeout
                )
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json().get("response", "")
                    print(f"? {model} responded in {elapsed:.2f}s")
                    
                    # Update model tracking
                    if use_fallback:
                        self.fallback_count += 1
                        if self.fallback_count >= self.max_fallbacks:
                            print("?? Trying primary model again...")
                            self.current_model = self.primary_model
                            self.fallback_count = 0
                    
                    return result
                else:
                    print(f"?? {model} error: {response.status_code}")
                    
            except Exception as e:
                print(f"?? {model} attempt {attempt+1} failed: {type(e).__name__}")
                time.sleep(1)
        
        # If we get here, both attempts failed
        return ""
    
    def _get_response_with_failover(self, prompt: str) -> str:
        """Get response with automatic failover between models"""
        # Try primary model first
        response = self._call_ollama(prompt, use_fallback=False)
        
        # If primary failed, try fallback
        if not response or len(response) < 10:
            print(f"?? Primary model failed, switching to {self.fallback_model}")
            self.current_model = self.fallback_model
            response = self._call_ollama(prompt, use_fallback=True)
        
        # If both failed, use hardcoded fallback
        if not response or len(response) < 10:
            print("? Both models failed, using hardcoded response")
            return ""
        
        return response
    
    def _get_fallback_response(self, agent_type: str) -> str:
        """Hardcoded fallback when all models fail"""
        if agent_type == "load":
            return json.dumps([{
                "type": "action", "target": "room",
                "label": "Take a Break",
                "message": "Consider taking a 5-minute break to recharge.",
                "severity": "info"
            }])
        elif agent_type == "burnout":
            return json.dumps([{
                "type": "advice", "target": "user",
                "label": "Rest Well",
                "message": "Make sure to get enough sleep between study sessions.",
                "severity": "info"
            }])
        else:
            return json.dumps([{
                "type": "plan", "target": "user",
                "label": "Keep Learning",
                "message": "Regular practice leads to improvement.",
                "severity": "info"
            }])
    
    def _extract_json(self, text: str) -> List[Dict]:
        """Extract JSON array from text response"""
        try:
            return json.loads(text)
        except:
            import re
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return json.loads(self._get_fallback_response("load"))
    
    def generate_load_actions(self, room_id: int) -> List[Dict[str, Any]]:
        """Load Balancer Agent with failover"""
        try:
            analytics = get_room_analytics(self.db, room_id)
            from .live_metrics import get_room_live_metrics
            live_metrics = get_room_live_metrics(room_id)
            
            prompt = f"""You are a Load Balancer Agent for a study room. Based on this data, suggest 2 helpful actions.

Room: {analytics.get('total_members', 0)} members, {analytics.get('total_events', 0)} events
Current cognitive load: {live_metrics.get('group_avg_load', 'unknown')}

Return a JSON array with this exact format:
[
  {{
    "type": "action",
    "target": "room",
    "label": "Short action title",
    "message": "Helpful suggestion",
    "severity": "info"
  }}
]"""
            
            response = self._get_response_with_failover(prompt)
            if response:
                return self._extract_json(response)
            return json.loads(self._get_fallback_response("load"))
            
        except Exception as e:
            print(f"Error in load agent: {e}")
            return json.loads(self._get_fallback_response("load"))
    
    def generate_burnout_advice(self, user_id: int) -> List[Dict[str, Any]]:
        """Burnout Sentinel Agent with failover"""
        try:
            analytics = get_user_analytics(self.db, user_id)
            
            prompt = f"""You are a Burnout Sentinel wellness coach. Based on this student's data, give 2 well-being tips.

Student Data:
- Focus Score: {analytics.get('focus_score', 50)}/100
- Burnout Risk: {analytics.get('burnout_risk', 'unknown')}
- Average Cognitive Load: {analytics.get('avg_cognitive_load', 0)}
- Total Study Events: {analytics.get('total_events', 0)}

Return a JSON array with this exact format:
[
  {{
    "type": "advice",
    "target": "user",
    "label": "Short advice title",
    "message": "Helpful wellness tip",
    "severity": "info"
  }}
]"""
            
            response = self._get_response_with_failover(prompt)
            if response:
                return self._extract_json(response)
            return json.loads(self._get_fallback_response("burnout"))
            
        except Exception as e:
            print(f"Error in burnout agent: {e}")
            return json.loads(self._get_fallback_response("burnout"))
    
    def generate_learning_plan(self, target_type: str, target_id: int) -> List[Dict[str, Any]]:
        """Performance Oracle Agent with failover"""
        try:
            if target_type == "user":
                analytics = get_user_analytics(self.db, target_id)
                prompt = f"""You are a Performance Oracle study advisor. Based on this student's data, give 2 learning tips.

Student Data:
- Focus Score: {analytics.get('focus_score', 50)}/100
- Quiz Performance: {analytics.get('quiz_performance', 0)}%
- Burnout Risk: {analytics.get('burnout_risk', 'unknown')}

Return a JSON array with this exact format:
[
  {{
    "type": "plan",
    "target": "user",
    "label": "Short plan title",
    "message": "Specific learning recommendation",
    "severity": "info"
  }}
]"""
            else:
                analytics = get_room_analytics(self.db, target_id)
                prompt = f"""You are a Performance Oracle group study advisor. Based on this room's data, give 2 group learning tips.

Room Data:
- Members: {analytics.get('total_members', 0)}
- Total Events: {analytics.get('total_events', 0)}
- Quiz Attempts: {analytics.get('total_quiz_attempts', 0)}

Return a JSON array with this exact format:
[
  {{
    "type": "plan",
    "target": "room",
    "label": "Short plan title",
    "message": "Group learning recommendation",
    "severity": "info"
  }}
]"""
            
            response = self._get_response_with_failover(prompt)
            if response:
                return self._extract_json(response)
            return json.loads(self._get_fallback_response("plan"))
            
        except Exception as e:
            print(f"Error in learning agent: {e}")
            return json.loads(self._get_fallback_response("plan"))

