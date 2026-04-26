from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.vital_signs import VitalSigns
from app.models.patient import Patient
from app.models.user import User
from app.models.audit_log import AuditLog

alerts_bp = Blueprint('alerts', __name__)

def log_action(user_id, action, resource_type=None, resource_id=None, details=None, success=True):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        success=success
    )
    db.session.add(log)
    db.session.commit()

@alerts_bp.route('/vital-signs', methods=['GET'])
@jwt_required()
def get_vital_sign_alerts():
    """Get all vital sign alerts, optionally filtered by severity"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    # Query parameters
    severity = request.args.get('severity')  # 'critical', 'high', 'medium', 'low'
    patient_id = request.args.get('patient_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query for vital signs with alerts
    query = VitalSigns.query.filter(VitalSigns.alert_generated == True)
    
    if severity:
        query = query.filter(VitalSigns.alert_severity == severity)
    
    if patient_id:
        query = query.filter(VitalSigns.patient_id == patient_id)
    
    # Order by most recent first
    vital_signs_with_alerts = query.order_by(
        VitalSigns.recorded_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    # Format response
    alerts = []
    for vs in vital_signs_with_alerts.items:
        alerts.append({
            'id': vs.id,
            'patient_id': vs.patient_id,
            'patient_name': f"{vs.patient.first_name} {vs.patient.last_name}" if vs.patient else "Unknown",
            'encounter_id': vs.encounter_id,
            'recorded_at': vs.recorded_at.isoformat() if vs.recorded_at else None,
            'severity': vs.alert_severity,
            'description': vs.alert_description,
            'vital_signs': {
                'temperature': vs.temperature,
                'heart_rate': vs.heart_rate,
                'respiratory_rate': vs.respiratory_rate,
                'blood_pressure': f"{vs.blood_pressure_systolic}/{vs.blood_pressure_diastolic}" if vs.blood_pressure_systolic and vs.blood_pressure_diastolic else None,
                'oxygen_saturation': vs.oxygen_saturation,
                'pain_score': vs.pain_score,
                'bmi': vs.bmi
            }
        })
    
    log_action(current_user_id, 'view_vital_sign_alerts', 'alert', details=f'Severity: {severity}, Patient: {patient_id}')
    
    return jsonify({
        'alerts': alerts,
        'total': vital_signs_with_alerts.total,
        'pages': vital_signs_with_alerts.pages,
        'current_page': page,
        'severity_breakdown': {
            'critical': len([a for a in alerts if a['severity'] == 'critical']),
            'high': len([a for a in alerts if a['severity'] == 'high']),
            'medium': len([a for a in alerts if a['severity'] == 'medium']),
            'low': len([a for a in alerts if a['severity'] == 'low'])
        }
    }), 200

@alerts_bp.route('/vital-signs/<int:alert_id>', methods=['GET'])
@jwt_required()
def get_alert_detail(alert_id):
    """Get detailed information about a specific alert"""
    current_user_id = int(get_jwt_identity())
    
    vital_sign = VitalSigns.query.get(alert_id)
    
    if not vital_sign or not vital_sign.alert_generated:
        return jsonify({'error': 'Alert not found'}), 404
    
    log_action(current_user_id, 'view_alert_detail', 'alert', str(alert_id))
    
    return jsonify({
        'alert': {
            'id': vital_sign.id,
            'patient_id': vital_sign.patient_id,
            'patient_name': f"{vital_sign.patient.first_name} {vital_sign.patient.last_name}",
            'encounter_id': vital_sign.encounter_id,
            'recorded_at': vital_sign.recorded_at.isoformat() if vital_sign.recorded_at else None,
            'recorded_by': vital_sign.recorded_by,
            'severity': vital_sign.alert_severity,
            'description': vital_sign.alert_description,
            'all_vital_signs': vital_sign.to_dict()
        }
    }), 200

@alerts_bp.route('/vital-signs/<int:alert_id>/acknowledge', methods=['POST'])
@jwt_required()
def acknowledge_alert(alert_id):
    """Mark an alert as acknowledged"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    vital_sign = VitalSigns.query.get(alert_id)
    
    if not vital_sign or not vital_sign.alert_generated:
        return jsonify({'error': 'Alert not found'}), 404
    
    log_action(current_user_id, 'acknowledge_alert', 'alert', str(alert_id), 
               f'User {user.full_name} acknowledged alert for patient {vital_sign.patient_id}')
    
    return jsonify({
        'message': 'Alert acknowledged successfully',
        'alert_id': alert_id
    }), 200
