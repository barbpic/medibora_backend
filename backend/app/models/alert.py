from datetime import datetime
from app import db


class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_uid = db.Column(db.String(128), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    patient_name = db.Column(db.String(255), nullable=True)
    patient_id_number = db.Column(db.String(128), nullable=True)
    severity = db.Column(db.String(32), nullable=True)
    category = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(64), nullable=True)
    alert_type = db.Column(db.String(64), nullable=True)
    data = db.Column(db.JSON, nullable=True)
    dismissed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.alert_uid,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'patient_id_number': self.patient_id_number,
            'severity': self.severity,
            'category': self.category,
            'description': self.description,
            'recommendation': self.recommendation,
            'source': self.source,
            'type': self.alert_type,
            'data': self.data,
            'dismissed': self.dismissed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
