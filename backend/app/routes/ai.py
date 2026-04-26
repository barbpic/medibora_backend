from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.patient import Patient
from app.models.vital_signs import VitalSigns
from app.models.encounter import Encounter
from app.models.user import User
from app.models.audit_log import AuditLog
from app.ai.intelligent_search_tf_idf import get_search_engine, expand_medical_query
from app.ai.rule_based_engine import get_rule_engine, AlertSeverity
from app.ai.risk_classifier import get_risk_classifier
from app.ai.vitals_risk_model import vitals_risk_predictor
from app.utils.interoperability import get_interoperability_service
from datetime import datetime, timedelta, date


ai_bp = Blueprint('ai', __name__)

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

# ==================== INTELLIGENT SEARCH (TF-IDF) ====================

@ai_bp.route('/search', methods=['GET'])
@jwt_required()
def intelligent_search():
    """
    AI-Powered Intelligent Search using TF-IDF and Cosine Similarity
    Processes clinical notes with NLP for semantic search
    """
    current_user_id = int(int(get_jwt_identity()))
    query = request.args.get('q', '')
    patient_id = request.args.get('patient_id', type=int)
    top_k = request.args.get('limit', 10, type=int)
    
    if not query:
        return jsonify({'results': []}), 200
    
    # Expand medical query with synonyms
    expanded_query = expand_medical_query(query)
    
    # Get search engine and index documents if needed
    search_engine = get_search_engine()
    
    # Build document index from patient data
    documents = []
    patients = Patient.query.filter_by(is_active=True).all()
    
    for patient in patients:
        # Add patient document with expanded fields including county and symptoms
        documents.append({
            'id': patient.id,
            'type': 'patient',
            'title': f"{patient.last_name}, {patient.first_name}",
            'content': f"{patient.chronic_conditions or ''} {patient.allergies or ''} {patient.current_medications or ''} {patient.county or ''} {patient.city or ''} {patient.address or ''}",
            'metadata': {
                'patient_id': patient.id,
                'patient_id_number': patient.patient_id,
                'age': patient.get_age(),
                'gender': patient.gender,
                'county': patient.county,
                'city': patient.city,
                'phone': patient.phone,
                'email': patient.email
            }
        })
        
        # Add encounter documents with symptoms and diagnoses
        for encounter in patient.encounters:
            documents.append({
                'id': encounter.id,
                'type': 'encounter',
                'title': f"Encounter {encounter.encounter_id}",
                'content': f"{encounter.chief_complaint or ''} {encounter.history_of_present_illness or ''} {encounter.assessment or ''} {encounter.diagnosis_primary or ''} {encounter.diagnosis_secondary or ''} {encounter.treatment_plan or ''} {encounter.procedures or ''} {encounter.lab_tests_ordered or ''}",
                'metadata': {
                    'patient_id': patient.id,
                    'encounter_id': encounter.encounter_id,
                    'visit_date': encounter.visit_date.isoformat() if encounter.visit_date else None,
                    'visit_type': encounter.visit_type
                }
            })
    
    # Index documents
    search_engine.index_documents(documents)
    
    # Perform search
    if patient_id:
        results = search_engine.search_by_patient(expanded_query, patient_id, top_k)
    else:
        results = search_engine.search(expanded_query, top_k)
    
    # Format results
    formatted_results = []
    for result in results:
        formatted_results.append({
            'id': result.id,
            'type': result.type,
            'title': result.title,
            'content': result.content,
            'relevance_score': round(result.similarity_score * 100, 2),
            'metadata': result.metadata,
            'url': f"/patients/{result.metadata.get('patient_id', result.id)}" if result.type == 'patient' else f"/encounters/{result.id}"
        })
    
    # Get similar term suggestions
    suggestions = search_engine.suggest_similar_terms(query)
    
    log_action(current_user_id, 'ai_search', None, None, f'Search query: {query}')
    
    return jsonify({
        'query': query,
        'expanded_query': expanded_query,
        'suggestions': suggestions,
        'results': formatted_results,
        'total': len(formatted_results)
    }), 200


# ==================== RULE-BASED ALERT ENGINE ====================

@ai_bp.route('/alerts/evaluate/<int:patient_id>', methods=['POST'])
@jwt_required()
def evaluate_patient_alerts(patient_id):
    """
    Rule-Based Decision Support & Alert Engine
    Evaluates patient data against clinical rules (O(n) complexity)
    """
    current_user_id = int(get_jwt_identity())
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Get latest vital signs
    latest_vitals = VitalSigns.query.filter_by(patient_id=patient_id).order_by(VitalSigns.recorded_at.desc()).first()
    
    # Get last encounter
    last_encounter = Encounter.query.filter_by(patient_id=patient_id).order_by(Encounter.visit_date.desc()).first()
    
    # Calculate days since last visit
    days_since_last_visit = 365
    if last_encounter and last_encounter.visit_date:
        visit_date = last_encounter.visit_date
        if hasattr(visit_date, 'date'):
            visit_date = visit_date.date()
        days_since_last_visit = (date.today() - visit_date).days
    # Build patient data for rule evaluation
    patient_data = {
        'id': patient.id,
        'age': patient.get_age(),
        'chronic_conditions': patient.chronic_conditions or '',
        'days_since_last_visit': days_since_last_visit,
        'bp_systolic': latest_vitals.blood_pressure_systolic if latest_vitals else 120,
        'bp_diastolic': latest_vitals.blood_pressure_diastolic if latest_vitals else 80,
        'temperature': latest_vitals.temperature if latest_vitals else 37.0,
        'heart_rate': latest_vitals.heart_rate if latest_vitals else 72,
        'oxygen_saturation': latest_vitals.oxygen_saturation if latest_vitals else 98,
        'missed_appointment': False,  # Would be calculated from appointment data
        'days_since_appointment': 0,
        'days_since_refill': 0,
        'current_medications': patient.current_medications or ''
    }
    
    # Evaluate rules
    rule_engine = get_rule_engine()
    alerts = rule_engine.evaluate_patient(patient_data)
    
    # Format alerts
    formatted_alerts = []
    for alert in alerts:
        formatted_alerts.append({
            'rule_id': alert.rule_id,
            'rule_name': alert.rule_name,
            'message': alert.message,
            'severity': alert.severity.value,
            'category': alert.category,
            'recommendation': alert.recommendation,
            'created_at': alert.created_at.isoformat()
        })
    
    log_action(current_user_id, 'evaluate_alerts', 'patient', str(patient_id), f'Generated {len(alerts)} alerts')
    
    return jsonify({
        'patient_id': patient_id,
        'alert_count': len(formatted_alerts),
        'alerts': formatted_alerts
    }), 200


