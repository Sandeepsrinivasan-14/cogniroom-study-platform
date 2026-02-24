"""
Burnout Prediction Model with Balanced Data
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import json

def train_burnout_model():
    """Train burnout prediction model on balanced data"""
    
    # Load balanced data
    try:
        sessions = pd.read_csv('src/ml/sessions_balanced.csv')
    except FileNotFoundError:
        print("? Balanced data not found. Run generate_balanced_data.py first")
        return
    
    print(f"?? Loaded {len(sessions)} sessions")
    print(f"Class distribution:\n{sessions['burnout_risk'].value_counts()}")
    
    # Prepare features
    feature_columns = [
        'start_hour', 'duration_minutes', 'late_night',
        'avg_load', 'max_load', 'load_variance',
        'has_quiz', 'message_count', 'whiteboard_actions'
    ]
    
    # Handle missing values
    sessions['quiz_score'] = sessions['quiz_score'].fillna(0)
    
    X = sessions[feature_columns]
    
    # Encode target
    risk_mapping = {'low': 0, 'medium': 1, 'high': 2}
    y = sessions['burnout_risk'].map(risk_mapping)
    
    # Check unique classes
    unique_classes = sorted(y.unique())
    print(f"Unique classes in training data: {unique_classes}")
    
    # Map class names for report
    target_names = ['low', 'medium', 'high']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        random_state=42,
        class_weight='balanced',
        min_samples_split=5
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    
    # Get unique classes in test set
    unique_test_classes = sorted(y_test.unique())
    print(f"\n?? Model Performance (classes in test: {unique_test_classes}):")
    
    # Use only the classes that appear in the test set
    present_labels = [target_names[i] for i in unique_test_classes]
    print(classification_report(y_test, y_pred,
          labels=unique_test_classes,
          target_names=present_labels,
          zero_division=0))
    
    # Confusion Matrix
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
    joblib.dump(model, 'src/ml/burnout_model_balanced.pkl')
    
    # Save feature names and mapping for later use
    with open('src/ml/burnout_features.json', 'w') as f:
        json.dump(feature_columns, f)
    
    with open('src/ml/risk_mapping.json', 'w') as f:
        json.dump(risk_mapping, f)
    
    print("\n? Model saved to src/ml/burnout_model_balanced.pkl")
    return model

if __name__ == "__main__":
    train_burnout_model()
