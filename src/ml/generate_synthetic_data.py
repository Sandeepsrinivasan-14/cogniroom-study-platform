"""
Synthetic Data Generator for ML Models
Generates realistic study session data for training
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

class SyntheticDataGenerator:
    def __init__(self):
        self.num_users = 100
        self.num_sessions = 1000
        
    def generate_user_profiles(self):
        """Generate synthetic user profiles"""
        users = []
        for i in range(self.num_users):
            user = {
                'user_id': i + 1,
                'age': random.randint(18, 35),
                'study_habit': random.choice(['morning', 'afternoon', 'night']),
                'avg_sleep': round(random.uniform(5, 9), 1),
                'baseline_focus': random.randint(40, 90)
            }
            users.append(user)
        return pd.DataFrame(users)
    
    def generate_sessions(self, users_df):
        """Generate synthetic study sessions"""
        sessions = []
        
        for session_id in range(self.num_sessions):
            user = users_df.sample(1).iloc[0]
            
            # Session timing
            start_hour = random.randint(6, 23)
            duration = random.randint(30, 180)  # minutes
            
            # Calculate burnout indicators
            late_night = 1 if start_hour > 22 or start_hour < 5 else 0
            session_length = duration / 60  # hours
            
            # Generate cognitive load pattern
            load_scores = []
            for minute in range(0, duration, 5):
                base_load = random.uniform(0.3, 0.7)
                # Load increases over time
                fatigue = (minute / duration) * 0.3
                load = min(1.0, base_load + fatigue + random.gauss(0, 0.1))
                load_scores.append(round(load, 2))
            
            avg_load = np.mean(load_scores)
            max_load = max(load_scores)
            load_variance = np.var(load_scores)
            
            # Quiz performance (if any)
            has_quiz = random.random() > 0.4
            quiz_score = None
            if has_quiz:
                # Score decreases with high load
                quiz_score = max(0, min(100, 
                    100 - (avg_load * 50) + random.gauss(0, 10)
                ))
            
            # Burnout risk calculation (for training labels)
            burnout_risk = 'low'
            risk_score = 0
            if late_night:
                risk_score += 30
            if session_length > 3:
                risk_score += 20
            if avg_load > 0.7:
                risk_score += 25
            if load_variance > 0.1:
                risk_score += 15
                
            if risk_score > 60:
                burnout_risk = 'high'
            elif risk_score > 30:
                burnout_risk = 'medium'
            
            session = {
                'session_id': session_id,
                'user_id': user['user_id'],
                'start_hour': start_hour,
                'duration_minutes': duration,
                'late_night': late_night,
                'avg_load': round(avg_load, 2),
                'max_load': round(max_load, 2),
                'load_variance': round(load_variance, 4),
                'has_quiz': int(has_quiz),
                'quiz_score': round(quiz_score, 2) if quiz_score else None,
                'message_count': random.randint(0, 50),
                'whiteboard_actions': random.randint(0, 30),
                'burnout_risk': burnout_risk
            }
            sessions.append(session)
        
        return pd.DataFrame(sessions)

if __name__ == "__main__":
    generator = SyntheticDataGenerator()
    
    # Generate data
    users = generator.generate_user_profiles()
    sessions = generator.generate_sessions(users)
    
    # Save to CSV
    users.to_csv('src/ml/synthetic_users.csv', index=False)
    sessions.to_csv('src/ml/synthetic_sessions.csv', index=False)
    
    print(f"? Generated {len(users)} users and {len(sessions)} sessions")
    print("\nSample session data:")
    print(sessions.head())
