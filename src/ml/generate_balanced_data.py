"""
Improved Synthetic Data Generator with Balanced Classes
"""

import pandas as pd
import numpy as np
import random

class BetterSyntheticDataGenerator:
    def __init__(self):
        self.num_users = 200
        self.num_sessions = 2000
    
    def generate_user_profiles(self):
        """Generate synthetic user profiles with varying capabilities"""
        users = []
        for i in range(self.num_users):
            # Different user types
            user_type = random.choice(['beginner', 'intermediate', 'advanced'])
            
            if user_type == 'beginner':
                baseline_focus = random.randint(30, 50)
                consistency = random.uniform(0.1, 0.2)
            elif user_type == 'intermediate':
                baseline_focus = random.randint(45, 70)
                consistency = random.uniform(0.05, 0.15)
            else:  # advanced
                baseline_focus = random.randint(65, 90)
                consistency = random.uniform(0.02, 0.08)
            
            user = {
                'user_id': i + 1,
                'user_type': user_type,
                'baseline_focus': baseline_focus,
                'consistency': consistency,
                'study_habit': random.choice(['morning', 'afternoon', 'night']),
                'avg_sleep': round(random.uniform(5, 9), 1)
            }
            users.append(user)
        return pd.DataFrame(users)
    
    def generate_sessions(self, users_df):
        """Generate synthetic study sessions with realistic grade distribution"""
        sessions = []
        
        for session_id in range(self.num_sessions):
            user = users_df.sample(1).iloc[0]
            
            # Session timing
            start_hour = random.randint(6, 23)
            duration = random.randint(15, 240)  # minutes
            late_night = 1 if start_hour > 22 or start_hour < 6 else 0
            
            # Generate cognitive load pattern based on user type
            base_load = random.uniform(0.2, 0.8)
            
            # Advanced users handle load better
            if user['user_type'] == 'advanced':
                load_variance = random.uniform(0.01, 0.05)
                fatigue_rate = 0.1
            elif user['user_type'] == 'intermediate':
                load_variance = random.uniform(0.03, 0.1)
                fatigue_rate = 0.2
            else:  # beginner
                load_variance = random.uniform(0.05, 0.2)
                fatigue_rate = 0.3
            
            # Generate load scores
            load_scores = []
            for minute in range(0, duration, 5):
                fatigue = (minute / duration) * fatigue_rate
                noise = random.gauss(0, load_variance)
                load = min(1.0, max(0.0, base_load + fatigue + noise))
                load_scores.append(round(load, 2))
            
            avg_load = np.mean(load_scores)
            max_load = max(load_scores)
            load_variance_calc = np.var(load_scores)
            
            # Quiz performance (correlated with user type and load)
            has_quiz = random.random() > 0.3
            
            if has_quiz:
                # Score based on user type and current load
                base_score = user['baseline_focus']
                load_penalty = avg_load * 30
                score = max(0, min(100, base_score - load_penalty + random.gauss(0, 10)))
                
                # Add some randomness for grade distribution
                if user['user_type'] == 'advanced':
                    score += random.uniform(5, 15)
                elif user['user_type'] == 'beginner':
                    score -= random.uniform(0, 10)
            else:
                score = None
            
            # Calculate performance grade (A/B/C/D)
            if has_quiz and score is not None:
                if score >= 80:
                    performance = 'A'
                elif score >= 65:
                    performance = 'B'
                elif score >= 50:
                    performance = 'C'
                else:
                    performance = 'D'
            else:
                # Even without quizzes, estimate performance from user type
                if user['user_type'] == 'advanced':
                    performance = random.choices(['A', 'B', 'C'], weights=[0.6, 0.3, 0.1])[0]
                elif user['user_type'] == 'intermediate':
                    performance = random.choices(['A', 'B', 'C', 'D'], weights=[0.2, 0.4, 0.3, 0.1])[0]
                else:  # beginner
                    performance = random.choices(['B', 'C', 'D'], weights=[0.2, 0.5, 0.3])[0]
            
            # Calculate burnout risk
            risk_score = 0
            if late_night:
                risk_score += 30
            if duration > 180:
                risk_score += 20
            if avg_load > 0.7:
                risk_score += 25
            if load_variance_calc > 0.1:
                risk_score += 15
            
            if risk_score > 60:
                burnout_risk = 'high'
            elif risk_score > 30:
                burnout_risk = 'medium'
            else:
                burnout_risk = 'low'
            
            session = {
                'session_id': session_id,
                'user_id': user['user_id'],
                'user_type': user['user_type'],
                'start_hour': start_hour,
                'duration_minutes': duration,
                'late_night': late_night,
                'avg_load': round(avg_load, 2),
                'max_load': round(max_load, 2),
                'load_variance': round(load_variance_calc, 4),
                'has_quiz': int(has_quiz),
                'quiz_score': round(score, 2) if score else None,
                'message_count': random.randint(0, 50),
                'whiteboard_actions': random.randint(0, 30),
                'burnout_risk': burnout_risk,
                'performance': performance
            }
            sessions.append(session)
        
        return pd.DataFrame(sessions)

if __name__ == "__main__":
    generator = BetterSyntheticDataGenerator()
    
    # Generate data
    users = generator.generate_user_profiles()
    sessions = generator.generate_sessions(users)
    
    # Save to CSV
    users.to_csv('src/ml/users_balanced.csv', index=False)
    sessions.to_csv('src/ml/sessions_balanced.csv', index=False)
    
    print(f"? Generated {len(users)} users and {len(sessions)} sessions")
    print("\n?? User type distribution:")
    print(users['user_type'].value_counts())
    
    print("\n?? Performance distribution:")
    print(sessions['performance'].value_counts())
    
    print("\n?? Burnout risk distribution:")
    print(sessions['burnout_risk'].value_counts())
    
    print("\nSample session data:")
    print(sessions[['user_id', 'performance', 'burnout_risk', 'avg_load', 'quiz_score']].head(10))
