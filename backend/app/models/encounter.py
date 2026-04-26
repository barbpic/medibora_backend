from datetime import datetime
from app import db

class Encounter(db.Model):
    __tablename__ = 'encounters'
    
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    visit_type = db.Column(db.String(30), nullable=False)  # outpatient, inpatient, emergency, follow_up
    chief_complaint = db.Column(db.Text, nullable=True)
    history_of_present_illness = db.Column(db.Text, nullable=True)
    physical_examination = db.Column(db.Text, nullable=True)
    assessment = db.Column(db.Text, nullable=True)
    diagnosis_primary = db.Column(db.String(255), nullable=True)
    diagnosis_secondary = db.Column(db.Text, nullable=True)
    treatment_plan = db.Column(db.Text, nullable=True)
    medications_prescribed = db.Column(db.Text, nullable=True)
    procedures = db.Column(db.Text, nullable=True)
    lab_tests_ordered = db.Column(db.Text, nullable=True)
    lab_results = db.Column(db.Text, nullable=True)
    follow_up_instructions = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vital_signs = db.relationship('VitalSigns', backref='encounter', lazy=True, cascade='all, delete-orphan', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'patient_id': self.patient_id,
            'provider_id': self.provider_id,
            'provider_name': self.provider.full_name if self.provider else None,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'visit_type': self.visit_type,
            'chief_complaint': self.chief_complaint,
            'history_of_present_illness': self.history_of_present_illness,
            'physical_examination': self.physical_examination,
            'assessment': self.assessment,
            'diagnosis_primary': self.diagnosis_primary,
            'diagnosis_secondary': self.diagnosis_secondary,
            'treatment_plan': self.treatment_plan,
            'medications_prescribed': self.medications_prescribed,
            'procedures': self.procedures,
            'lab_tests_ordered': self.lab_tests_ordered,
            'lab_results': self.lab_results,
            'follow_up_instructions': self.follow_up_instructions,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'vital_signs': self.vital_signs.to_dict() if self.vital_signs else None
        }
    
    def to_summary_dict(self):
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'visit_type': self.visit_type,
            'chief_complaint': self.chief_complaint[:100] + '...' if self.chief_complaint and len(self.chief_complaint) > 100 else self.chief_complaint,
            'diagnosis_primary': self.diagnosis_primary,
            'provider_name': self.provider.full_name if self.provider else None,
            'status': self.status
        }
