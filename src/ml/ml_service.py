"""
ML Service Integration - Final Version
Connects trained models to your FastAPI endpoints
"""

import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
import os
import json

class MLService:
    """Service for all ML predictions"""
    
    def __init__(self):
        self.models_loaded = False
        self.burnout_model = None
        self.performance_model = None
        self.burnout_features = None
        self.grade_mapping = None
        self.risk_mapping = None
        self.reverse_grade_mapping = None
        self.reverse_risk_mapping = None
        self.load_models()
    
    def load_models(self):
        """Load trained models from disk"""
        try:
            # Try to load balanced models first, then fallback to original
            model_paths = [
                'src/ml/burnout_model_balanced.pkl',
                'src/ml/burnout_model.pkl'
            ]
            
            for path in model_paths:
                if os.path.exists(path):
                    self.burnout_model = joblib.load(path)
                    print(f"? Burnout model loaded from {path}")
                    break
            
            perf_paths = [
                'src/ml/performance_model_balanced.pkl',
                'src/ml/performance_model.pkl'
            ]
            
            for path in perf_paths:
                if os.path.exists(path):
                    self.performance_model = joblib.load(path)
                    print(f"? Performance model loaded from {path}")
                    break
            
            # Load feature names
            features_path = 'src/ml/burnout_features.json'
            if os.path.exists(features_path):
                with open(features_path, 'r') as f:
                    self.burnout_features = json.load(f)
            
            # Load mappings
            risk_path = 'src/ml/risk_mapping.json'
            if os.path.exists(risk_path):
                with open(risk_path, 'r') as f:
                    self.risk_mapping = json.load(f)
                    self.reverse_risk_mapping = {v: k for k, v in self.risk_mapping.items()}
            
            grade_path = 'src/ml/grade_mapping.json'
            if os.path.exists(grade_path):
                with open(grade_path, 'r') as f:
                    self.grade_mapping = json.load(f)
                    self.reverse_grade_mapping = {v: k for k, v in self.grade_mapping.items()}
            
            self.models_loaded = True
            
        except Exception as e:
            print(f"?? Error loading models: {e}")
            self.models_loaded = False
    
    def predict_burnout(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """
        Predict burnout risk from user features
        Returns: (risk_level, confidence)
        """
        if not self.models_loaded or not self.burnout_model:
            return self._heuristic_burnout(features), 0.5
        
        try:
            # Prepare feature vector
            if not self.burnout_features:
                return self._heuristic_burnout(features), 0.5
            
            feature_vector = []
            for f in self.burnout_features:
                feature_vector.append(features.get(f, 0))
            
            # Predict
            X = pd.DataFrame([feature_vector], columns=self.burnout_features)
            
            # Get probabilities
            proba = self.burnout_model.predict_proba(X)[0]
            
            # Get prediction and confidence
            pred_class = np.argmax(proba)
            confidence = proba[pred_class]
            
            # Map to labels
            if self.reverse_risk_mapping:
                risk_level = self.reverse_risk_mapping.get(pred_class, 'low')
            else:
                risk_map = {0: 'low', 1: 'medium', 2: 'high'}
                risk_level = risk_map.get(pred_class, 'low')
            
            return risk_level, float(confidence)
            
        except Exception as e:
            print(f"?? Burnout prediction error: {e}")
            return self._heuristic_burnout(features), 0.3
    
    def predict_performance(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """
        Predict performance grade
        Returns: (grade, confidence)
        """
        if not self.models_loaded or not self.performance_model:
            return self._heuristic_performance(features), 0.5
        
        try:
            # Prepare features
            feature_cols = [
                'avg_load', 'max_load', 'load_variance',
                'duration_minutes', 'late_night', 'has_quiz',
                'message_count', 'whiteboard_actions'
            ]
            
            feature_vector = []
            for f in feature_cols:
                feature_vector.append(features.get(f, 0))
            
            # Predict
            X = pd.DataFrame([feature_vector], columns=feature_cols)
            proba = self.performance_model.predict_proba(X)[0]
            pred_class = np.argmax(proba)
            confidence = proba[pred_class]
            
            # Map to grade
            if self.reverse_grade_mapping:
                grade = self.reverse_grade_mapping.get(pred_class, 'B')
            else:
                grade_map = {0: 'D', 1: 'C', 2: 'B', 3: 'A'}
                grade = grade_map.get(pred_class, 'B')
            
            return grade, float(confidence)
            
        except Exception as e:
            print(f"?? Performance prediction error: {e}")
            return self._heuristic_performance(features), 0.3
    
    def _heuristic_burnout(self, features: Dict[str, Any]) -> str:
        """Fallback heuristic when model not available"""
        risk_score = 0
        
        if features.get('late_night', 0) > 2:
            risk_score += 30
        if features.get('duration_minutes', 0) > 180:
            risk_score += 20
        if features.get('avg_load', 0) > 0.7:
            risk_score += 25
        if features.get('load_variance', 0) > 0.1:
            risk_score += 15
        
        if risk_score > 60:
            return 'high'
        elif risk_score > 30:
            return 'medium'
        else:
            return 'low'
    
    def _heuristic_performance(self, features: Dict[str, Any]) -> str:
        """Fallback heuristic for performance"""
        score = 50
        
        if features.get('has_quiz', 0) > 0:
            score += features.get('quiz_score', 50) * 0.3
        
        if features.get('load_variance', 0) < 0.05:
            score += 15
            
        if score >= 80:
            return 'A'
        elif score >= 65:
            return 'B'
        elif score >= 50:
            return 'C'
        else:
            return 'D'

# Singleton instance
ml_service = MLService()
