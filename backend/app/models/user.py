from datetime import datetime
from app import db
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='nurse')  # admin, doctor, nurse, records_officer
    department = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    encounters = db.relationship('Encounter', backref='provider', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def has_permission(self, permission):
        role_permissions = {
            'admin': [
                'all', 'view_patient', 'register_patient', 'edit_patient', 'delete_patient',
                'view_all_patients', 'view_assigned_patients',
                'create_encounter', 'edit_encounter', 'view_encounter',
                'view_all_records', 'view_assigned_records',
                'view_vitals', 'record_vitals',
                'view_diagnoses', 'write_diagnoses',
                'view_prescriptions', 'write_prescriptions',
                'ai_features', 'ai_alerts', 'ai_risk_assessment', 'ai_diagnosis_suggestions',
                'export_fhir', 'export_reports',
                'view_audit_logs', 'manage_users',
                'view_counters', 'view_ai_dashboard'
            ],
            'doctor': [
                'view_patient', 'register_patient', 'edit_patient',
                'view_all_patients', 'view_assigned_patients',
                'create_encounter', 'edit_encounter', 'view_encounter',
                'view_all_records', 'view_assigned_records',
                'view_vitals', 'record_vitals',
                'view_diagnoses', 'write_diagnoses',
                'view_prescriptions', 'write_prescriptions',
                'ai_features', 'ai_alerts', 'ai_risk_assessment', 'ai_diagnosis_suggestions',
                'export_fhir', 'export_reports',
                'view_audit_logs'
            ],
            'nurse': [
                'view_patient', 'register_patient', 'edit_patient',
                'view_assigned_patients',
                'create_encounter', 'view_encounter',
                'view_assigned_records',
                'view_vitals', 'record_vitals',
                'view_diagnoses',
                'view_prescriptions',
                'ai_alerts', 'send_appointment_email'
            ],
            'records_officer': [
                'view_patient', 'register_patient',
                'view_all_patients', 'view_assigned_patients',
                'view_encounter', 'view_all_records',
                'view_vitals', 'view_diagnoses', 'view_prescriptions',
                'export_fhir', 'export_reports',
                'view_counters', 'view_ai_dashboard'
            ]
        }
        permissions = role_permissions.get(self.role, [])
        return 'all' in permissions or permission in permissions
    
    def can_access_problems_diagnoses(self):
        """Check if user can access problems and diagnoses - not allowed for nurse/records_officer roles"""
        return self.role in ['admin', 'doctor']
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'role': self.role,
            'department': self.department,
            'phone': self.phone,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
