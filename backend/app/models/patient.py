from datetime import datetime
from app import db

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_type = db.Column(db.String(5), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(50), nullable=True)
    county = db.Column(db.String(50), nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_relationship = db.Column(db.String(30), nullable=True)
    insurance_provider = db.Column(db.String(100), nullable=True)
    insurance_number = db.Column(db.String(50), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    chronic_conditions = db.Column(db.Text, nullable=True)
    current_medications = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    registered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    encounters = db.relationship('Encounter', backref='patient', lazy=True, cascade='all, delete-orphan')
    vital_signs = db.relationship('VitalSigns', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def get_age(self):
        today = datetime.today()
        born = self.date_of_birth
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return age
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.get_age(),
            'gender': self.gender,
            'blood_type': self.blood_type,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'city': self.city,
            'county': self.county,
            'emergency_contact': {
                'name': self.emergency_contact_name,
                'phone': self.emergency_contact_phone,
                'relationship': self.emergency_contact_relationship
            },
            'insurance': {
                'provider': self.insurance_provider,
                'number': self.insurance_number
            },
            'allergies': self.allergies,
            'chronic_conditions': self.chronic_conditions,
            'current_medications': self.current_medications,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'encounter_count': len(self.encounters) if self.encounters else 0
        }
    
    def to_summary_dict(self):
        # Get last encounter date
        last_encounter = None
        if self.encounters and len(self.encounters) > 0:
            last_encounter = sorted(self.encounters, key=lambda e: e.visit_date, reverse=True)[0]
        
        # Get most recent vital signs
        latest_vital_signs = None
        if self.vital_signs and len(self.vital_signs) > 0:
            latest_vital_signs = sorted(self.vital_signs, key=lambda v: v.recorded_at, reverse=True)[0]
        
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'age': self.get_age(),
            'gender': self.gender,
            'phone': self.phone,
            'blood_type': self.blood_type,
            'allergies': self.allergies,
            'chronic_conditions': self.chronic_conditions,
            'current_medications': self.current_medications,
            'insurance': {
                'provider': self.insurance_provider,
                'number': self.insurance_number
            },
            'last_visit': last_encounter.visit_date.isoformat() if last_encounter else None,
            'latest_vital_signs': latest_vital_signs.to_dict() if latest_vital_signs else None,
            'vital_signs_count': len(self.vital_signs) if self.vital_signs else 0,
            'encounter_count': len(self.encounters) if self.encounters else 0
        }