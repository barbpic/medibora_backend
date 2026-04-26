"""
Machine Learning-Based Risk Classification for MEDIBORA
Implements Logistic Regression for predicting binary outcomes
such as missed follow-up risk
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import scikit-learn, if not available use simple implementation
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Using simplified implementation.")

@dataclass
class RiskPrediction:
    """Represents a risk prediction result"""
    patient_id: int
    risk_score: float
    risk_level: str
    probability: float
    features_used: Dict[str, Any]
    recommendation: str
    timestamp: datetime

class RiskClassifier:
    """
    Logistic Regression-based Risk Classifier
    Predicts binary outcomes such as missed follow-up risk
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.path.join(
            os.path.dirname(__file__), 'models', 'risk_classifier.pkl'
        )
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.feature_names = [
            'age',
            'days_since_last_visit',
            'has_chronic_condition',
            'visit_count_last_year',
            'has_missed_appointments',
            'medication_count'
        ]
        
        # Try to load existing model
        self._load_model()
        
        # If no model exists, train with sample data
        if not self.is_trained:
            self._train_sample_model()
    
    def _load_model(self) -> bool:
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    saved_data = pickle.load(f)
                    self.model = saved_data.get('model')
                    self.scaler = saved_data.get('scaler')
                    self.is_trained = True
                    return True
        except Exception as e:
            print(f"Could not load model: {e}")
        return False
    
    def _save_model(self) -> bool:
        """Save trained model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler
                }, f)
            return True
        except Exception as e:
            print(f"Could not save model: {e}")
            return False
    
    def _train_sample_model(self) -> None:
        """Train model with sample data for demonstration"""
        if not SKLEARN_AVAILABLE:
            # Simple rule-based fallback
            self.is_trained = True
            return
        
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        # Features: [age, days_since_last_visit, has_chronic_condition, 
        #           visit_count_last_year, has_missed_appointments, medication_count]
        X = np.random.rand(n_samples, 6)
        
        # Adjust feature distributions to be more realistic
        X[:, 0] = X[:, 0] * 80 + 18  # Age: 18-98
        X[:, 1] = X[:, 1] * 365  # Days since last visit: 0-365
        X[:, 2] = (X[:, 2] > 0.7).astype(float)  # 30% have chronic conditions
        X[:, 3] = (X[:, 3] * 10).astype(int)  # 0-10 visits
        X[:, 4] = (X[:, 4] > 0.8).astype(float)  # 20% missed appointments
        X[:, 5] = (X[:, 5] * 5).astype(int)  # 0-5 medications
        
        # Generate target: higher risk for older, longer gaps, chronic conditions, missed appointments
        risk_score = (
            (X[:, 0] > 60) * 0.3 +  # Age factor
            (X[:, 1] > 180) * 0.4 +  # Gap factor
            X[:, 2] * 0.2 +  # Chronic condition factor
            (X[:, 3] < 2) * 0.2 +  # Low visit count factor
            X[:, 4] * 0.3 +  # Missed appointment factor
            (X[:, 5] > 2) * 0.1  # Multiple medications factor
        )
        y = (risk_score > 0.5).astype(int)
        
        # Train model
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        self.model = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        )
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Save model
        self._save_model()
        
        # Calculate metrics
        y_pred = self.model.predict(X_scaled)
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, zero_division=0)
        recall = recall_score(y, y_pred, zero_division=0)
        f1 = f1_score(y, y_pred, zero_division=0)
        
        print(f"Model trained - Accuracy: {accuracy:.3f}, Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
    
    def extract_features(self, patient_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from patient data"""
        features = []
        
        # Age
        features.append(patient_data.get('age', 30))
        
        # Days since last visit
        last_visit = patient_data.get('last_visit')
        if last_visit:
            if isinstance(last_visit, str):
                last_visit = datetime.fromisoformat(last_visit.replace('Z', '+00:00'))
            days_since = (datetime.utcnow() - last_visit).days
        else:
            days_since = 365  # Default to 1 year if no visit
        features.append(days_since)
        
        # Has chronic condition
        has_chronic = 1 if patient_data.get('chronic_conditions') else 0
        features.append(has_chronic)
        
        # Visit count in last year
        features.append(patient_data.get('visit_count_last_year', 0))
        
        # Has missed appointments
        features.append(1 if patient_data.get('missed_appointments', 0) > 0 else 0)
        
        # Medication count
        medications = patient_data.get('current_medications', '')
        med_count = len([m for m in medications.split(',') if m.strip()]) if medications else 0
        features.append(med_count)
        
        return np.array(features).reshape(1, -1)
    
    def predict_risk(self, patient_data: Dict[str, Any]) -> RiskPrediction:
        """
        Predict risk for a patient
        Returns RiskPrediction with score, level, and recommendation
        """
        features = self.extract_features(patient_data)
        
        if not SKLEARN_AVAILABLE or not self.is_trained:
            # Fallback to rule-based scoring
            return self._rule_based_prediction(patient_data, features[0])
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Get probability
        probability = self.model.predict_proba(features_scaled)[0][1]
        
        # Determine risk level
        if probability >= 0.7:
            risk_level = "HIGH"
            recommendation = "Schedule urgent follow-up within 7 days"
        elif probability >= 0.4:
            risk_level = "MEDIUM"
            recommendation = "Schedule follow-up within 14 days"
        else:
            risk_level = "LOW"
            recommendation = "Routine follow-up as scheduled"
        
        return RiskPrediction(
            patient_id=patient_data.get('id', 0),
            risk_score=round(probability * 100, 1),
            risk_level=risk_level,
            probability=round(probability, 3),
            features_used=dict(zip(self.feature_names, features[0].tolist())),
            recommendation=recommendation,
            timestamp=datetime.utcnow()
        )
    
    def _rule_based_prediction(self, patient_data: Dict[str, Any], features: np.ndarray) -> RiskPrediction:
        """Fallback rule-based prediction when sklearn is not available"""
        age, days_since, has_chronic, visit_count, missed_appts, med_count = features
        
        # Simple scoring
        score = 0
        if age > 60: score += 0.25
        if days_since > 180: score += 0.30
        if has_chronic: score += 0.20
        if visit_count < 2: score += 0.15
        if missed_appts: score += 0.25
        if med_count > 2: score += 0.10
        
        if score >= 0.7:
            risk_level = "HIGH"
            recommendation = "Schedule urgent follow-up within 7 days"
        elif score >= 0.4:
            risk_level = "MEDIUM"
            recommendation = "Schedule follow-up within 14 days"
        else:
            risk_level = "LOW"
            recommendation = "Routine follow-up as scheduled"
        
        return RiskPrediction(
            patient_id=patient_data.get('id', 0),
            risk_score=round(score * 100, 1),
            risk_level=risk_level,
            probability=round(score, 3),
            features_used=dict(zip(self.feature_names, features.tolist())),
            recommendation=recommendation,
            timestamp=datetime.utcnow()
        )
    
    def batch_predict(self, patients_data: List[Dict[str, Any]]) -> List[RiskPrediction]:
        """Predict risk for multiple patients"""
        return [self.predict_risk(p) for p in patients_data]
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if not SKLEARN_AVAILABLE or not self.is_trained or self.model is None:
            return {name: 0.0 for name in self.feature_names}
        
        coefficients = self.model.coef_[0]
        importance = dict(zip(self.feature_names, coefficients.tolist()))
        return importance

# Singleton instance
_classifier = None

def get_risk_classifier() -> RiskClassifier:
    """Get or create the risk classifier singleton"""
    global _classifier
    if _classifier is None:
        _classifier = RiskClassifier()
    return _classifier