@ai_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_critical_alerts():
    """Get all critical alerts across patients"""
    current_user_id = int(get_jwt_identity())
    
    # Get all vital signs with critical alerts
    critical_vitals = VitalSigns.query.filter(
        VitalSigns.alert_generated == True
    ).order_by(VitalSigns.recorded_at.desc()).limit(20).all()
    
    alerts = []
    for vital in critical_vitals:
        patient = Patient.query.get(vital.patient_id)
        if patient:
            alerts.append({
                'id': vital.id,
                'patient_id': patient.id,
                'patient_name': f"{patient.first_name} {patient.last_name}",
                'patient_id_number': patient.patient_id,
                'severity': vital.alert_severity,
                'description': vital.alert_description,
                'recorded_at': vital.recorded_at.isoformat() if vital.recorded_at else None,
                'vital_signs': vital.to_dict()
            })
    
    log_action(current_user_id, 'view_alerts', None, None, f'Viewed {len(alerts)} critical alerts')
    
    return jsonify({
        'alerts': alerts,
        'total': len(alerts)
    }), 200


# ==================== MACHINE LEARNING RISK CLASSIFICATION ====================

@ai_bp.route('/risk-assessment/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_risk_assessment(patient_id):
    """
    Machine Learning-Based Risk Classification
    Uses Logistic Regression to predict missed follow-up risk
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user.has_permission('ai_features'):
        log_action(current_user_id, 'risk_assessment', 'patient', str(patient_id), 'Permission denied', False)
        return jsonify({'error': 'Permission denied'}), 403
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Get patient's encounter history
    encounters = Encounter.query.filter_by(patient_id=patient_id).all()
    
    # Get last encounter date
    last_encounter = Encounter.query.filter_by(patient_id=patient_id).order_by(Encounter.visit_date.desc()).first()
    
    # Build patient data for risk prediction
    patient_data = {
        'id': patient.id,
        'age': patient.get_age(),
        'last_visit': last_encounter.visit_date.isoformat() if last_encounter and last_encounter.visit_date else None,
        'chronic_conditions': patient.chronic_conditions,
        'visit_count_last_year': len([e for e in encounters if e.visit_date and (e.visit_date.date() if hasattr(e.visit_date, 'date') else e.visit_date) >= (datetime.utcnow() - timedelta(days=365)).date()]),
        'missed_appointments': 0,  # Would be calculated from appointment data
        'current_medications': patient.current_medications
    }
    
    # Perform risk assessment
    classifier = get_risk_classifier()
    prediction = classifier.predict_risk(patient_data)
    
    # Get feature importance
    feature_importance = classifier.get_feature_importance()
    
    log_action(current_user_id, 'risk_assessment', 'patient', str(patient_id), f'Risk: {prediction.risk_level}')
    
    return jsonify({
        'patient_id': patient_id,
        'patient_name': patient.full_name,
        'assessment': {
            'risk_score': prediction.risk_score,
            'risk_level': prediction.risk_level,
            'probability': prediction.probability,
            'features_used': prediction.features_used,
            'feature_importance': feature_importance,
            'recommendation': prediction.recommendation,
            'assessed_at': prediction.timestamp.isoformat()
        }
    }), 200


@ai_bp.route('/risk-assessment/batch', methods=['POST'])
@jwt_required()
def batch_risk_assessment():
    """Perform risk assessment for multiple patients"""
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    patient_ids = data.get('patient_ids', [])
    
    if not patient_ids:
        return jsonify({'error': 'No patient IDs provided'}), 400
    
    classifier = get_risk_classifier()
    results = []
    
    for patient_id in patient_ids:
        patient = Patient.query.get(patient_id)
        if patient:
            last_encounter = Encounter.query.filter_by(patient_id=patient_id).order_by(Encounter.visit_date.desc()).first()
            encounters = Encounter.query.filter_by(patient_id=patient_id).all()
            
            patient_data = {
                'id': patient.id,
                'age': patient.get_age(),
                'last_visit': last_encounter.visit_date.isoformat() if last_encounter and last_encounter.visit_date else None,
                'chronic_conditions': patient.chronic_conditions,
                'visit_count_last_year': len([e for e in encounters if e.visit_date and (e.visit_date.date() if hasattr(e.visit_date, 'date') else e.visit_date) >= (datetime.utcnow() - timedelta(days=365)).date()]),
                'missed_appointments': 0,
                'current_medications': patient.current_medications
            }
            
            prediction = classifier.predict_risk(patient_data)
            results.append({
                'patient_id': patient_id,
                'patient_name': patient.full_name,
                'risk_score': prediction.risk_score,
                'risk_level': prediction.risk_level
            })
    
    log_action(current_user_id, 'batch_risk_assessment', None, None, f'Assessed {len(results)} patients')
    
    return jsonify({
        'total': len(results),
        'high_risk': len([r for r in results if r['risk_level'] == 'HIGH']),
        'medium_risk': len([r for r in results if r['risk_level'] == 'MEDIUM']),
        'low_risk': len([r for r in results if r['risk_level'] == 'LOW']),
        'results': results
    }), 200


# ==================== DIAGNOSIS SUGGESTIONS ====================

@ai_bp.route('/suggestions/diagnosis', methods=['POST'])
@jwt_required()
def get_diagnosis_suggestions():
    """Get AI-powered diagnosis suggestions based on symptoms"""
    current_user_id = int(get_jwt_identity())
    
    data = request.get_json()
    symptoms = data.get('symptoms', [])
    
    if not symptoms:
        return jsonify({'suggestions': []}), 200
    
    # Symptom-Diagnosis mapping based on common Kenyan conditions
    symptom_diagnosis_map = {
        'fever': [
            {'diagnosis': 'Malaria', 'icd10': 'B50-B54', 'confidence': 85},
            {'diagnosis': 'Typhoid Fever', 'icd10': 'A01.0', 'confidence': 70},
            {'diagnosis': 'Respiratory Infection', 'icd10': 'J06.9', 'confidence': 65},
            {'diagnosis': 'COVID-19', 'icd10': 'U07.1', 'confidence': 60},
            {'diagnosis': 'Dengue Fever', 'icd10': 'A90', 'confidence': 45}
        ],
        'cough': [
            {'diagnosis': 'Acute Bronchitis', 'icd10': 'J20.9', 'confidence': 80},
            {'diagnosis': 'Pneumonia', 'icd10': 'J18.9', 'confidence': 75},
            {'diagnosis': 'Tuberculosis', 'icd10': 'A15.0', 'confidence': 60},
            {'diagnosis': 'Asthma', 'icd10': 'J45.9', 'confidence': 55},
            {'diagnosis': 'COVID-19', 'icd10': 'U07.1', 'confidence': 50}
        ],
        'headache': [
            {'diagnosis': 'Tension Headache', 'icd10': 'G44.2', 'confidence': 75},
            {'diagnosis': 'Migraine', 'icd10': 'G43.9', 'confidence': 65},
            {'diagnosis': 'Malaria', 'icd10': 'B50-B54', 'confidence': 60},
            {'diagnosis': 'Hypertension', 'icd10': 'I10', 'confidence': 50},
            {'diagnosis': 'Meningitis', 'icd10': 'G03.9', 'confidence': 30}
        ],
        'chest pain': [
            {'diagnosis': 'Angina Pectoris', 'icd10': 'I20.9', 'confidence': 80},
            {'diagnosis': 'Myocardial Infarction', 'icd10': 'I21.9', 'confidence': 70},
            {'diagnosis': 'GERD', 'icd10': 'K21.9', 'confidence': 55},
            {'diagnosis': 'Costochondritis', 'icd10': 'M94.0', 'confidence': 45},
            {'diagnosis': 'Pneumonia', 'icd10': 'J18.9', 'confidence': 40}
        ],
        'shortness of breath': [
            {'diagnosis': 'Asthma', 'icd10': 'J45.9', 'confidence': 80},
            {'diagnosis': 'Pneumonia', 'icd10': 'J18.9', 'confidence': 75},
            {'diagnosis': 'Heart Failure', 'icd10': 'I50.9', 'confidence': 65},
            {'diagnosis': 'COPD', 'icd10': 'J44.9', 'confidence': 60},
            {'diagnosis': 'Pulmonary Embolism', 'icd10': 'I26.9', 'confidence': 35}
        ],
        'abdominal pain': [
            {'diagnosis': 'Gastritis', 'icd10': 'K29.7', 'confidence': 70},
            {'diagnosis': 'Appendicitis', 'icd10': 'K35.8', 'confidence': 65},
            {'diagnosis': 'Peptic Ulcer', 'icd10': 'K27.9', 'confidence': 60},
            {'diagnosis': 'Gastroenteritis', 'icd10': 'A09', 'confidence': 55},
            {'diagnosis': 'Cholecystitis', 'icd10': 'K81.0', 'confidence': 40}
        ],
        'diarrhea': [
            {'diagnosis': 'Gastroenteritis', 'icd10': 'A09', 'confidence': 85},
            {'diagnosis': 'Food Poisoning', 'icd10': 'A05.9', 'confidence': 70},
            {'diagnosis': 'Dysentery', 'icd10': 'A03.9', 'confidence': 50},
            {'diagnosis': 'Cholera', 'icd10': 'A00.9', 'confidence': 30},
            {'diagnosis': 'IBS', 'icd10': 'K58.9', 'confidence': 25}
        ],
        'rash': [
            {'diagnosis': 'Allergic Reaction', 'icd10': 'T78.4', 'confidence': 75},
            {'diagnosis': 'Dermatitis', 'icd10': 'L30.9', 'confidence': 65},
            {'diagnosis': 'Measles', 'icd10': 'B05.9', 'confidence': 50},
            {'diagnosis': 'Chickenpox', 'icd10': 'B01.9', 'confidence': 45},
            {'diagnosis': 'Typhoid (Rose Spots)', 'icd10': 'A01.0', 'confidence': 35}
        ],
        'joint pain': [
            {'diagnosis': 'Osteoarthritis', 'icd10': 'M19.90', 'confidence': 75},
            {'diagnosis': 'Malaria', 'icd10': 'B50-B54', 'confidence': 60},
            {'diagnosis': 'Dengue Fever', 'icd10': 'A90', 'confidence': 50},
            {'diagnosis': 'Rheumatoid Arthritis', 'icd10': 'M06.9', 'confidence': 45},
            {'diagnosis': 'Gout', 'icd10': 'M10.9', 'confidence': 35}
        ],
        'fatigue': [
            {'diagnosis': 'Anemia', 'icd10': 'D64.9', 'confidence': 70},
            {'diagnosis': 'Malaria', 'icd10': 'B50-B54', 'confidence': 65},
            {'diagnosis': 'Hypothyroidism', 'icd10': 'E03.9', 'confidence': 50},
            {'diagnosis': 'Depression', 'icd10': 'F32.9', 'confidence': 45},
            {'diagnosis': 'Diabetes', 'icd10': 'E11.9', 'confidence': 40}
        ]
    }
    
    # Aggregate suggestions from all symptoms
    suggestions_map = {}
    for symptom in symptoms:
        symptom_lower = symptom.lower()
        if symptom_lower in symptom_diagnosis_map:
            for diag in symptom_diagnosis_map[symptom_lower]:
                key = diag['diagnosis']
                if key in suggestions_map:
                    suggestions_map[key]['confidence'] = min(95, suggestions_map[key]['confidence'] + 15)
                else:
                    suggestions_map[key] = diag.copy()
    
    # Sort by confidence
    sorted_suggestions = sorted(suggestions_map.values(), key=lambda x: x['confidence'], reverse=True)
    
    log_action(current_user_id, 'diagnosis_suggestions', None, None, f'Symptoms: {symptoms}')
    
    return jsonify({
        'symptoms': symptoms,
        'suggestions': sorted_suggestions[:5]
    }), 200


# ==================== DASHBOARD STATS ====================

@ai_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get AI-enhanced dashboard statistics"""
    current_user_id = int(get_jwt_identity())
    
    # Get statistics
    total_patients = Patient.query.filter_by(is_active=True).count()
    total_encounters = Encounter.query.count()
    today_encounters = Encounter.query.filter(
        db.func.date(Encounter.visit_date) == db.func.current_date()
    ).count()
    critical_alerts = VitalSigns.query.filter(
        VitalSigns.alert_generated == True,
        VitalSigns.alert_severity.in_(['high', 'critical'])
    ).count()
    
    # Get high-risk patients
    classifier = get_risk_classifier()
    high_risk_count = 0
    
    # Recent patients
    recent_patients = Patient.query.filter_by(is_active=True).order_by(
        Patient.created_at.desc()
    ).limit(5).all()
    
    log_action(current_user_id, 'view_dashboard_stats', None, None, 'Viewed dashboard statistics')
    
    return jsonify({
        'stats': {
            'total_patients': total_patients,
            'total_encounters': total_encounters,
            'today_encounters': today_encounters,
            'critical_alerts': critical_alerts,
            'high_risk_patients': high_risk_count
        },
        'recent_patients': [p.to_summary_dict() for p in recent_patients]
    }), 200


# ==================== INTEROPERABILITY ENDPOINTS ====================

@ai_bp.route('/export/fhir/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def export_patient_fhir(patient_id):
    """Export patient data in FHIR format"""
    current_user_id = int(get_jwt_identity())
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    interop = get_interoperability_service()
    fhir_json = interop.export_patient_fhir(patient)
    
    log_action(current_user_id, 'export_fhir', 'patient', str(patient_id), 'Exported to FHIR')
    
    return jsonify({
        'patient_id': patient_id,
        'format': 'FHIR R4',
        'data': json.loads(fhir_json)
    }), 200


@ai_bp.route('/export/hl7/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def export_patient_hl7(patient_id):
    """Export patient data in HL7 v2.x format"""
    current_user_id = int(get_jwt_identity())
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    interop = get_interoperability_service()
    hl7_message = interop.export_patient_hl7(patient)
    
    log_action(current_user_id, 'export_hl7', 'patient', str(patient_id), 'Exported to HL7')
    
    return jsonify({
        'patient_id': patient_id,
        'format': 'HL7 v2.5',
        'message': hl7_message
    }), 200


@ai_bp.route('/export/fhir/bundle/<int:patient_id>', methods=['GET'])
@jwt_required()
def export_patient_bundle(patient_id):
    """Export complete patient summary as FHIR Bundle"""
    current_user_id = int(get_jwt_identity())
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    encounters = Encounter.query.filter_by(patient_id=patient_id).all()
    vitals = VitalSigns.query.filter_by(patient_id=patient_id).all()
    
    interop = get_interoperability_service()
    bundle_json = interop.create_patient_summary_bundle(patient, encounters, vitals)
    
    log_action(current_user_id, 'export_fhir_bundle', 'patient', str(patient_id), 'Exported FHIR Bundle')
    
    return jsonify({
        'patient_id': patient_id,
        'format': 'FHIR R4 Bundle',
        'data': json.loads(bundle_json)
    }), 200
# ==================== VITALS RISK PREDICTION ====================

@ai_bp.route('/vitals-risk/predict', methods=['POST'])
@jwt_required(optional=True)  # Optional for testing, can be removed in production
def predict_vitals_risk():
    """
    Predict clinical risk from vital signs data
    Uses trained ML model or rule-based fallback
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract vitals with default values for missing fields
        vital_signs = {
            'heart_rate': data.get('heart_rate'),
            'respiratory_rate': data.get('respiratory_rate'),
            'temperature': data.get('temperature'),
            'oxygen_saturation': data.get('oxygen_saturation'),
            'systolic_bp': data.get('systolic_bp'),
            'diastolic_bp': data.get('diastolic_bp'),
            'age': data.get('age'),
            'gender': data.get('gender'),
            'weight': data.get('weight', 70),
            'height': data.get('height', 1.7),
            'heart_rate_variability': data.get('heart_rate_variability', 0.1)
        }
        
        # Validate required fields
        required_fields = ['heart_rate', 'respiratory_rate', 'temperature', 
                          'oxygen_saturation', 'systolic_bp', 'diastolic_bp', 
                          'age', 'gender']
        
        missing_fields = [field for field in required_fields if vital_signs.get(field) is None]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields,
                'required_fields': required_fields
            }), 400
        
        # Get prediction from vitals risk model
        result = vitals_risk_predictor.predict(vital_signs)
        
        # Add input data to response for reference
        result['input_data'] = {
            'heart_rate': vital_signs['heart_rate'],
            'respiratory_rate': vital_signs['respiratory_rate'],
            'temperature': vital_signs['temperature'],
            'oxygen_saturation': vital_signs['oxygen_saturation'],
            'blood_pressure': f"{vital_signs['systolic_bp']}/{vital_signs['diastolic_bp']}",
            'age': vital_signs['age'],
            'gender': vital_signs['gender']
        }
        
        # Log if user is authenticated
        try:
            current_user_id = get_jwt_identity()
            if current_user_id:
                log_action(int(current_user_id), 'vitals_risk_prediction', None, None, 
                          f'Risk score: {result["risk_score"]:.2f}')
        except:
            pass  # Skip logging for unauthenticated requests
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in predict_vitals_risk: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@ai_bp.route('/vitals-risk/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def patient_vitals_risk(patient_id):
    """Get risk assessment for a patient using their latest vital signs from database"""
    current_user_id = int(get_jwt_identity())
    
    # Get patient info
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Get latest vital signs
    latest_vitals = VitalSigns.query.filter_by(
        patient_id=patient_id
    ).order_by(VitalSigns.recorded_at.desc()).first()
    
    if not latest_vitals:
        return jsonify({
            'error': 'No vital signs recorded for this patient',
            'patient_id': patient_id,
            'patient_name': f"{patient.first_name} {patient.last_name}"
        }), 404
    
    # Prepare vitals data with patient info
    vitals_data = {
        'heart_rate': latest_vitals.heart_rate,
        'respiratory_rate': latest_vitals.respiratory_rate,
        'temperature': latest_vitals.temperature,
        'oxygen_saturation': latest_vitals.oxygen_saturation,
        'systolic_bp': latest_vitals.blood_pressure_systolic,
        'diastolic_bp': latest_vitals.blood_pressure_diastolic,
        'age': patient.get_age(),
        'gender': patient.gender,
        'weight': latest_vitals.weight,
        'height': latest_vitals.height,
        'heart_rate_variability': getattr(latest_vitals, 'heart_rate_variability', 0.1)
    }
    
    # Get prediction
    result = vitals_risk_predictor.predict(vitals_data)
    
    # Add patient info
    result['patient'] = {
        'id': patient_id,
        'name': f"{patient.first_name} {patient.last_name}",
        'gender': patient.gender,
        'age': patient.get_age()
    }
    result['vitals_timestamp'] = latest_vitals.recorded_at.isoformat() if latest_vitals.recorded_at else None
    
    log_action(current_user_id, 'patient_vitals_risk', 'patient', str(patient_id), 
              f'Risk score: {result["risk_score"]:.2f}')
    
    return jsonify(result), 200


@ai_bp.route('/vitals-risk/high-risk-patients', methods=['GET'])
@jwt_required()
def high_risk_patients():
    """Get all patients with recent high-risk vitals"""
    current_user_id = int(get_jwt_identity())
    
    # Get patients with vitals recorded in last 24 hours
    last_24h = datetime.utcnow() - timedelta(hours=24)
    
    # Get latest vitals per patient
    from sqlalchemy import func, and_
    
    # Subquery to get latest vitals per patient
    latest_vitals_subq = db.session.query(
        VitalSigns.patient_id,
        func.max(VitalSigns.recorded_at).label('latest_time')
    ).filter(VitalSigns.recorded_at >= last_24h).group_by(VitalSigns.patient_id).subquery()
    
    # Get the actual vitals
    recent_vitals = db.session.query(VitalSigns, Patient).join(
        latest_vitals_subq,
        and_(
            VitalSigns.patient_id == latest_vitals_subq.c.patient_id,
            VitalSigns.recorded_at == latest_vitals_subq.c.latest_time
        )
    ).join(Patient, Patient.id == VitalSigns.patient_id).all()
    
    high_risk_patients = []
    
    for vital, patient in recent_vitals:
        vitals_data = {
            'heart_rate': vital.heart_rate,
            'respiratory_rate': vital.respiratory_rate,
            'temperature': vital.temperature,
            'oxygen_saturation': vital.oxygen_saturation,
            'systolic_bp': vital.blood_pressure_systolic,
            'diastolic_bp': vital.blood_pressure_diastolic,
            'age': patient.get_age(),
            'gender': patient.gender,
            'weight': vital.weight,
            'height': vital.height,
        }
        
        risk = vitals_risk_predictor.predict(vitals_data)
        
        if risk['risk_score'] >= 0.6:  # High risk threshold
            high_risk_patients.append({
                'patient_id': patient.id,
                'patient_name': f"{patient.first_name} {patient.last_name}",
                'risk_score': risk['risk_score'],
                'risk_level': risk['risk_level'],
                'recommendation': risk['recommendation'],
                'recorded_at': vital.recorded_at.isoformat() if vital.recorded_at else None
            })
    
    # Sort by risk score descending
    high_risk_patients.sort(key=lambda x: x['risk_score'], reverse=True)
    
    log_action(current_user_id, 'high_risk_patients', None, None, f'Found {len(high_risk_patients)} high risk patients')
    
    return jsonify({
        'count': len(high_risk_patients),
        'patients': high_risk_patients,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@ai_bp.route('/vitals-risk/model-info', methods=['GET'])
@jwt_required(optional=True)
def vitals_model_info():
    """Get information about the vitals risk model"""
    return jsonify({
        'model_trained': vitals_risk_predictor.is_trained,
        'model_type': 'trained_ml_model' if vitals_risk_predictor.is_trained else 'rule_based_fallback',
        'features_used': vitals_risk_predictor.feature_columns if vitals_risk_predictor.is_trained else None,
        'disclaimer': 'AI-assisted prediction - not a substitute for clinical judgment'
    }), 200


@ai_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify server is running"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'available_endpoints': [
            '/api/ai/search',
            '/api/ai/alerts/evaluate/<patient_id>',
            '/api/ai/alerts',
            '/api/ai/risk-assessment/<patient_id>',
            '/api/ai/vitals-risk/predict',
            '/api/ai/vitals-risk/patient/<patient_id>',
            '/api/ai/vitals-risk/high-risk-patients',
            '/api/ai/vitals-risk/model-info',
            '/api/ai/health'
        ]
    }), 200
# ==================== AI RECOMMENDATIONS FOR PATIENT ====================

# backend/app/routes/ai.py - Update the recommendations endpoint

@ai_bp.route('/recommendations/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_ai_recommendations(patient_id):
    """
    Get AI-powered recommendations based on patient's vitals and clinical data
    Returns both structured and full text recommendations
    """
    current_user_id = int(get_jwt_identity())
    
    # Get patient
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Get latest vital signs
    latest_vitals = VitalSigns.query.filter_by(
        patient_id=patient_id
    ).order_by(VitalSigns.recorded_at.desc()).first()
    
    if not latest_vitals:
        return jsonify({
            'error': 'No vital signs recorded for this patient',
            'recommendations': {
                'priority_actions': ['Record vital signs to generate AI recommendations'],
                'monitoring': ['Schedule initial assessment'],
                'lifestyle': ['Regular health checkup recommended']
            }
        }), 200
    
    # Prepare vitals data
    vitals_data = {
        'heart_rate': latest_vitals.heart_rate,
        'respiratory_rate': latest_vitals.respiratory_rate,
        'temperature': latest_vitals.temperature,
        'oxygen_saturation': latest_vitals.oxygen_saturation,
        'systolic_bp': latest_vitals.blood_pressure_systolic,
        'diastolic_bp': latest_vitals.blood_pressure_diastolic,
        'age': patient.get_age(),
        'gender': patient.gender,
        'weight': latest_vitals.weight,
        'height': latest_vitals.height,
    }
    
    # Get risk assessment
    risk_result = vitals_risk_predictor.predict(vitals_data)
    
    # Generate structured recommendations
    structured_recs = generate_structured_recommendations(
        patient, latest_vitals, risk_result
    )
    
    # Generate full text recommendation (like the expected output)
    full_text_recommendation = generate_full_text_recommendation(
        patient, latest_vitals, risk_result
    )
    
    log_action(current_user_id, 'get_recommendations', 'patient', str(patient_id), 
              f'Risk level: {risk_result["risk_level"]}')
    
    return jsonify({
        'patient_id': patient_id,
        'patient_name': f"{patient.first_name} {patient.last_name}",
        'assessment_time': datetime.utcnow().isoformat(),
        'risk_summary': {
            'level': risk_result['risk_level'],
            'score': risk_result['risk_score'],
            'percentage': risk_result['risk_percentage']
        },
        'abnormal_findings': risk_result.get('abnormal_findings', []),
        'news2_score': risk_result.get('news2_score', 0),
        'news2_interpretation': risk_result.get('news2_interpretation', ''),
        # NEW: Full text recommendation (like expected output)
        'full_recommendation': full_text_recommendation,
        # Structured recommendations (for UI components)
        'structured_recommendations': structured_recs
    }), 200


def generate_full_text_recommendation(patient, vitals, risk_result):
    """
    Generate the full text recommendation with all bullet points
    This matches the expected output format
    """
    risk_score = risk_result['risk_score']
    risk_level = risk_result['risk_level']
    findings = risk_result.get('abnormal_findings', [])
    
    lines = []
    
    # Header with emoji based on risk level
    if risk_score >= 0.7:
        lines.append("🔴 IMMEDIATE ACTION REQUIRED:")
    elif risk_score >= 0.4:
        lines.append("🟡 CLOSE MONITORING REQUIRED:")
    else:
        lines.append("🟢 ROUTINE CARE:")
    
    # Add action items based on specific abnormalities
    actions_added = set()
    
    # Check each vital sign and add appropriate actions
    if vitals.oxygen_saturation and vitals.oxygen_saturation < 90:
        lines.append("   • Administer supplemental oxygen")
        actions_added.add('oxygen')
    elif vitals.oxygen_saturation and vitals.oxygen_saturation < 94:
        lines.append("   • Monitor oxygen saturation closely")
        actions_added.add('oxygen_monitor')
    
    if vitals.blood_pressure_systolic and vitals.blood_pressure_systolic < 90:
        lines.append("   • Start IV fluids")
        actions_added.add('fluids')
    elif vitals.blood_pressure_systolic and vitals.blood_pressure_systolic > 180:
        lines.append("   • Administer antihypertensive medication")
        actions_added.add('bp_meds')
    
    if vitals.temperature and vitals.temperature > 39.0:
        lines.append("   • Administer antipyretics")
        lines.append("   • Order blood cultures and CBC")
        actions_added.add('antipyretics')
    elif vitals.temperature and vitals.temperature > 38.0:
        lines.append("   • Consider antipyretics if symptomatic")
        actions_added.add('antipyretics_mild')
    
    if vitals.heart_rate and vitals.heart_rate > 120:
        lines.append("   • Order ECG")
        lines.append("   • Assess for dehydration or pain")
        actions_added.add('ecg')
    elif vitals.heart_rate and vitals.heart_rate > 100:
        lines.append("   • Monitor heart rate trends")
        actions_added.add('hr_monitor')
    
    if vitals.respiratory_rate and vitals.respiratory_rate > 24:
        lines.append("   • Assess respiratory status")
        lines.append("   • Consider chest X-ray")
        actions_added.add('resp_assess')
    
    # Add general actions based on risk level
    if risk_score >= 0.7:
        if 'notify' not in actions_added:
            lines.append("   • Notify attending physician immediately")
        if 'admit' not in actions_added:
            lines.append("   • Consider hospital admission")
        if 'repeat_vitals' not in actions_added:
            lines.append("   • Repeat vital signs in 15 minutes")
    
    # Add age-specific actions
    age = patient.get_age()
    if age and age > 75:
        lines.append("   • Consider geriatric assessment")
        lines.append("   • Review medication list for interactions")
    elif age and age > 65:
        lines.append("   • Review medication list for potential interactions")
    
    # Add chronic condition specific actions
    if patient.chronic_conditions:
        if 'hypertension' in patient.chronic_conditions.lower():
            lines.append("   • Review antihypertensive regimen")
        if 'diabetes' in patient.chronic_conditions.lower():
            lines.append("   • Check blood glucose")
        if 'asthma' in patient.chronic_conditions.lower() or 'copd' in patient.chronic_conditions.lower():
            lines.append("   • Assess peak flow and inhaler technique")
    
    # Remove duplicates while preserving order
    unique_lines = []
    for line in lines:
        if line not in unique_lines:
            unique_lines.append(line)
    
    return "\n".join(unique_lines)


def generate_structured_recommendations(patient, vitals, risk_result):
    """
    Generate structured recommendations (for UI components)
    This is your existing function but kept for compatibility
    """
    priority_actions = []
    monitoring_suggestions = []
    lifestyle_advice = []
    
    # Get abnormal findings
    risk_score = risk_result['risk_score']
    risk_level = risk_result['risk_level']
    
    # ============================================================
    # PRIORITY ACTIONS
    # ============================================================
    
    # Oxygen/Respiratory issues
    if vitals.oxygen_saturation and vitals.oxygen_saturation < 90:
        priority_actions.append({
            'action': '🚨 Start supplemental oxygen immediately',
            'priority': 'critical',
            'reason': f'SpO2 is {vitals.oxygen_saturation}% (severe hypoxemia)'
        })
    elif vitals.oxygen_saturation and vitals.oxygen_saturation < 94:
        priority_actions.append({
            'action': '📊 Monitor oxygen saturation closely',
            'priority': 'high',
            'reason': f'SpO2 is {vitals.oxygen_saturation}% (below normal range)'
        })
    
    # Respiratory rate issues
    if vitals.respiratory_rate and vitals.respiratory_rate > 24:
        priority_actions.append({
            'action': '🫁 Assess respiratory distress',
            'priority': 'critical',
            'reason': f'Respiratory rate is {vitals.respiratory_rate}/min (tachypnea)'
        })
    elif vitals.respiratory_rate and vitals.respiratory_rate > 20:
        priority_actions.append({
            'action': '📈 Monitor respiratory rate',
            'priority': 'medium',
            'reason': f'Respiratory rate is {vitals.respiratory_rate}/min (elevated)'
        })
    
    # Blood pressure issues
    if vitals.blood_pressure_systolic and vitals.blood_pressure_systolic > 180:
        priority_actions.append({
            'action': '🚑 Immediate BP reduction needed',
            'priority': 'critical',
            'reason': f'BP is {vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic} mmHg (hypertensive crisis)'
        })
    elif vitals.blood_pressure_systolic and vitals.blood_pressure_systolic > 140:
        priority_actions.append({
            'action': '💊 Review antihypertensive medication',
            'priority': 'high',
            'reason': f'BP is {vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic} mmHg (elevated)'
        })
    elif vitals.blood_pressure_systolic and vitals.blood_pressure_systolic < 90:
        priority_actions.append({
            'action': '💧 Start IV fluids',
            'priority': 'critical',
            'reason': f'BP is {vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic} mmHg (hypotension)'
        })
    
    # Temperature issues
    if vitals.temperature and vitals.temperature > 39.0:
        priority_actions.append({
            'action': '🌡️ Administer antipyretics and investigate infection source',
            'priority': 'high',
            'reason': f'Temperature is {vitals.temperature}°C (high fever)'
        })
    elif vitals.temperature and vitals.temperature > 38.0:
        priority_actions.append({
            'action': '🦠 Order blood cultures and WBC count',
            'priority': 'medium',
            'reason': f'Temperature is {vitals.temperature}°C (fever)'
        })
    
    # Heart rate issues
    if vitals.heart_rate and vitals.heart_rate > 120:
        priority_actions.append({
            'action': '❤️ Order ECG and cardiac evaluation',
            'priority': 'high',
            'reason': f'Heart rate is {vitals.heart_rate} bpm (severe tachycardia)'
        })
    elif vitals.heart_rate and vitals.heart_rate > 100:
        priority_actions.append({
            'action': '🩺 Assess for dehydration, pain, or infection',
            'priority': 'medium',
            'reason': f'Heart rate is {vitals.heart_rate} bpm (tachycardia)'
        })
    elif vitals.heart_rate and vitals.heart_rate < 50:
        priority_actions.append({
            'action': '📋 Review medications (beta-blockers, digoxin)',
            'priority': 'medium',
            'reason': f'Heart rate is {vitals.heart_rate} bpm (bradycardia)'
        })
    
    # Age-specific actions
    age = patient.get_age()
    if age and age > 75:
        priority_actions.append({
            'action': '👴 Consider geriatric assessment',
            'priority': 'medium',
            'reason': f'Patient age: {age} years (elderly)'
        })
    elif age and age > 65:
        priority_actions.append({
            'action': '📝 Review medication list for interactions',
            'priority': 'low',
            'reason': f'Patient age: {age} years (increased risk)'
        })
    
    # ============================================================
    # MONITORING SUGGESTIONS
    # ============================================================
    
    if risk_level == 'HIGH RISK':
        monitoring_suggestions.append({
            'suggestion': '🔴 Reassess vital signs every 15-30 minutes',
            'frequency': '15-30 minutes',
            'duration': 'Until stable'
        })
        monitoring_suggestions.append({
            'suggestion': '🏥 Consider ICU transfer or close monitoring unit',
            'frequency': 'Continuous',
            'duration': '24-48 hours'
        })
    elif risk_level == 'MODERATE RISK':
        monitoring_suggestions.append({
            'suggestion': '🟡 Monitor vital signs every 2-4 hours',
            'frequency': '2-4 hours',
            'duration': '24 hours'
        })
        monitoring_suggestions.append({
            'suggestion': '📞 Schedule follow-up within 24-48 hours',
            'frequency': 'Once',
            'duration': 'Follow-up'
        })
    else:
        monitoring_suggestions.append({
            'suggestion': '🟢 Routine vital signs monitoring',
            'frequency': 'As scheduled',
            'duration': 'Ongoing'
        })
    
    if vitals.oxygen_saturation and vitals.oxygen_saturation < 94:
        monitoring_suggestions.append({
            'suggestion': '📊 Continuous pulse oximetry monitoring',
            'frequency': 'Continuous',
            'duration': 'Until SpO2 > 94%'
        })
    
    # ============================================================
    # LIFESTYLE ADVICE
    # ============================================================
    
    if vitals.blood_pressure_systolic and vitals.blood_pressure_systolic > 130:
        lifestyle_advice.append({
            'advice': '🧂 Reduce sodium intake (less than 2g/day)',
            'category': 'Diet',
            'reason': 'To help lower blood pressure'
        })
        lifestyle_advice.append({
            'advice': '🏃 Regular aerobic exercise (30 min, 5x/week)',
            'category': 'Exercise',
            'reason': 'Improves cardiovascular health'
        })
    
    lifestyle_advice.append({
        'advice': '💧 Stay hydrated (8-10 glasses of water daily)',
        'category': 'Hydration',
        'reason': 'Essential for overall health'
    })
    lifestyle_advice.append({
        'advice': '😴 Maintain regular sleep schedule (7-8 hours)',
        'category': 'Sleep',
        'reason': 'Improves immune function and recovery'
    })
    lifestyle_advice.append({
        'advice': '🚭 Avoid smoking and limit alcohol',
        'category': 'Lifestyle',
        'reason': 'Reduces cardiovascular risk'
    })
    
    # Limit items
    priority_actions = priority_actions[:5]
    monitoring_suggestions = monitoring_suggestions[:3]
    lifestyle_advice = lifestyle_advice[:4]
    
    return {
        'priority_actions': priority_actions,
        'monitoring': monitoring_suggestions,
        'lifestyle': lifestyle_advice
    }

import json
