"""
Performance Prediction Model with Balanced Data
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import json

def train_performance_model():
    """Train performance prediction model on balanced data"""
    
    # Load balanced data
    try:
        sessions = pd.read_csv('src/ml/sessions_balanced.csv')
    except FileNotFoundError:
        print("? Balanced data not found")
        return
    
    # Aggregate by user to get user-level features
    user_features = sessions.groupby('user_id').agg({
        'avg_load': 'mean',
        'max_load': 'max',
        'load_variance': 'mean',
        'duration_minutes': 'sum',
        'late_night': 'sum',
        'has_quiz': 'sum',
        'quiz_score': 'mean',
        'message_count': 'sum',
        'whiteboard_actions': 'sum',
        'performance': lambda x: x.mode()[0] if not x.mode().empty else 'B'  # Most common performance
    }).reset_index()
    
    print(f"?? Aggregated data for {len(user_features)} users")
    print(f"Performance distribution:\n{user_features['performance'].value_counts()}")
    
    # Prepare features for training
    feature_columns = [
        'avg_load', 'max_load', 'load_variance',
        'duration_minutes', 'late_night', 'has_quiz',
        'message_count', 'whiteboard_actions'
    ]
    
    # Fill missing quiz scores
    user_features['quiz_score'] = user_features['quiz_score'].fillna(50)
    
    X = user_features[feature_columns]
    
    # Encode target - include all grades
    grade_mapping = {'D': 0, 'C': 1, 'B': 2, 'A': 3}
    y = user_features['performance'].map(grade_mapping)
    
    # Check unique classes
    unique_classes = sorted(y.unique())
    print(f"Unique classes in training data: {unique_classes}")
    
    if len(unique_classes) < 2:
        print("? Need at least 2 classes for training")
        return
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train model
    model = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        min_samples_split=5
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n?? Model Accuracy: {accuracy:.2%}")
    
    # Get unique classes in test set
    unique_test_classes = sorted(y_test.unique())
    target_names = ['D', 'C', 'B', 'A']
    present_labels = [target_names[i] for i in unique_test_classes if i < len(target_names)]
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred,
          labels=unique_test_classes,
          target_names=present_labels,
          zero_division=0))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n?? Feature Importance:")
    print(importance)
    
    # Save model
    joblib.dump(model, 'src/ml/performance_model_balanced.pkl')
    
    # Save mapping
    with open('src/ml/grade_mapping.json', 'w') as f:
        json.dump(grade_mapping, f)
    
    print("\n? Model saved to src/ml/performance_model_balanced.pkl")
    return model

if __name__ == "__main__":
    train_performance_model()
