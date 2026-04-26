from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models.encounter import Encounter
from app.models.patient import Patient
from app.models.vital_signs import VitalSigns
from app.models.user import User
from app.models.audit_log import AuditLog

encounters_bp = Blueprint('encounters', __name__)

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

def generate_encounter_id():
    # Generate unique encounter ID: ENC25XXX format (ENC + year last 2 digits + sequential number)
    year_suffix = datetime.now().year % 100
    last_encounter = Encounter.query.filter(Encounter.encounter_id.like(f'ENC{year_suffix}%')).order_by(Encounter.id.desc()).first()
    
    if last_encounter:
        # Extract the number part after ENC25
        last_number = int(last_encounter.encounter_id[5:])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f'ENC{year_suffix}{new_number:03d}'

@encounters_bp.route('/', methods=['GET'])
@jwt_required()
def get_encounters():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    # Query parameters
    patient_id = request.args.get('patient_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Encounter.query
    
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    
    if user.role == 'nurse':
        # Nurses can only see encounters they created or are assigned to
        query = query.filter_by(provider_id=current_user_id)
    
    encounters = query.order_by(Encounter.visit_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    log_action(current_user_id, 'view_encounter_list', 'encounter', details=f'Patient: {patient_id}')
    
    return jsonify({
        'encounters': [e.to_summary_dict() for e in encounters.items],
        'total': encounters.total,
        'pages': encounters.pages,
        'current_page': page
    }), 200

@encounters_bp.route('/<int:encounter_id>', methods=['GET'])
@jwt_required()
def get_encounter(encounter_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    encounter = Encounter.query.get(encounter_id)
    
    if not encounter:
        return jsonify({'error': 'Encounter not found'}), 404
    
    log_action(current_user_id, 'view_encounter', 'encounter', str(encounter_id), f'Viewed encounter {encounter.encounter_id}')
    
    return jsonify({'encounter': encounter.to_dict()}), 200

@encounters_bp.route('/', methods=['POST'])
@jwt_required()
def create_encounter():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('create_encounter'):
        log_action(current_user_id, 'create_encounter', 'encounter', None, 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    # Required fields
    if 'patient_id' not in data:
        return jsonify({'error': 'patient_id is required'}), 400
    
    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Create new encounter
    encounter = Encounter(
        encounter_id=generate_encounter_id(),
        patient_id=data['patient_id'],
        provider_id=current_user_id,
        visit_type=data.get('visit_type', 'outpatient'),
        chief_complaint=data.get('chief_complaint'),
        history_of_present_illness=data.get('history_of_present_illness'),
        physical_examination=data.get('physical_examination'),
        assessment=data.get('assessment'),
        diagnosis_primary=data.get('diagnosis_primary'),
        diagnosis_secondary=data.get('diagnosis_secondary'),
        treatment_plan=data.get('treatment_plan'),
        medications_prescribed=data.get('medications_prescribed'),
        procedures=data.get('procedures'),
        lab_tests_ordered=data.get('lab_tests_ordered'),
        follow_up_instructions=data.get('follow_up_instructions'),
        follow_up_date=datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date() if data.get('follow_up_date') else None
    )
    
    db.session.add(encounter)
    db.session.flush()  # Get encounter ID without committing
    
    # Add vital signs if provided
    if 'vital_signs' in data:
        vs_data = data['vital_signs']
        
        # Handle both flat and nested blood pressure formats
        bp_systolic = vs_data.get('blood_pressure_systolic') or (vs_data.get('blood_pressure') and vs_data.get('blood_pressure', {}).get('systolic'))
        bp_diastolic = vs_data.get('blood_pressure_diastolic') or (vs_data.get('blood_pressure') and vs_data.get('blood_pressure', {}).get('diastolic'))
        
        vital_signs = VitalSigns(
            patient_id=data['patient_id'],
            encounter_id=encounter.id,
            recorded_by=current_user_id,
            temperature=vs_data.get('temperature'),
            temperature_site=vs_data.get('temperature_site'),
            heart_rate=vs_data.get('heart_rate'),
            respiratory_rate=vs_data.get('respiratory_rate'),
            blood_pressure_systolic=bp_systolic,
            blood_pressure_diastolic=bp_diastolic,
            oxygen_saturation=vs_data.get('oxygen_saturation'),
            weight=vs_data.get('weight'),
            height=vs_data.get('height'),
            pain_score=vs_data.get('pain_score')
        )
        
        # Calculate BMI and check critical values
        vital_signs.calculate_bmi()
        vital_signs.check_critical_values()
        
        db.session.add(vital_signs)
    
    db.session.commit()
    
    log_action(current_user_id, 'create_encounter', 'encounter', str(encounter.id), f'Created encounter {encounter.encounter_id}')
    
    return jsonify({
        'message': 'Encounter created successfully',
        'encounter': encounter.to_dict()
    }), 201

@encounters_bp.route('/<int:encounter_id>', methods=['PUT'])
@jwt_required()
def update_encounter(encounter_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('edit_encounter'):
        log_action(current_user_id, 'update_encounter', 'encounter', str(encounter_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    encounter = Encounter.query.get(encounter_id)
    
    if not encounter:
        return jsonify({'error': 'Encounter not found'}), 404
    
    data = request.get_json()
    
    # Update fields
    if 'visit_type' in data:
        encounter.visit_type = data['visit_type']
    if 'chief_complaint' in data:
        encounter.chief_complaint = data['chief_complaint']
    if 'history_of_present_illness' in data:
        encounter.history_of_present_illness = data['history_of_present_illness']
    if 'physical_examination' in data:
        encounter.physical_examination = data['physical_examination']
    if 'assessment' in data:
        encounter.assessment = data['assessment']
    if 'diagnosis_primary' in data:
        encounter.diagnosis_primary = data['diagnosis_primary']
    if 'diagnosis_secondary' in data:
        encounter.diagnosis_secondary = data['diagnosis_secondary']
    if 'treatment_plan' in data:
        encounter.treatment_plan = data['treatment_plan']
    if 'medications_prescribed' in data:
        encounter.medications_prescribed = data['medications_prescribed']
    if 'procedures' in data:
        encounter.procedures = data['procedures']
    if 'lab_tests_ordered' in data:
        encounter.lab_tests_ordered = data['lab_tests_ordered']
    if 'lab_results' in data:
        encounter.lab_results = data['lab_results']
    if 'follow_up_instructions' in data:
        encounter.follow_up_instructions = data['follow_up_instructions']
    if 'follow_up_date' in data:
        encounter.follow_up_date = datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date() if data['follow_up_date'] else None
    if 'status' in data:
        encounter.status = data['status']
    
      # Update vital signs if provided
    if 'vital_signs' in data:
        vs_data = data['vital_signs']
        
        if encounter.vital_signs:
            vital_signs = encounter.vital_signs

            if 'temperature' in vs_data:
                vital_signs.temperature = vs_data['temperature']
            if 'temperature_site' in vs_data:
                vital_signs.temperature_site = vs_data['temperature_site']
            if 'heart_rate' in vs_data:
                vital_signs.heart_rate = vs_data['heart_rate']
            if 'respiratory_rate' in vs_data:
                vital_signs.respiratory_rate = vs_data['respiratory_rate']

            bp_systolic = vs_data.get('blood_pressure_systolic') or (
                vs_data.get('blood_pressure') and vs_data.get('blood_pressure', {}).get('systolic')
            )
            bp_diastolic = vs_data.get('blood_pressure_diastolic') or (
                vs_data.get('blood_pressure') and vs_data.get('blood_pressure', {}).get('diastolic')
            )

            if bp_systolic:
                vital_signs.blood_pressure_systolic = bp_systolic
            if bp_diastolic:
                vital_signs.blood_pressure_diastolic = bp_diastolic

            if 'oxygen_saturation' in vs_data:
                vital_signs.oxygen_saturation = vs_data['oxygen_saturation']
            if 'weight' in vs_data:
                vital_signs.weight = vs_data['weight']
            if 'height' in vs_data:
                vital_signs.height = vs_data['height']
            if 'pain_score' in vs_data:
                vital_signs.pain_score = vs_data['pain_score']

        else:
            vital_signs = VitalSigns(
                patient_id=encounter.patient_id,
                encounter_id=encounter.id,
                recorded_by=current_user_id,
                temperature=vs_data.get('temperature'),
                temperature_site=vs_data.get('temperature_site'),
                heart_rate=vs_data.get('heart_rate'),
                respiratory_rate=vs_data.get('respiratory_rate'),
                blood_pressure_systolic=vs_data.get('blood_pressure_systolic'),
                blood_pressure_diastolic=vs_data.get('blood_pressure_diastolic'),
                oxygen_saturation=vs_data.get('oxygen_saturation'),
                weight=vs_data.get('weight'),
                height=vs_data.get('height'),
                pain_score=vs_data.get('pain_score')
            )
            db.session.add(vital_signs)

        vital_signs.calculate_bmi()
        vital_signs.check_critical_values()

    db.session.commit()

    log_action(current_user_id,'update_encounter','encounter',str(encounter_id),f'Updated encounter {encounter.encounter_id}')

    return jsonify({
        'message': 'Encounter updated successfully',
        'encounter': encounter.to_dict()
    }), 200

@encounters_bp.route('/<int:encounter_id>', methods=['DELETE'])
@jwt_required()
def delete_encounter(encounter_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('all'):
        log_action(current_user_id, 'delete_encounter', 'encounter', str(encounter_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    encounter = Encounter.query.get(encounter_id)
    
    if not encounter:
        return jsonify({'error': 'Encounter not found'}), 404
    
    encounter.status = 'cancelled'
    db.session.commit()
    
    log_action(current_user_id, 'delete_encounter', 'encounter', str(encounter_id), f'Cancelled encounter {encounter.encounter_id}')
    
    return jsonify({'message': 'Encounter cancelled successfully'}), 200

@encounters_bp.route('/patient/<int:patient_id>/history', methods=['GET'])
@jwt_required()
def get_patient_history(patient_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    encounters = Encounter.query.filter_by(patient_id=patient_id).order_by(Encounter.visit_date.desc()).all()
    
    log_action(current_user_id, 'view_patient_history', 'patient', str(patient_id), f'Viewed history for patient {patient.patient_id}')
    
    return jsonify({
        'patient': patient.to_summary_dict(),
        'encounters': [e.to_summary_dict() for e in encounters]
    }), 200
