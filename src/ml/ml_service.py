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

            # Only report models as loaded if they can actually run a prediction
            # with the installed numpy/scikit-learn. A pickle produced by a
            # different library version often imports fine but raises on predict;
            # in that case we must fall back to heuristics honestly.
            self.models_loaded = self._self_test()

        except Exception as e:
            print(f"[WARN] Error loading ML models, falling back to heuristics: {e}")
            self.models_loaded = False

    def _self_test(self) -> bool:
        """Run a throwaway prediction against each model to verify compatibility."""
        sample = {
            "start_hour": 14, "duration_minutes": 90, "late_night": 0,
            "avg_load": 0.5, "max_load": 0.7, "load_variance": 0.02,
            "has_quiz": 1, "message_count": 5, "whiteboard_actions": 3,
            "quiz_score": 60,
        }
        ok = True
        if self.burnout_model is not None:
            try:
                self._raw_predict_burnout(sample)
            except Exception as e:
                print(f"[WARN] burnout model incompatible with installed libs: {e}")
                self.burnout_model = None
                ok = False
        if self.performance_model is not None:
            try:
                self._raw_predict_performance(sample)
            except Exception as e:
                print(f"[WARN] performance model incompatible with installed libs: {e}")
                self.performance_model = None
                ok = False
        return ok
    
    _PERF_FEATURE_COLS = [
        'avg_load', 'max_load', 'load_variance',
        'duration_minutes', 'late_night', 'has_quiz',
        'message_count', 'whiteboard_actions',
    ]

    def _raw_predict_burnout(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """Run the burnout model. Raises if the model/libs are incompatible."""
        cols = self.burnout_features or [
            'start_hour', 'duration_minutes', 'late_night', 'avg_load', 'max_load',
            'load_variance', 'has_quiz', 'message_count', 'whiteboard_actions',
        ]
        X = pd.DataFrame([[features.get(f, 0) for f in cols]], columns=cols)
        proba = self.burnout_model.predict_proba(X)[0]
        pred_class = int(np.argmax(proba))
        confidence = float(proba[pred_class])
        if self.reverse_risk_mapping:
            risk_level = self.reverse_risk_mapping.get(pred_class, 'low')
        else:
            risk_level = {0: 'low', 1: 'medium', 2: 'high'}.get(pred_class, 'low')
        return risk_level, confidence

    def _raw_predict_performance(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """Run the performance model. Raises if the model/libs are incompatible."""
        cols = self._PERF_FEATURE_COLS
        X = pd.DataFrame([[features.get(f, 0) for f in cols]], columns=cols)
        proba = self.performance_model.predict_proba(X)[0]
        pred_class = int(np.argmax(proba))
        confidence = float(proba[pred_class])
        if self.reverse_grade_mapping:
            grade = self.reverse_grade_mapping.get(pred_class, 'B')
        else:
            grade = {0: 'D', 1: 'C', 2: 'B', 3: 'A'}.get(pred_class, 'B')
        return grade, confidence

    def predict_burnout(self, features: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Predict burnout risk from user features.
        Returns: (risk_level, confidence, source) where source is
        "ml_model" or "heuristic".
        """
        if self.models_loaded and self.burnout_model is not None:
            try:
                risk_level, confidence = self._raw_predict_burnout(features)
                return risk_level, confidence, "ml_model"
            except Exception as e:
                print(f"[WARN] Burnout prediction failed, using heuristic: {e}")
        return self._heuristic_burnout(features), 0.5, "heuristic"

    def predict_performance(self, features: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Predict performance grade.
        Returns: (grade, confidence, source) where source is
        "ml_model" or "heuristic".
        """
        if self.models_loaded and self.performance_model is not None:
            try:
                grade, confidence = self._raw_predict_performance(features)
                return grade, confidence, "ml_model"
            except Exception as e:
                print(f"[WARN] Performance prediction failed, using heuristic: {e}")
        return self._heuristic_performance(features), 0.5, "heuristic"

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
