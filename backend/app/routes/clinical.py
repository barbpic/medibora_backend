from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models.clinical import (
    Allergy, Problem, Medication, PatientHistory,
    Immunization, Appointment, LabResult, Admission, SBAR
)
from app.models.vital_signs import VitalSigns
from app.models.user import User
from app.models.audit_log import AuditLog

clinical_bp = Blueprint('clinical', __name__)

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


# Allergies Routes
@clinical_bp.route('/<int:patient_id>/allergies', methods=['GET'])
@jwt_required()
def get_allergies(patient_id):
    current_user_id = int(get_jwt_identity())
    
    allergies = Allergy.query.filter_by(patient_id=patient_id, is_active=True).all()
    
    return jsonify({
        'allergies': [a.to_dict() for a in allergies]
    }), 200


@clinical_bp.route('/<int:patient_id>/allergies', methods=['POST'])
@jwt_required()
def create_allergy(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    if not data.get('allergen'):
        return jsonify({'error': 'allergen is required'}), 400
    
    allergy = Allergy(
        patient_id=patient_id,
        allergen=data['allergen'],
        reaction=data.get('reaction'),
        severity=data.get('severity', 'Moderate'),
        recorded_by=current_user_id
    )
    
    db.session.add(allergy)
    db.session.commit()
    
    log_action(current_user_id, 'create_allergy', 'allergy', str(allergy.id), f'Added allergy for patient {patient_id}')
    
    return jsonify({
        'message': 'Allergy added successfully',
        'allergy': allergy.to_dict()
    }), 201


# Problems/Diagnoses Routes
@clinical_bp.route('/<int:patient_id>/problems', methods=['GET'])
@jwt_required()
def get_problems(patient_id):
    current_user_id = int(get_jwt_identity())
    
    problems = Problem.query.filter_by(patient_id=patient_id, is_active=True).all()
    
    return jsonify({
        'problems': [p.to_dict() for p in problems]
    }), 200


@clinical_bp.route('/<int:patient_id>/problems', methods=['POST'])
@jwt_required()
def create_problem(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    if not data.get('description'):
        return jsonify({'error': 'description is required'}), 400
    
    problem = Problem(
        patient_id=patient_id,
        description=data['description'],
        icd10_code=data.get('icd10_code'),
        onset_date=datetime.strptime(data['onset_date'], '%Y-%m-%d').date() if data.get('onset_date') else None,
        problem_type=data.get('problem_type', 'Primary'),
        status=data.get('status', 'Active'),
        recorded_by=current_user_id
    )
    
    db.session.add(problem)
    db.session.commit()
    
    log_action(current_user_id, 'create_problem', 'problem', str(problem.id), f'Added problem for patient {patient_id}')
    
    return jsonify({
        'message': 'Problem added successfully',
        'problem': problem.to_dict()
    }), 201


# Medications Routes
@clinical_bp.route('/<int:patient_id>/medications', methods=['GET'])
@jwt_required()
def get_medications(patient_id):
    current_user_id = int(get_jwt_identity())
    
    medications = Medication.query.filter_by(patient_id=patient_id, is_active=True).all()
    
    return jsonify({
        'medications': [m.to_dict() for m in medications]
    }), 200


@clinical_bp.route('/<int:patient_id>/medications', methods=['POST'])
@jwt_required()
def create_medication(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    if not data.get('medication_name'):
        return jsonify({'error': 'medication_name is required'}), 400
    
    medication = Medication(
        patient_id=patient_id,
        medication_name=data['medication_name'],
        dosage=data.get('dosage'),
        frequency=data.get('frequency'),
        route=data.get('route'),
        special_instructions=data.get('special_instructions'),
        status=data.get('status', 'Active'),
        prescribed_by=current_user_id
    )
    
    db.session.add(medication)
    db.session.commit()
    
    log_action(current_user_id, 'create_medication', 'medication', str(medication.id), f'Added medication for patient {patient_id}')
    
    return jsonify({
        'message': 'Medication added successfully',
        'medication': medication.to_dict()
    }), 201


# Patient Histories Routes
@clinical_bp.route('/<int:patient_id>/histories', methods=['GET'])
@jwt_required()
def get_histories(patient_id):
    current_user_id = int(get_jwt_identity())
    
    histories = PatientHistory.query.filter_by(patient_id=patient_id, is_active=True).all()
    
    return jsonify({
        'histories': [h.to_dict() for h in histories]
    }), 200


@clinical_bp.route('/<int:patient_id>/histories', methods=['POST'])
@jwt_required()
def create_history(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    if not data.get('history_type') or not data.get('description'):
        return jsonify({'error': 'history_type and description are required'}), 400
    
    history = PatientHistory(
        patient_id=patient_id,
        history_type=data['history_type'],
        description=data['description'],
        recorded_by=current_user_id
    )
    
    db.session.add(history)
    db.session.commit()
    
    log_action(current_user_id, 'create_history', 'history', str(history.id), f'Added history for patient {patient_id}')
    
    return jsonify({
        'message': 'History added successfully',
        'history': history.to_dict()
    }), 201


# Immunizations Routes
@clinical_bp.route('/<int:patient_id>/immunizations', methods=['GET'])
@jwt_required()
def get_immunizations(patient_id):
    current_user_id = int(get_jwt_identity())
    
    immunizations = Immunization.query.filter_by(patient_id=patient_id, is_active=True).all()
    
    return jsonify({
        'immunizations': [i.to_dict() for i in immunizations]
    }), 200


@clinical_bp.route('/<int:patient_id>/immunizations', methods=['POST'])
@jwt_required()
def create_immunization(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    if not data.get('vaccine_name') or not data.get('date_given'):
        return jsonify({'error': 'vaccine_name and date_given are required'}), 400
    
    immunization = Immunization(
        patient_id=patient_id,
        vaccine_name=data['vaccine_name'],
        dose=data.get('dose'),
        date_given=datetime.strptime(data['date_given'], '%Y-%m-%d').date(),
        next_due_date=datetime.strptime(data['next_due_date'], '%Y-%m-%d').date() if data.get('next_due_date') else None,
        lot_number=data.get('lot_number'),
        administration_site=data.get('administration_site'),
        administered_by=current_user_id
    )
    
    db.session.add(immunization)
    db.session.commit()
    
    log_action(current_user_id, 'create_immunization', 'immunization', str(immunization.id), f'Added immunization for patient {patient_id}')
    
    return jsonify({
        'message': 'Immunization added successfully',
        'immunization': immunization.to_dict()
    }), 201


# Appointments Routes
@clinical_bp.route('/<int:patient_id>/appointments', methods=['GET'])
@jwt_required()
def get_appointments(patient_id):
    current_user_id = int(get_jwt_identity())
    
    appointments = Appointment.query.filter_by(patient_id=patient_id, is_active=True).order_by(Appointment.appointment_date).all()
    
    return jsonify({
        'appointments': [a.to_dict() for a in appointments]
    }), 200


@clinical_bp.route('/<int:patient_id>/appointments', methods=['POST'])
@jwt_required()
def create_appointment(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    if not data.get('appointment_date') or not data.get('provider'):
        return jsonify({'error': 'appointment_date and provider are required'}), 400
    
    appointment = Appointment(
        patient_id=patient_id,
        appointment_date=datetime.strptime(data['appointment_date'], '%Y-%m-%dT%H:%M'),
        appointment_type=data.get('appointment_type', 'Follow-up'),
        provider=data['provider'],
        notes=data.get('notes'),
        status=data.get('status', 'Scheduled'),
        scheduled_by=current_user_id
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    log_action(current_user_id, 'create_appointment', 'appointment', str(appointment.id), f'Scheduled appointment for patient {patient_id}')
    
    return jsonify({
        'message': 'Appointment scheduled successfully',
        'appointment': appointment.to_dict()
    }), 201


# Lab Results Routes
@clinical_bp.route('/<int:patient_id>/results', methods=['GET'])
@jwt_required()
def get_lab_results(patient_id):
    current_user_id = int(get_jwt_identity())
    
    results = LabResult.query.filter_by(patient_id=patient_id, is_active=True).order_by(LabResult.order_date.desc()).all()
    
    return jsonify({
        'results': [r.to_dict() for r in results]
    }), 200


@clinical_bp.route('/<int:patient_id>/results', methods=['POST'])
@jwt_required()
def create_lab_result(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    if not data.get('test_name') or not data.get('clinical_indication'):
        return jsonify({'error': 'test_name and clinical_indication are required'}), 400
    
    lab_result = LabResult(
        patient_id=patient_id,
        test_name=data['test_name'],
        test_type=data.get('test_type', 'Laboratory'),
        clinical_indication=data['clinical_indication'],
        urgency=data.get('urgency', 'Routine'),
        status=data.get('status', 'Pending'),
        ordered_by=current_user_id
    )
    
    db.session.add(lab_result)
    db.session.commit()
    
    log_action(current_user_id, 'create_lab_result', 'lab_result', str(lab_result.id), f'Ordered lab test for patient {patient_id}')
    
    return jsonify({
        'message': 'Lab test ordered successfully',
        'result': lab_result.to_dict()
    }), 201


# Admissions Routes
@clinical_bp.route('/<int:patient_id>/admissions', methods=['GET'])
@jwt_required()
def get_admissions(patient_id):
    current_user_id = int(get_jwt_identity())
    
    admissions = Admission.query.filter_by(patient_id=patient_id, is_active=True).order_by(Admission.admission_date.desc()).all()
    
    return jsonify({
        'admissions': [a.to_dict() for a in admissions]
    }), 200


@clinical_bp.route('/<int:patient_id>/admissions', methods=['POST'])
@jwt_required()
def create_admission(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    if not data.get('department') or not data.get('primary_diagnosis'):
        return jsonify({'error': 'department and primary_diagnosis are required'}), 400
    
    admission = Admission(
        patient_id=patient_id,
        department=data['department'],
        primary_diagnosis=data['primary_diagnosis'],
        admission_type=data.get('admission_type', 'Emergency'),
        room_number=data.get('room_number'),
        status=data.get('status', 'Active'),
        admitted_by=current_user_id
    )
    
    db.session.add(admission)
    db.session.commit()
    
    log_action(current_user_id, 'create_admission', 'admission', str(admission.id), f'Created admission for patient {patient_id}')
    
    return jsonify({
        'message': 'Admission created successfully',
        'admission': admission.to_dict()
    }), 201


# Vital Signs Routes
@clinical_bp.route('/<int:patient_id>/vitals', methods=['GET'])
@jwt_required()
def get_vital_signs(patient_id):
    current_user_id = int(get_jwt_identity())
    
    vitals = VitalSigns.query.filter_by(patient_id=patient_id).order_by(VitalSigns.recorded_at.desc()).all()
    
    return jsonify({
        'vital_signs': [v.to_dict() for v in vitals]
    }), 200


@clinical_bp.route('/<int:patient_id>/vitals', methods=['POST'])
@jwt_required()
def create_vital_signs(patient_id):
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    
    # Handle both flat and nested blood pressure formats
    bp_systolic = data.get('blood_pressure_systolic') or (data.get('blood_pressure') and data.get('blood_pressure', {}).get('systolic'))
    bp_diastolic = data.get('blood_pressure_diastolic') or (data.get('blood_pressure') and data.get('blood_pressure', {}).get('diastolic'))
    
    if not bp_systolic or not bp_diastolic:
        return jsonify({'error': 'Blood pressure is required'}), 400
    
    vital_signs = VitalSigns(
        patient_id=patient_id,
        recorded_by=current_user_id,
        temperature=data.get('temperature'),
        temperature_site=data.get('temperature_site'),
        heart_rate=data.get('heart_rate'),
        respiratory_rate=data.get('respiratory_rate'),
        blood_pressure_systolic=bp_systolic,
        blood_pressure_diastolic=bp_diastolic,
        oxygen_saturation=data.get('oxygen_saturation'),
        weight=data.get('weight'),
        height=data.get('height'),
        pain_score=data.get('pain_score')
    )
    
    vital_signs.calculate_bmi()
    vital_signs.check_critical_values()
    
    db.session.add(vital_signs)
    db.session.commit()
    
    log_action(current_user_id, 'create_vital_signs', 'vital_signs', str(vital_signs.id), f'Recorded vitals for patient {patient_id}')
    
    return jsonify({
        'message': 'Vital signs recorded successfully',
        'vital_signs': vital_signs.to_dict()
    }), 201


# SBAR Routes
@clinical_bp.route('/<int:patient_id>/sbar', methods=['GET'])
@jwt_required()
def get_sbar_list(patient_id):
    current_user_id = int(get_jwt_identity())
    
    sbars = SBAR.query.filter_by(patient_id=patient_id, is_active=True).order_by(SBAR.created_at.desc()).all()
    
    return jsonify({
        'sbars': [s.to_dict() for s in sbars]
    }), 200


@clinical_bp.route('/<int:patient_id>/sbar', methods=['POST'])
@jwt_required()
def create_sbar(patient_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data.get('situation'):
        return jsonify({'error': 'Situation is required'}), 400
    
    sbar = SBAR(
        patient_id=patient_id,
        recorded_by=current_user_id,
        situation=data['situation'],
        background=data.get('background'),
        assessment=data.get('assessment'),
        recommendation=data.get('recommendation'),
        status=data.get('status', 'draft')
    )
    
    db.session.add(sbar)
    db.session.commit()
    
    log_action(current_user_id, 'create_sbar', 'sbar', str(sbar.id), f'Created SBAR for patient {patient_id}')
    
    return jsonify({
        'message': 'SBAR created successfully',
        'sbar': sbar.to_dict()
    }), 201


# Documents Routes
@clinical_bp.route('/<int:patient_id>/documents', methods=['GET'])
@jwt_required()
def get_documents(patient_id):
    from app.models.clinical import Document
    documents = Document.query.filter_by(patient_id=patient_id, is_active=True).order_by(Document.uploaded_at.desc()).all()
    
    return jsonify({
        'documents': [d.to_dict() for d in documents]
    }), 200


@clinical_bp.route('/<int:patient_id>/documents', methods=['POST'])
@jwt_required()
def create_document(patient_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    from app.models.clinical import Document
    
    if not data.get('title') or not data.get('document_type'):
        return jsonify({'error': 'title and document_type are required'}), 400
    
    document = Document(
        patient_id=patient_id,
        title=data['title'],
        document_type=data['document_type'],
        description=data.get('description'),
        file_path=data.get('file_path'),
        uploaded_by=current_user_id
    )
    
    db.session.add(document)
    db.session.commit()
    
    log_action(current_user_id, 'create_document', 'document', str(document.id), f'Added document for patient {patient_id}')
    
    return jsonify({
        'message': 'Document added successfully',
        'document': document.to_dict()
    }), 201


# Tasks Routes
@clinical_bp.route('/<int:patient_id>/tasks', methods=['GET'])
@jwt_required()
def get_tasks(patient_id):
    from app.models.clinical import Task
    tasks = Task.query.filter_by(patient_id=patient_id, is_active=True).order_by(Task.due_date).all()
    
    return jsonify({
        'tasks': [t.to_dict() for t in tasks]
    }), 200


@clinical_bp.route('/<int:patient_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(patient_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    from app.models.clinical import Task
    
    if not data.get('title'):
        return jsonify({'error': 'title is required'}), 400
    
    task = Task(
        patient_id=patient_id,
        title=data['title'],
        description=data.get('description'),
        task_type=data.get('task_type', 'general'),
        priority=data.get('priority', 'medium'),
        due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None,
        status=data.get('status', 'pending'),
        assigned_to=data.get('assigned_to'),
        created_by=current_user_id
    )
    
    db.session.add(task)
    db.session.commit()
    
    log_action(current_user_id, 'create_task', 'task', str(task.id), f'Created task for patient {patient_id}')
    
    return jsonify({
        'message': 'Task created successfully',
        'task': task.to_dict()
    }), 201


@clinical_bp.route('/<int:patient_id>/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(patient_id, task_id):
    from app.models.clinical import Task
    task = Task.query.get(task_id)
    
    if not task or task.patient_id != patient_id:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    
    if 'status' in data:
        task.status = data['status']
    if 'description' in data:
        task.description = data['description']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Task updated successfully',
        'task': task.to_dict()
    }), 200


# Reports Routes
@clinical_bp.route('/<int:patient_id>/reports', methods=['GET'])
@jwt_required()
def get_reports(patient_id):
    from app.models.clinical import Report
    reports = Report.query.filter_by(patient_id=patient_id, is_active=True).order_by(Report.created_at.desc()).all()
    
    return jsonify({
        'reports': [r.to_dict() for r in reports]
    }), 200


@clinical_bp.route('/<int:patient_id>/reports', methods=['POST'])
@jwt_required()
def create_report(patient_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    from app.models.clinical import Report
    
    if not data.get('report_type'):
        return jsonify({'error': 'report_type is required'}), 400
    
    report = Report(
        patient_id=patient_id,
        report_type=data['report_type'],
        title=data.get('title'),
        date_from=datetime.strptime(data['date_from'], '%Y-%m-%d').date() if data.get('date_from') else None,
        date_to=datetime.strptime(data['date_to'], '%Y-%m-%d').date() if data.get('date_to') else None,
        content=data.get('content'),
        generated_by=current_user_id
    )
    
    db.session.add(report)
    db.session.commit()
    
    log_action(current_user_id, 'create_report', 'report', str(report.id), f'Generated report for patient {patient_id}')
    
    return jsonify({
        'message': 'Report generated successfully',
        'report': report.to_dict()
    }), 201
