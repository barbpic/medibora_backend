from datetime import datetime
from app import db

class VitalSigns(db.Model):
    __tablename__ = 'vital_signs'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vital signs
    temperature = db.Column(db.Float, nullable=True)  # Celsius
    temperature_site = db.Column(db.String(20), nullable=True)  # oral, axillary, rectal, tympanic
    heart_rate = db.Column(db.Integer, nullable=True)  # bpm
    respiratory_rate = db.Column(db.Integer, nullable=True)  # breaths per minute
    blood_pressure_systolic = db.Column(db.Integer, nullable=True)  # mmHg
    blood_pressure_diastolic = db.Column(db.Integer, nullable=True)  # mmHg
    oxygen_saturation = db.Column(db.Float, nullable=True)  # SpO2 %
    weight = db.Column(db.Float, nullable=True)  # kg
    height = db.Column(db.Float, nullable=True)  # cm
    bmi = db.Column(db.Float, nullable=True)  # calculated
    pain_score = db.Column(db.Integer, nullable=True)  # 0-10 scale
    
    # AI-generated alerts
    alert_generated = db.Column(db.Boolean, default=False)
    alert_severity = db.Column(db.String(20), nullable=True)  # low, medium, high, critical
    alert_description = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_bmi(self):
        if self.weight and self.height:
            height_m = self.height / 100
            self.bmi = round(self.weight / (height_m ** 2), 2)
        return self.bmi
    
    def check_critical_values(self):
        alerts = []
        
        if self.temperature:
            if self.temperature > 39.5:
                alerts.append({'severity': 'high', 'message': f'High fever: {self.temperature}°C'})
            elif self.temperature < 35.0:
                alerts.append({'severity': 'critical', 'message': f'Hypothermia: {self.temperature}°C'})
        
        if self.heart_rate:
            if self.heart_rate > 120:
                alerts.append({'severity': 'high', 'message': f'Tachycardia: {self.heart_rate} bpm'})
            elif self.heart_rate < 50:
                alerts.append({'severity': 'medium', 'message': f'Bradycardia: {self.heart_rate} bpm'})
        
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            if self.blood_pressure_systolic > 180 or self.blood_pressure_diastolic > 110:
                alerts.append({'severity': 'critical', 'message': f'Severe hypertension: {self.blood_pressure_systolic}/{self.blood_pressure_diastolic} mmHg'})
            elif self.blood_pressure_systolic < 90 or self.blood_pressure_diastolic < 60:
                alerts.append({'severity': 'high', 'message': f'Hypotension: {self.blood_pressure_systolic}/{self.blood_pressure_diastolic} mmHg'})
        
        if self.oxygen_saturation and self.oxygen_saturation < 90:
            alerts.append({'severity': 'critical', 'message': f'Severe hypoxemia: SpO2 {self.oxygen_saturation}%'})
        
        if self.pain_score and self.pain_score >= 8:
            alerts.append({'severity': 'high', 'message': f'Severe pain: {self.pain_score}/10'})
        
        if alerts:
            self.alert_generated = True
            highest_severity = max(alerts, key=lambda x: {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}.get(x['severity'], 0))
            self.alert_severity = highest_severity['severity']
            self.alert_description = '; '.join([a['message'] for a in alerts])
        
        return alerts
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'encounter_id': self.encounter_id,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'temperature': self.temperature,
            'temperature_site': self.temperature_site,
            'heart_rate': self.heart_rate,
            'respiratory_rate': self.respiratory_rate,
            'blood_pressure': {
                'systolic': self.blood_pressure_systolic,
                'diastolic': self.blood_pressure_diastolic,
                'display': f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}" if self.blood_pressure_systolic and self.blood_pressure_diastolic else None
            },
            'oxygen_saturation': self.oxygen_saturation,
            'weight': self.weight,
            'height': self.height,
            'bmi': self.bmi,
            'pain_score': self.pain_score,
            'alert': {
                'generated': self.alert_generated,
                'severity': self.alert_severity,
                'description': self.alert_description
            } if self.alert_generated else None
        }
