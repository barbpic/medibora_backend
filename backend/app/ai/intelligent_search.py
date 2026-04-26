from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.user import User
from fuzzywuzzy import fuzz
import re

class IntelligentSearch:
    """
    Intelligent search engine for EHR system.
    Uses fuzzy matching and context-aware search to find relevant records.
    """
    
    def __init__(self):
        self.search_weights = {
            'patient_name': 1.0,
            'patient_id': 0.9,
            'phone': 0.8,
            'diagnosis': 0.7,
            'symptoms': 0.6
        }
    
    def search(self, query, limit=20):
        """
        Perform intelligent search across patients, encounters, and users.
        """
        results = []
        query_lower = query.lower().strip()
        
        # Search patients
        patient_results = self._search_patients(query_lower)
        results.extend(patient_results)
        
        # Search encounters
        encounter_results = self._search_encounters(query_lower)
        results.extend(encounter_results)
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results[:limit]
    
    def _search_patients(self, query):
        """Search patients with fuzzy matching."""
        results = []
        patients = Patient.query.filter_by(is_active=True).all()
        
        for patient in patients:
            scores = []
            
            # Name matching
            full_name = f"{patient.first_name} {patient.last_name}".lower()
            name_score = fuzz.partial_ratio(query, full_name)
            scores.append(('patient_name', name_score))
            
            # Patient ID matching
            patient_id_score = fuzz.ratio(query, patient.patient_id.lower())
            scores.append(('patient_id', patient_id_score))
            
            # Phone matching
            if patient.phone:
                phone_score = fuzz.ratio(query, patient.phone)
                scores.append(('phone', phone_score))
            
            # Calculate weighted score
            max_score = 0
            for field, score in scores:
                weight = self.search_weights.get(field, 0.5)
                weighted_score = score * weight
                if weighted_score > max_score:
                    max_score = weighted_score
            
            if max_score > 50:  # Threshold for relevance
                results.append({
                    'type': 'patient',
                    'id': patient.id,
                    'title': patient.full_name,
                    'subtitle': f"ID: {patient.patient_id} | Age: {patient.get_age()} | {patient.gender}",
                    'details': f"Phone: {patient.phone or 'N/A'} | County: {patient.county or 'N/A'}",
                    'relevance_score': round(max_score, 2),
                    'url': f'/patients/{patient.id}'
                })
        
        return results
    
    def _search_encounters(self, query):
        """Search encounters with fuzzy matching."""
        results = []
        encounters = Encounter.query.all()
        
        for encounter in encounters:
            scores = []
            
            # Chief complaint matching
            if encounter.chief_complaint:
                complaint_score = fuzz.partial_ratio(query, encounter.chief_complaint.lower())
                scores.append(('symptoms', complaint_score))
            
            # Diagnosis matching
            if encounter.diagnosis_primary:
                diagnosis_score = fuzz.partial_ratio(query, encounter.diagnosis_primary.lower())
                scores.append(('diagnosis', diagnosis_score))
            
            # Encounter ID matching
            encounter_id_score = fuzz.ratio(query, encounter.encounter_id.lower())
            scores.append(('encounter_id', encounter_id_score))
            
            # Calculate weighted score
            max_score = 0
            for field, score in scores:
                weight = self.search_weights.get(field, 0.5)
                weighted_score = score * weight
                if weighted_score > max_score:
                    max_score = weighted_score
            
            if max_score > 50:
                patient = Patient.query.get(encounter.patient_id)
                results.append({
                    'type': 'encounter',
                    'id': encounter.id,
                    'title': f"Encounter {encounter.encounter_id}",
                    'subtitle': f"Patient: {patient.full_name if patient else 'Unknown'} | {encounter.visit_type}",
                    'details': f"Complaint: {encounter.chief_complaint[:50] if encounter.chief_complaint else 'N/A'}...",
                    'relevance_score': round(max_score, 2),
                    'url': f'/encounters/{encounter.id}'
                })
        
        return results
    
    def suggest_similar_terms(self, query):
        """Suggest similar medical terms based on the query."""
        medical_terms = {
            'fever': ['pyrexia', 'hyperthermia', 'febrile'],
            'high bp': ['hypertension', 'elevated blood pressure'],
            'low bp': ['hypotension'],
            'chest pain': ['angina', 'thoracic pain'],
            'shortness of breath': ['dyspnea', 'SOB', 'breathlessness'],
            'diabetes': ['DM', 'high blood sugar', 'hyperglycemia'],
            'malaria': ['plasmodium', 'fever with chills']
        }
        
        suggestions = []
        query_lower = query.lower()
        
        for term, synonyms in medical_terms.items():
            if fuzz.partial_ratio(query_lower, term) > 70:
                suggestions.extend(synonyms)
        
        return suggestions
