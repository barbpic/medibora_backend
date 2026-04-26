from datetime import datetime
from app import db

class Allergy(db.Model):
    __tablename__ = 'allergies'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    allergen = db.Column(db.String(100), nullable=False)
    reaction = db.Column(db.String(255), nullable=True)
    severity = db.Column(db.String(20), nullable=True)  # Mild, Moderate, Severe
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'allergen': self.allergen,
            'reaction': self.reaction,
            'severity': self.severity,
            'recorded_by': self.recorded_by,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'is_active': self.is_active
        }


class Problem(db.Model):
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icd10_code = db.Column(db.String(10), nullable=True)
    onset_date = db.Column(db.Date, nullable=True)
    problem_type = db.Column(db.String(30), nullable=True)  # Primary, Secondary, Working, Differential, Admitting
    status = db.Column(db.String(20), default='Active')  # Active, Chronic, Resolved
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'description': self.description,
            'icd10_code': self.icd10_code,
            'onset_date': self.onset_date.isoformat() if self.onset_date else None,
            'problem_type': self.problem_type,
            'status': self.status,
            'recorded_by': self.recorded_by,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'is_active': self.is_active
        }


class Medication(db.Model):
    __tablename__ = 'medications'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medication_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(50), nullable=True)
    frequency = db.Column(db.String(50), nullable=True)
    route = db.Column(db.String(30), nullable=True)  # Oral, IV, IM, etc.
    special_instructions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Active')  # Active, Chronic, Discontinued
    prescribed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    prescribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'medication_name': self.medication_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'route': self.route,
            'special_instructions': self.special_instructions,
            'status': self.status,
            'prescribed_by': self.prescribed_by,
            'prescribed_at': self.prescribed_at.isoformat() if self.prescribed_at else None,
            'is_active': self.is_active
        }


class PatientHistory(db.Model):
    __tablename__ = 'patient_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    history_type = db.Column(db.String(30), nullable=False)  # Medical, Surgical, Family, Social, etc.
    description = db.Column(db.Text, nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'history_type': self.history_type,
            'description': self.description,
            'recorded_by': self.recorded_by,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'is_active': self.is_active
        }


class Immunization(db.Model):
    __tablename__ = 'immunizations'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    vaccine_name = db.Column(db.String(200), nullable=False)
    dose = db.Column(db.String(50), nullable=True)
    date_given = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=True)
    lot_number = db.Column(db.String(50), nullable=True)
    administration_site = db.Column(db.String(50), nullable=True)
    administered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'vaccine_name': self.vaccine_name,
            'dose': self.dose,
            'date_given': self.date_given.isoformat() if self.date_given else None,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'lot_number': self.lot_number,
            'administration_site': self.administration_site,
            'administered_by': self.administered_by,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'is_active': self.is_active
        }


class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_type = db.Column(db.String(50), nullable=True)  # Follow-up, Consultation, etc.
    provider = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Scheduled')  # Scheduled, Completed, Cancelled
    scheduled_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'appointment_type': self.appointment_type,
            'provider': self.provider,
            'notes': self.notes,
            'status': self.status,
            'scheduled_by': self.scheduled_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class LabResult(db.Model):
    __tablename__ = 'lab_results'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    test_name = db.Column(db.String(200), nullable=False)
    test_type = db.Column(db.String(50), nullable=True)  # Laboratory, Radiology, etc.
    clinical_indication = db.Column(db.Text, nullable=True)
    urgency = db.Column(db.String(20), default='Routine')  # Routine, Urgent, Stat
    result = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending')  # Pending, Final, Critical
    ordered_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    result_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'test_name': self.test_name,
            'test_type': self.test_type,
            'clinical_indication': self.clinical_indication,
            'urgency': self.urgency,
            'result': self.result,
            'status': self.status,
            'ordered_by': self.ordered_by,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'result_date': self.result_date.isoformat() if self.result_date else None,
            'is_active': self.is_active
        }


class Admission(db.Model):
    __tablename__ = 'admissions'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    admission_date = db.Column(db.DateTime, default=datetime.utcnow)
    discharge_date = db.Column(db.DateTime, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    primary_diagnosis = db.Column(db.String(255), nullable=True)
    admission_type = db.Column(db.String(30), nullable=True)  # Emergency, Elective, Transfer
    room_number = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default='Active')  # Active, Discharged
    admitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'admission_date': self.admission_date.isoformat() if self.admission_date else None,
            'discharge_date': self.discharge_date.isoformat() if self.discharge_date else None,
            'department': self.department,
            'primary_diagnosis': self.primary_diagnosis,
            'admission_type': self.admission_type,
            'room_number': self.room_number,
            'status': self.status,
            'admitted_by': self.admitted_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class SBAR(db.Model):
    __tablename__ = 'sbars'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    situation = db.Column(db.Text, nullable=False)
    background = db.Column(db.Text, nullable=True)
    assessment = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, submitted
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'situation': self.situation,
            'background': self.background,
            'assessment': self.assessment,
            'recommendation': self.recommendation,
            'status': self.status,
            'recorded_by': self.recorded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # Lab, Imaging, Consent, Referral, etc.
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'title': self.title,
            'document_type': self.document_type,
            'description': self.description,
            'file_path': self.file_path,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_active': self.is_active
        }


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    task_type = db.Column(db.String(30), default='general')  # lab, referral, followup, general
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_active': self.is_active
        }


class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # Summary, Lab, Admittance, Discharge
    title = db.Column(db.String(200), nullable=True)
    date_from = db.Column(db.Date, nullable=True)
    date_to = db.Column(db.Date, nullable=True)
    content = db.Column(db.Text, nullable=True)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'report_type': self.report_type,
            'title': self.title,
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'date_to': self.date_to.isoformat() if self.date_to else None,
            'content': self.content,
            'generated_by': self.generated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
