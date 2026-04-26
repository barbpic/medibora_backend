from datetime import datetime, timedelta

"""
AI-Powered Risk Assessment for MEDIBORA EHR System

This module provides comprehensive risk assessment for patients by analyzing:
- Vital signs (blood pressure, heart rate, temperature, oxygen saturation, BMI)
- Chronic conditions
- Encounter history and frequency
- Patient demographics (age)

USAGE:
------
1. Import and initialize:
   from app.ai.risk_assessment import RiskAssessment
   risk_assessment = RiskAssessment()

2. Call assess_patient_risk() with patient data:
   result = risk_assessment.assess_patient_risk(
       patient=patient_object,      # Patient model instance
       vital_signs=vitals_object,   # VitalSigns model instance  
       encounters=encounters_list   # List of Encounter model instances
   )

3. The result contains:
   - risk_score: Numeric score (0-100+)
   - risk_level: 'critical', 'high', 'moderate', or 'low'
   - risk_factors: List of identified risk factors
   - recommendations: List of clinical recommendations
   - assessed_at: Timestamp of assessment

4. Get quick suggestions for a patient:
   suggestions = risk_assessment.get_clinical_suggestions(patient_id)
   - Returns a dictionary with quick recommendations based on patient data
   
5. Batch assessment for multiple patients:
   results = risk_assessment.batch_assess(patient_ids_list)
   - Returns list of assessments for all patients

Example API endpoint:
   @ai_bp.route('/risk-assessment/<int:patient_id>', methods=['GET'])
   @jwt_required()
   def get_risk_assessment(patient_id):
       patient = Patient.query.get(patient_id)
       vitals = VitalSigns.query.filter_by(patient_id=patient_id).first()
       encounters = Encounter.query.filter_by(patient_id=patient_id).all()
       
       risk_assessment = RiskAssessment()
       result = risk_assessment.assess_patient_risk(patient, vitals, encounters)
       
       return jsonify(result)
"""

