import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
import joblib

class EligibilityClassifier:
    def __init__(self):
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        self.label_encoders = {}
    
# In eligibility_classifier.py, update the preprocess_data method:

    def preprocess_data(self, X):
        """Preprocess the input data"""
        X_processed = X.copy()
        
        # Encode categorical variables
        categorical_cols = ['employment_status', 'housing_type', 'marital_status', 'nationality']
        for col in categorical_cols:
            if col in X_processed.columns:
                if col not in self.label_encoders:
                    # Create a label encoder that includes "Unknown" as a category
                    self.label_encoders[col] = LabelEncoder()
                    # Get unique values from training data plus "Unknown"
                    unique_vals = X_processed[col].unique().tolist()
                    if "Unknown" not in unique_vals:
                        unique_vals.append("Unknown")
                    self.label_encoders[col].fit(unique_vals)
                
                # Handle unseen categories by mapping them to "Unknown"
                unseen_mask = ~X_processed[col].isin(self.label_encoders[col].classes_)
                if unseen_mask.any():
                    X_processed.loc[unseen_mask, col] = "Unknown"
                
                X_processed[col] = self.label_encoders[col].transform(X_processed[col])
        
        return X_processed
        
    def fit(self, X, y):
        """Train the model"""
        X_processed = self.preprocess_data(X)
        self.model.fit(X_processed, y)
        return self
    
    def predict(self, X, threshold=0.5):
        """Predict 0/1 eligibility by thresholding the positive class probability."""
        proba = self.predict_proba(X)
        # For binary classifiers, the positive class is typically column 1
        pos_idx = 1 if proba.shape[1] > 1 else 0
        return (proba[:, pos_idx] >= threshold).astype(int)

    
    def predict_proba(self, X):
        """Predict probability of eligibility"""
        X_processed = self.preprocess_data(X)
        return self.model.predict_proba(X_processed)
    
    def save(self, path):
        """Save the model to disk"""
        joblib.dump({
            'model': self.model,
            'label_encoders': self.label_encoders
        }, path)
    
    @classmethod
    def load(cls, path):
        """Load a saved model"""
        data = joblib.load(path)
        classifier = cls()
        classifier.model = data['model']
        classifier.label_encoders = data['label_encoders']
        return classifier