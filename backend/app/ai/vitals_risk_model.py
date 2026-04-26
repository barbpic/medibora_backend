# backend/app/ai/vitals_risk_model.py
import joblib
import numpy as np
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path

class VitalsRiskPredictor:
    """Vitals-based risk prediction using trained ML model or rule-based fallback"""
    
    def __init__(self):
        # Get the absolute path to the AI module directory
        self.ai_dir = Path(__file__).parent
        
        # Load model and artifacts
        model_path = self.ai_dir / 'vitals_risk_model.pkl'
        features_path = self.ai_dir / 'feature_columns.json'
        scaler_path = self.ai_dir / 'feature_scaler.pkl'
        
        # Check if model exists (will be created during training)
        if model_path.exists():
            self.model = joblib.load(model_path)
            with open(features_path, 'r') as f:
                self.feature_columns = json.load(f)
            
            # Load scaler if it exists (for Logistic Regression)
            self.scaler = joblib.load(scaler_path) if scaler_path.exists() else None
            self.is_trained = True
            print(f"✅ Loaded trained model from {model_path}")
        else:
            self.is_trained = False
            print("⚠️ Vitals risk model not trained yet. Using rule-based fallback.")
    
    def extract_features_from_vitals(self, vital_signs_record):
        """Convert vital signs record to feature vector"""
        # Calculate derived features
        pulse_pressure = vital_signs_record.get('systolic_bp', 0) - vital_signs_record.get('diastolic_bp', 0)
        map_value = vital_signs_record.get('diastolic_bp', 0) + (pulse_pressure / 3)
        
        # BMI calculation (if height and weight available)
        bmi = 25.0  # default
        if vital_signs_record.get('weight') and vital_signs_record.get('height'):
            bmi = vital_signs_record['weight'] / (vital_signs_record['height'] ** 2)
        
        features = {
            'Heart Rate': vital_signs_record.get('heart_rate', 75),
            'Respiratory Rate': vital_signs_record.get('respiratory_rate', 16),
            'Body Temperature': vital_signs_record.get('temperature', 36.8),
            'Oxygen Saturation': vital_signs_record.get('oxygen_saturation', 97),
            'Systolic Blood Pressure': vital_signs_record.get('systolic_bp', 120),
            'Diastolic Blood Pressure': vital_signs_record.get('diastolic_bp', 80),
            'Age': vital_signs_record.get('age', 50),
            'Derived_HRV': vital_signs_record.get('heart_rate_variability', 0.1),
            'Derived_Pulse_Pressure': pulse_pressure,
            'Derived_BMI': bmi,
            'Derived_MAP': map_value,
            'Gender_encoded': 1 if vital_signs_record.get('gender') == 'Male' else 0
        }
        
        return features
    
    def _get_abnormal_findings(self, vital_signs):
        """Generate detailed list of abnormal findings from vital signs"""
        findings = []
        
        # Heart Rate analysis
        hr = vital_signs.get('heart_rate', 75)
        if hr > 130:
            findings.append(f"⚠️ Severe tachycardia: {hr} bpm (Normal: 60-100)")
        elif hr > 100:
            findings.append(f"⚠️ Tachycardia: {hr} bpm (Normal: 60-100)")
        elif hr < 50:
            findings.append(f"⚠️ Bradycardia: {hr} bpm (Normal: 60-100)")
        elif hr < 60:
            findings.append(f"⚠️ Mild bradycardia: {hr} bpm (Normal: 60-100)")
        
        # Blood Pressure analysis
        sbp = vital_signs.get('systolic_bp', 120)
        dbp = vital_signs.get('diastolic_bp', 80)
        
        if sbp > 180:
            findings.append(f"⚠️ Severe hypertension: {sbp}/{dbp} mmHg (Target: <140/90)")
        elif sbp > 140:
            findings.append(f"⚠️ Elevated BP: {sbp}/{dbp} mmHg (Target: <140/90)")
        elif sbp < 90:
            findings.append(f"⚠️ Hypotension: {sbp}/{dbp} mmHg (Target: >90/60)")
        elif dbp > 100:
            findings.append(f"⚠️ Elevated diastolic BP: {dbp} mmHg (Target: <90)")
        
        # Oxygen Saturation analysis
        spo2 = vital_signs.get('oxygen_saturation', 98)
        if spo2 < 88:
            findings.append(f"⚠️ Severe hypoxemia: {spo2}% (Target: >94%)")
        elif spo2 < 92:
            findings.append(f"⚠️ Moderate hypoxemia: {spo2}% (Target: >94%)")
        elif spo2 < 95:
            findings.append(f"⚠️ Mild hypoxemia: {spo2}% (Target: >94%)")
        
        # Temperature analysis
        temp = vital_signs.get('temperature', 36.8)
        if temp > 39.5:
            findings.append(f"⚠️ Critical fever: {temp}°C (Normal: 36.5-37.5)")
        elif temp > 38.5:
            findings.append(f"⚠️ High fever: {temp}°C (Normal: 36.5-37.5)")
        elif temp > 38.0:
            findings.append(f"⚠️ Fever: {temp}°C (Normal: 36.5-37.5)")
        elif temp < 35.0:
            findings.append(f"⚠️ Hypothermia: {temp}°C (Normal: 36.5-37.5)")
        
        # Respiratory Rate analysis
        rr = vital_signs.get('respiratory_rate', 16)
        if rr > 28:
            findings.append(f"⚠️ Severe tachypnea: {rr}/min (Normal: 12-20)")
        elif rr > 24:
            findings.append(f"⚠️ Tachypnea: {rr}/min (Normal: 12-20)")
        elif rr > 20:
            findings.append(f"⚠️ Mild tachypnea: {rr}/min (Normal: 12-20)")
        elif rr < 10:
            findings.append(f"⚠️ Bradypnea: {rr}/min (Normal: 12-20)")
        
        # Age-related findings
        age = vital_signs.get('age', 50)
        if age > 75:
            findings.append(f"⚠️ Advanced age: {age} years (Increased risk)")
        elif age > 65:
            findings.append(f"⚠️ Elderly: {age} years (Moderate risk increase)")
        
        # Combined risk patterns
        if sbp < 90 and hr > 100:
            findings.append("⚠️ Shock risk: Hypotension + Tachycardia")
        if spo2 < 92 and rr > 24:
            findings.append("⚠️ Respiratory distress: Hypoxemia + Tachypnea")
        if temp > 39.0 and hr > 100:
            findings.append("⚠️ Sepsis risk: Fever + Tachycardia")
        
        return findings if findings else ["✓ All vital signs within normal range"]
    
    def _get_detailed_recommendation(self, risk_score, findings, vital_signs):
        """Generate detailed clinical recommendations based on findings"""
        recommendations = []
        
        if risk_score >= 0.7:
            recommendations.append("🔴 IMMEDIATE ACTION REQUIRED:")
            recommendations.append("   • Notify attending physician immediately")
            recommendations.append("   • Consider hospital admission")
            recommendations.append("   • Repeat vital signs in 15 minutes")
            
            # Specific recommendations based on findings
            if vital_signs.get('oxygen_saturation', 98) < 92:
                recommendations.append("   • Administer supplemental oxygen")
            if vital_signs.get('systolic_bp', 120) < 90:
                recommendations.append("   • Start IV fluids")
            if vital_signs.get('temperature', 36.8) > 39.0:
                recommendations.append("   • Administer antipyretics")
            if vital_signs.get('heart_rate', 75) > 120:
                recommendations.append("   • Order ECG")
                
        elif risk_score >= 0.4:
            recommendations.append("🟡 CLOSE MONITORING REQUIRED:")
            recommendations.append("   • Schedule follow-up within 24 hours")
            recommendations.append("   • Monitor vital signs every 4 hours")
            recommendations.append("   • Review medications")
            
            if vital_signs.get('oxygen_saturation', 98) < 94:
                recommendations.append("   • Consider home oxygen assessment")
            if vital_signs.get('systolic_bp', 120) > 140:
                recommendations.append("   • Review antihypertensive medications")
        else:
            recommendations.append("🟢 ROUTINE CARE:")
            recommendations.append("   • Routine follow-up as scheduled")
            recommendations.append("   • Continue current management")
            recommendations.append("   • Patient education on healthy lifestyle")
        
        return "\n".join(recommendations)
    
    def predict(self, vital_signs_record):
        """
        Predict risk from vital signs
        Returns: dict with risk assessment and detailed findings
        """
        # Always generate abnormal findings (for both ML and fallback)
        findings = self._get_abnormal_findings(vital_signs_record)
        
        if not self.is_trained:
            # Use rule-based assessment
            return self._rule_based_assessment(vital_signs_record, findings)
        
        try:
            # Use ML model
            features = self.extract_features_from_vitals(vital_signs_record)
            
            # Create DataFrame with proper column order
            X = pd.DataFrame([features])[self.feature_columns]
            
            # Scale if scaler exists
            if self.scaler:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X.values
            
            # Predict probability
            risk_probability = self.model.predict_proba(X_scaled)[0][1]
            
            # Clinical interpretation with detailed breakdown
            if risk_probability >= 0.7:
                risk_level = "HIGH RISK"
                recommendation = self._get_detailed_recommendation(risk_probability, findings, vital_signs_record)
                color_code = "danger"
                action_required = True
            elif risk_probability >= 0.4:
                risk_level = "MODERATE RISK"
                recommendation = self._get_detailed_recommendation(risk_probability, findings, vital_signs_record)
                color_code = "warning"
                action_required = False
            else:
                risk_level = "LOW RISK"
                recommendation = self._get_detailed_recommendation(risk_probability, findings, vital_signs_record)
                color_code = "success"
                action_required = False
            
            # Calculate NEWS2 score (clinical early warning score)
            news2_score = self._calculate_news2_score(vital_signs_record)
            
            return {
                'risk_score': float(risk_probability),
                'risk_percentage': f"{risk_probability * 100:.1f}%",
                'risk_level': risk_level,
                'recommendation': recommendation,
                'color_code': color_code,
                'action_required': action_required,
                'model_used': 'trained_ml_model',
                'abnormal_findings': findings,
                'news2_score': news2_score,
                'news2_interpretation': self._interpret_news2(news2_score),
                'disclaimer': '⚠️ AI-assisted prediction - not a substitute for clinical judgment. Always verify with clinical assessment.',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"ML prediction failed: {e}, falling back to rule-based")
            return self._rule_based_assessment(vital_signs_record, findings)
    
    def _calculate_news2_score(self, vital_signs):
        """Calculate NEWS2 (National Early Warning Score)"""
        score = 0
        
        # Respiratory Rate
        rr = vital_signs.get('respiratory_rate', 16)
        if rr <= 8: score += 3
        elif rr >= 25: score += 3
        elif rr >= 21: score += 2
        elif rr <= 11: score += 1
        
        # Oxygen Saturation
        spo2 = vital_signs.get('oxygen_saturation', 98)
        if spo2 <= 91: score += 3
        elif spo2 <= 93: score += 2
        elif spo2 <= 95: score += 1
        
        # Temperature
        temp = vital_signs.get('temperature', 36.8)
        if temp <= 35.0: score += 3
        elif temp >= 39.1: score += 2
        elif temp >= 38.1: score += 1
        
        # Systolic BP
        sbp = vital_signs.get('systolic_bp', 120)
        if sbp <= 90: score += 3
        elif sbp <= 100: score += 2
        elif sbp >= 220: score += 2
        
        # Heart Rate
        hr = vital_signs.get('heart_rate', 75)
        if hr <= 40: score += 3
        elif hr >= 131: score += 3
        elif hr >= 111: score += 2
        elif hr >= 91: score += 1
        elif hr <= 50: score += 1
        
        return score
    
    def _interpret_news2(self, score):
        """Interpret NEWS2 score"""
        if score >= 7:
            return "CRITICAL - Immediate transfer to higher level care"
        elif score >= 5:
            return "HIGH - Urgent review by clinician"
        elif score >= 3:
            return "MODERATE - Clinical review required"
        elif score >= 1:
            return "LOW - Monitor regularly"
        else:
            return "NORMAL - Routine care"
    
    def _rule_based_assessment(self, vital_signs_record, findings):
        """Rule-based assessment with full details"""
        risk_score = 0
        
        # Calculate risk score based on abnormalities
        hr = vital_signs_record.get('heart_rate', 75)
        if hr > 130: risk_score += 0.4
        elif hr > 110: risk_score += 0.2
        elif hr < 50: risk_score += 0.2
        
        sbp = vital_signs_record.get('systolic_bp', 120)
        if sbp > 180: risk_score += 0.4
        elif sbp < 90: risk_score += 0.3
        elif sbp > 140: risk_score += 0.15
        
        spo2 = vital_signs_record.get('oxygen_saturation', 98)
        if spo2 < 90: risk_score += 0.4
        elif spo2 < 94: risk_score += 0.2
        
        temp = vital_signs_record.get('temperature', 36.8)
        if temp > 39.0: risk_score += 0.3
        elif temp > 38.0: risk_score += 0.15
        elif temp < 35.0: risk_score += 0.3
        
        rr = vital_signs_record.get('respiratory_rate', 16)
        if rr > 24: risk_score += 0.3
        elif rr > 20: risk_score += 0.15
        
        age = vital_signs_record.get('age', 50)
        if age > 75: risk_score += 0.15
        elif age > 65: risk_score += 0.1
        
        # Cap risk score
        risk_score = min(risk_score, 0.95)
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "HIGH RISK"
            recommendation = self._get_detailed_recommendation(risk_score, findings, vital_signs_record)
            color_code = "danger"
            action_required = True
        elif risk_score >= 0.4:
            risk_level = "MODERATE RISK"
            recommendation = self._get_detailed_recommendation(risk_score, findings, vital_signs_record)
            color_code = "warning"
            action_required = False
        else:
            risk_level = "LOW RISK"
            recommendation = self._get_detailed_recommendation(risk_score, findings, vital_signs_record)
            color_code = "success"
            action_required = False
        
        # Calculate NEWS2 score
        news2_score = self._calculate_news2_score(vital_signs_record)
        
        return {
            'risk_score': risk_score,
            'risk_percentage': f"{risk_score * 100:.1f}%",
            'risk_level': risk_level,
            'recommendation': recommendation,
            'color_code': color_code,
            'action_required': action_required,
            'model_used': 'rule_based_fallback',
            'abnormal_findings': findings,
            'news2_score': news2_score,
            'news2_interpretation': self._interpret_news2(news2_score),
            'disclaimer': '⚠️ AI-assisted prediction - not a substitute for clinical judgment. Always verify with clinical assessment.',
            'timestamp': datetime.now().isoformat()
        }

# Singleton instance
vitals_risk_predictor = VitalsRiskPredictor()