class RiskAssessment:
    """
    AI-powered risk assessment for patients.
    Analyzes vital signs, medical history, and encounter data to identify risks.
    """
    
    def __init__(self):
        self.risk_factors = {
            'age': {
                'elderly': 65,
                'very_elderly': 80
            },
            'vital_signs': {
                'temperature_high': 39.0,
                'temperature_low': 35.5,
                'heart_rate_high': 100,
                'heart_rate_low': 60,
                'bp_systolic_high': 140,
                'bp_systolic_low': 90,
                'bp_diastolic_high': 90,
                'bp_diastolic_low': 60,
                'oxygen_low': 92
            }
        }
    
    def assess_patient_risk(self, patient, vital_signs, encounters):
        """
        Perform comprehensive risk assessment for a patient.
        """
        risk_score = 0
        risk_factors = []
        recommendations = []
        
        # Age-based risk
        age = patient.get_age()
        if age >= self.risk_factors['age']['very_elderly']:
            risk_score += 15
            risk_factors.append('Very elderly patient (80+ years)')
            recommendations.append('Consider geriatric care protocols')
        elif age >= self.risk_factors['age']['elderly']:
            risk_score += 10
            risk_factors.append('Elderly patient (65+ years)')
            recommendations.append('Monitor for age-related complications')
        
        # Vital signs risk
        if vital_signs:
            vs_risk, vs_factors, vs_recommendations = self._assess_vital_signs_risk(vital_signs)
            risk_score += vs_risk
            risk_factors.extend(vs_factors)
            recommendations.extend(vs_recommendations)
        
        # Chronic conditions risk
        if patient.chronic_conditions:
            chronic_risk, chronic_factors, chronic_recommendations = self._assess_chronic_conditions(patient.chronic_conditions)
            risk_score += chronic_risk
            risk_factors.extend(chronic_factors)
            recommendations.extend(chronic_recommendations)
        
        # Encounter frequency risk
        if encounters:
            encounter_risk, encounter_factors = self._assess_encounter_frequency(encounters)
            risk_score += encounter_risk
            risk_factors.extend(encounter_factors)
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'assessed_at': datetime.utcnow().isoformat()
        }
    
    def _assess_vital_signs_risk(self, vital_signs):
        """Assess risk based on vital signs."""
        risk_score = 0
        risk_factors = []
        recommendations = []
        
        # Temperature
        if vital_signs.temperature:
            if vital_signs.temperature >= self.risk_factors['vital_signs']['temperature_high']:
                risk_score += 15
                risk_factors.append(f"High fever: {vital_signs.temperature}°C")
                recommendations.append('Investigate infection source; consider antipyretics')
            elif vital_signs.temperature <= self.risk_factors['vital_signs']['temperature_low']:
                risk_score += 20
                risk_factors.append(f"Hypothermia: {vital_signs.temperature}°C")
                recommendations.append('Urgent: Warm patient; check for sepsis or exposure')
        
        # Heart rate
        if vital_signs.heart_rate:
            if vital_signs.heart_rate >= self.risk_factors['vital_signs']['heart_rate_high']:
                risk_score += 10
                risk_factors.append(f"Tachycardia: {vital_signs.heart_rate} bpm")
                recommendations.append('Monitor cardiac status; check for pain, fever, or hypovolemia')
            elif vital_signs.heart_rate <= self.risk_factors['vital_signs']['heart_rate_low']:
                risk_score += 10
                risk_factors.append(f"Bradycardia: {vital_signs.heart_rate} bpm")
                recommendations.append('Evaluate for medication effects or cardiac conduction issues')
        
        # Blood pressure
        if vital_signs.blood_pressure_systolic and vital_signs.blood_pressure_diastolic:
            if (vital_signs.blood_pressure_systolic >= self.risk_factors['vital_signs']['bp_systolic_high'] or 
                vital_signs.blood_pressure_diastolic >= self.risk_factors['vital_signs']['bp_diastolic_high']):
                risk_score += 12
                risk_factors.append(f"Hypertension: {vital_signs.blood_pressure_systolic}/{vital_signs.blood_pressure_diastolic} mmHg")
                recommendations.append('Monitor BP; consider antihypertensive therapy')
            elif (vital_signs.blood_pressure_systolic <= self.risk_factors['vital_signs']['bp_systolic_low'] or 
                  vital_signs.blood_pressure_diastolic <= self.risk_factors['vital_signs']['bp_diastolic_low']):
                risk_score += 15
                risk_factors.append(f"Hypotension: {vital_signs.blood_pressure_systolic}/{vital_signs.blood_pressure_diastolic} mmHg")
                recommendations.append('Urgent: Assess for shock, dehydration, or bleeding')
        
        # Oxygen saturation
        if vital_signs.oxygen_saturation:
            if vital_signs.oxygen_saturation < self.risk_factors['vital_signs']['oxygen_low']:
                risk_score += 25
                risk_factors.append(f"Hypoxemia: SpO2 {vital_signs.oxygen_saturation}%")
                recommendations.append('Urgent: Provide supplemental oxygen; investigate respiratory cause')
        
        # BMI
        if vital_signs.bmi:
            if vital_signs.bmi < 18.5:
                risk_score += 8
                risk_factors.append(f"Underweight: BMI {vital_signs.bmi}")
                recommendations.append('Nutritional assessment and support')
            elif vital_signs.bmi >= 30:
                risk_score += 8
                risk_factors.append(f"Obesity: BMI {vital_signs.bmi}")
                recommendations.append('Weight management counseling')
        
        return risk_score, risk_factors, recommendations
    
    def _assess_chronic_conditions(self, chronic_conditions):
        """Assess risk based on chronic conditions."""
        risk_score = 0
        risk_factors = []
        recommendations = []
        
        conditions = chronic_conditions.lower()
        
        high_risk_conditions = {
            'diabetes': (10, 'Diabetes mellitus', 'Monitor glucose; check HbA1c regularly'),
            'hypertension': (8, 'Hypertension', 'Monitor BP; ensure medication adherence'),
            'hiv': (15, 'HIV/AIDS', 'Monitor CD4 count; ensure ART adherence'),
            'tb': (12, 'Tuberculosis', 'Monitor treatment response; check for drug resistance'),
            'asthma': (8, 'Asthma', 'Ensure inhaler technique; monitor peak flow'),
            'copd': (10, 'COPD', 'Monitor respiratory status; smoking cessation'),
            'heart failure': (15, 'Heart failure', 'Monitor fluid status; cardiac workup'),
            'cancer': (20, 'Cancer', 'Oncology follow-up; monitor for complications'),
            'stroke': (12, 'History of stroke', 'Neurological monitoring; stroke prevention'),
            'kidney': (12, 'Kidney disease', 'Monitor renal function; nephrology referral')
        }
        
        for condition, (score, display_name, recommendation) in high_risk_conditions.items():
            if condition in conditions:
                risk_score += score
                risk_factors.append(display_name)
                recommendations.append(recommendation)
        
        return risk_score, risk_factors, recommendations
    
    def _assess_encounter_frequency(self, encounters):
        """Assess risk based on encounter frequency."""
        risk_score = 0
        risk_factors = []
        
        # Count encounters in last 3 months
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        recent_encounters = [e for e in encounters if e.visit_date >= three_months_ago]
        
        if len(recent_encounters) >= 5:
            risk_score += 15
            risk_factors.append(f'Frequent healthcare utilization ({len(recent_encounters)} visits in 3 months)')
        elif len(recent_encounters) >= 3:
            risk_score += 8
            risk_factors.append(f'Moderate healthcare utilization ({len(recent_encounters)} visits in 3 months)')
        
        return risk_score, risk_factors
    
    def _determine_risk_level(self, risk_score):
        """Determine risk level based on score."""
        if risk_score >= 50:
            return {
                'level': 'critical',
                'color': 'red',
                'description': 'Critical risk - Immediate attention required'
            }
        elif risk_score >= 30:
            return {
                'level': 'high',
                'color': 'orange',
                'description': 'High risk - Close monitoring recommended'
            }
        elif risk_score >= 15:
            return {
                'level': 'moderate',
                'color': 'yellow',
                'description': 'Moderate risk - Regular follow-up advised'
            }
        else:
            return {
                'level': 'low',
                'color': 'green',
                'description': 'Low risk - Routine care'
            }

    def get_clinical_suggestions(self, patient, vital_signs=None, encounters=None):
        """
        Get quick clinical suggestions for a patient based on available data.
        
        Args:
            patient: Patient model instance
            vital_signs: VitalSigns model instance (optional)
            encounters: List of Encounter model instances (optional)
            
        Returns:
            dict: Quick suggestions based on patient data
        """
        suggestions = {
            'priority_actions': [],
            'monitoring': [],
            'lifestyle': [],
            'follow_up': []
        }
        
        # Age-based suggestions
        age = patient.get_age()
        if age >= 65:
            suggestions['monitoring'].append('Consider geriatric assessment')
            suggestions['priority_actions'].append('Review medication list for interactions')
        
        # Chronic conditions
        if patient.chronic_conditions:
            conditions = patient.chronic_conditions.lower()
            if 'diabetes' in conditions:
                suggestions['monitoring'].append('Check HbA1c; monitor blood glucose')
                suggestions['follow_up'].append('Schedule diabetic eye examination')
            if 'hypertension' in conditions:
                suggestions['monitoring'].append('Monitor blood pressure regularly')
                suggestions['lifestyle'].append('Reduce sodium intake; regular exercise')
            if 'asthma' in conditions:
                suggestions['monitoring'].append('Review inhaler technique; check peak flow')
            if 'hiv' in conditions:
                suggestions['monitoring'].append('Monitor CD4 count and viral load')
        
        # Vital signs suggestions
        if vital_signs:
            if vital_signs.blood_pressure_systolic and vital_signs.blood_pressure_systolic >= 140:
                suggestions['priority_actions'].append('Review antihypertensive therapy')
            if vital_signs.oxygen_saturation and vital_signs.oxygen_saturation < 92:
                suggestions['priority_actions'].append('Assess respiratory status; consider oxygen')
            if vital_signs.temperature and vital_signs.temperature > 38.5:
                suggestions['priority_actions'].append('Investigate potential infection')
        
        return suggestions
    
    def batch_assess(self, patients_data):
        """
        Perform risk assessment for multiple patients.
        
        Args:
            patients_data: List of dicts with patient, vital_signs, encounters keys
            
        Returns:
            list: Risk assessment results for each patient
        """
        results = []
        
        for data in patients_data:
            patient = data.get('patient')
            vital_signs = data.get('vital_signs')
            encounters = data.get('encounters', [])
            
            assessment = self.assess_patient_risk(patient, vital_signs, encounters)
            results.append({
                'patient_id': patient.id,
                'patient_name': patient.full_name,
                'assessment': assessment
            })
        
        return results
