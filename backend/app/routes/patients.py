from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models.patient import Patient
from app.models.user import User
from app.models.audit_log import AuditLog

patients_bp = Blueprint('patients', __name__)

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

def generate_patient_id():
    # Generate unique patient ID: MED25XXX format (MED + year last 2 digits + sequential number)
    year_suffix = datetime.now().year % 100
    last_patient = Patient.query.filter(Patient.patient_id.like(f'MED{year_suffix}%')).order_by(Patient.id.desc()).first()
    
    if last_patient:
        # Extract the number part after MED25
        last_number = int(last_patient.patient_id[5:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f'MED{year_suffix}{new_number:03d}'

@patients_bp.route('/', methods=['GET'])
@jwt_required()
def get_patients():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    # Query parameters
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Patient.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.patient_id.ilike(f'%{search}%'),
                Patient.phone.ilike(f'%{search}%'),
                Patient.county.ilike(f'%{search}%'),
                Patient.city.ilike(f'%{search}%'),
                Patient.allergies.ilike(f'%{search}%'),
                Patient.chronic_conditions.ilike(f'%{search}%'),
                Patient.email.ilike(f'%{search}%')
            )
        )
    
    patients = query.order_by(Patient.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    log_action(current_user_id, 'view_patient_list', 'patient', details=f'Searched: {search}')
    
    return jsonify({
        'patients': [p.to_summary_dict() for p in patients.items],
        'total': patients.total,
        'pages': patients.pages,
        'current_page': page
    }), 200

@patients_bp.route('/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    log_action(current_user_id, 'view_patient', 'patient', str(patient_id), f'Viewed patient {patient.patient_id}')
    
    return jsonify({'patient': patient.to_dict()}), 200

@patients_bp.route('/', methods=['POST'])
@jwt_required()
def create_patient():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('register_patient'):
        log_action(current_user_id, 'create_patient', 'patient', None, 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Required fields
    required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Create new patient
    patient = Patient(
        patient_id=generate_patient_id(),
        first_name=data['first_name'],
        last_name=data['last_name'],
        date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date(),
        gender=data['gender'],
        blood_type=data.get('blood_type'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        city=data.get('city'),
        county=data.get('county'),
        emergency_contact_name=data.get('emergency_contact_name'),
        emergency_contact_phone=data.get('emergency_contact_phone'),
        emergency_contact_relationship=data.get('emergency_contact_relationship'),
        insurance_provider=data.get('insurance_provider'),
        insurance_number=data.get('insurance_number'),
        allergies=data.get('allergies'),
        chronic_conditions=data.get('chronic_conditions'),
        current_medications=data.get('current_medications'),
        registered_by=current_user_id
    )
    
    db.session.add(patient)
    db.session.commit()
    
    log_action(current_user_id, 'create_patient', 'patient', str(patient.id), f'Created patient {patient.patient_id}')
    
    return jsonify({
        'message': 'Patient created successfully',
        'patient': patient.to_dict()
    }), 201

@patients_bp.route('/<int:patient_id>', methods=['PUT'])
@jwt_required()
def update_patient(patient_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('edit_patient'):
        log_action(current_user_id, 'update_patient', 'patient', str(patient_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'first_name' in data:
        patient.first_name = data['first_name']
    if 'last_name' in data:
        patient.last_name = data['last_name']
    if 'date_of_birth' in data:
        patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    if 'gender' in data:
        patient.gender = data['gender']
    if 'blood_type' in data:
        patient.blood_type = data['blood_type']
    if 'phone' in data:
        patient.phone = data['phone']
    if 'email' in data:
        patient.email = data['email']
    if 'address' in data:
        patient.address = data['address']
    if 'city' in data:
        patient.city = data['city']
    if 'county' in data:
        patient.county = data['county']
    if 'emergency_contact_name' in data:
        patient.emergency_contact_name = data['emergency_contact_name']
    if 'emergency_contact_phone' in data:
        patient.emergency_contact_phone = data['emergency_contact_phone']
    if 'emergency_contact_relationship' in data:
        patient.emergency_contact_relationship = data['emergency_contact_relationship']
    if 'insurance_provider' in data:
        patient.insurance_provider = data['insurance_provider']
    if 'insurance_number' in data:
        patient.insurance_number = data['insurance_number']
    if 'allergies' in data:
        patient.allergies = data['allergies']
    if 'chronic_conditions' in data:
        patient.chronic_conditions = data['chronic_conditions']
    if 'current_medications' in data:
        patient.current_medications = data['current_medications']
    
    db.session.commit()
    
    log_action(current_user_id, 'update_patient', 'patient', str(patient_id), f'Updated patient {patient.patient_id}')
    
    return jsonify({
        'message': 'Patient updated successfully',
        'patient': patient.to_dict()
    }), 200

@patients_bp.route('/<int:patient_id>/clinical', methods=['PUT'])
@jwt_required()
def update_patient_clinical(patient_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('edit_patient'):
        log_action(current_user_id, 'update_patient_clinical', 'patient', str(patient_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    data = request.get_json()
    
    if 'allergies' in data:
        patient.allergies = data['allergies']
    if 'chronic_conditions' in data:
        patient.chronic_conditions = data['chronic_conditions']
    if 'current_medications' in data:
        patient.current_medications = data['current_medications']
    
    db.session.commit()
    
    log_action(current_user_id, 'update_patient_clinical', 'patient', str(patient_id), f'Updated clinical data for patient {patient.patient_id}')
    
    return jsonify({
        'message': 'Patient clinical data updated successfully',
        'patient': patient.to_dict()
    }), 200

@patients_bp.route('/<int:patient_id>', methods=['DELETE'])
@jwt_required()
def delete_patient(patient_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('all'):  # Only admin can delete
        log_action(current_user_id, 'delete_patient', 'patient', str(patient_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    patient.is_active = False
    db.session.commit()
    
    log_action(current_user_id, 'delete_patient', 'patient', str(patient_id), f'Deactivated patient {patient.patient_id}')
    
    return jsonify({'message': 'Patient deactivated successfully'}), 200

@patients_bp.route('/search', methods=['GET'])
@jwt_required()
def search_patients():
    current_user_id = int(get_jwt_identity())
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify({'patients': []}), 200
    
    patients = Patient.query.filter(
        db.and_(
            Patient.is_active == True,
            db.or_(
                Patient.first_name.ilike(f'%{query}%'),
                Patient.last_name.ilike(f'%{query}%'),
                Patient.patient_id.ilike(f'%{query}%'),
                Patient.phone.ilike(f'%{query}%'),
                Patient.county.ilike(f'%{query}%'),
                Patient.city.ilike(f'%{query}%'),
                Patient.allergies.ilike(f'%{query}%'),
                Patient.chronic_conditions.ilike(f'%{query}%')
            )
        )
    ).limit(20).all()
    
    log_action(current_user_id, 'search_patients', 'patient', details=f'Search query: {query}')
    
    return jsonify({
        'patients': [p.to_summary_dict() for p in patients]
    }), 200
