"""
Rule-Based Decision Support & Alert Engine for MEDIBORA
Implements deterministic IF-THEN logical rules for clinical decision support
Time Complexity: O(n) where n is the number of rules
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ClinicalRule:
    """Represents a clinical decision rule"""
    id: str
    name: str
    description: str
    conditions: List[Dict[str, Any]]
    action: str
    severity: AlertSeverity
    category: str

@dataclass
class Alert:
    """Represents a generated clinical alert"""
    rule_id: str
    rule_name: str
    message: str
    severity: AlertSeverity
    patient_id: int
    created_at: datetime
    category: str
    recommendation: str

class RuleBasedEngine:
    """
    Rule-Based Decision Support & Alert Engine
    Uses deterministic IF-THEN logical rules to evaluate patient data
    """
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> List[ClinicalRule]:
        """Initialize the clinical rule set"""
        return [
            # Hypertension Follow-up Rule
            ClinicalRule(
                id="HTN_FOLLOWUP_001",
                name="Hypertension Follow-up Required",
                description="Patient with hypertension needs follow-up if last visit > 180 days",
                conditions=[
                    {"field": "chronic_conditions", "operator": "contains", "value": "hypertension"},
                    {"field": "days_since_last_visit", "operator": ">", "value": 180}
                ],
                action="trigger_follow_up_alert",
                severity=AlertSeverity.HIGH,
                category="follow_up"
            ),
            
            # Diabetes Follow-up Rule
            ClinicalRule(
                id="DM_FOLLOWUP_001",
                name="Diabetes Follow-up Required",
                description="Patient with diabetes needs follow-up if last visit > 90 days",
                conditions=[
                    {"field": "chronic_conditions", "operator": "contains", "value": "diabetes"},
                    {"field": "days_since_last_visit", "operator": ">", "value": 90}
                ],
                action="trigger_follow_up_alert",
                severity=AlertSeverity.HIGH,
                category="follow_up"
            ),
            
            # Elderly Care Rule
            ClinicalRule(
                id="ELDERLY_CARE_001",
                name="Elderly Patient Care Alert",
                description="Patient over 65 requires regular monitoring",
                conditions=[
                    {"field": "age", "operator": ">=", "value": 65},
                    {"field": "days_since_last_visit", "operator": ">", "value": 60}
                ],
                action="trigger_monitoring_alert",
                severity=AlertSeverity.MEDIUM,
                category="monitoring"
            ),
            
            # High BP Alert
            ClinicalRule(
                id="VITAL_BP_001",
                name="Hypertensive Crisis",
                description="Blood pressure > 180/110 requires immediate attention",
                conditions=[
                    {"field": "bp_systolic", "operator": ">", "value": 180},
                    {"field": "bp_diastolic", "operator": ">", "value": 110}
                ],
                action="trigger_critical_alert",
                severity=AlertSeverity.CRITICAL,
                category="vitals"
            ),
            
            # Low BP Alert
            ClinicalRule(
                id="VITAL_BP_002",
                name="Hypotension Alert",
                description="Blood pressure < 90/60 requires attention",
                conditions=[
                    {"field": "bp_systolic", "operator": "<", "value": 90},
                    {"field": "bp_diastolic", "operator": "<", "value": 60}
                ],
                action="trigger_alert",
                severity=AlertSeverity.HIGH,
                category="vitals"
            ),
            
            # High Temperature
            ClinicalRule(
                id="VITAL_TEMP_001",
                name="High Fever",
                description="Temperature > 39.5°C indicates high fever",
                conditions=[
                    {"field": "temperature", "operator": ">", "value": 39.5}
                ],
                action="trigger_alert",
                severity=AlertSeverity.HIGH,
                category="vitals"
            ),
            
            # Low Temperature
            ClinicalRule(
                id="VITAL_TEMP_002",
                name="Hypothermia",
                description="Temperature < 35°C indicates hypothermia",
                conditions=[
                    {"field": "temperature", "operator": "<", "value": 35.0}
                ],
                action="trigger_critical_alert",
                severity=AlertSeverity.CRITICAL,
                category="vitals"
            ),
            
            # Tachycardia
            ClinicalRule(
                id="VITAL_HR_001",
                name="Tachycardia",
                description="Heart rate > 120 bpm",
                conditions=[
                    {"field": "heart_rate", "operator": ">", "value": 120}
                ],
                action="trigger_alert",
                severity=AlertSeverity.HIGH,
                category="vitals"
            ),
            
            # Bradycardia
            ClinicalRule(
                id="VITAL_HR_002",
                name="Bradycardia",
                description="Heart rate < 50 bpm",
                conditions=[
                    {"field": "heart_rate", "operator": "<", "value": 50}
                ],
                action="trigger_alert",
                severity=AlertSeverity.MEDIUM,
                category="vitals"
            ),
            
            # Hypoxemia
            ClinicalRule(
                id="VITAL_SPO2_001",
                name="Severe Hypoxemia",
                description="Oxygen saturation < 90% requires immediate attention",
                conditions=[
                    {"field": "oxygen_saturation", "operator": "<", "value": 90}
                ],
                action="trigger_critical_alert",
                severity=AlertSeverity.CRITICAL,
                category="vitals"
            ),
            
            # Missed Appointment
            ClinicalRule(
                id="APPT_001",
                name="Missed Follow-up Appointment",
                description="Patient missed scheduled follow-up appointment",
                conditions=[
                    {"field": "missed_appointment", "operator": "==", "value": True},
                    {"field": "days_since_appointment", "operator": ">", "value": 7}
                ],
                action="trigger_follow_up_alert",
                severity=AlertSeverity.MEDIUM,
                category="appointment"
            ),
            
            # Medication Adherence
            ClinicalRule(
                id="MED_001",
                name="Medication Refill Due",
                description="Patient medication refill is overdue",
                conditions=[
                    {"field": "days_since_refill", "operator": ">", "value": 30}
                ],
                action="trigger_medication_alert",
                severity=AlertSeverity.MEDIUM,
                category="medication"
            ),
            
            # HIV Care
            ClinicalRule(
                id="HIV_CARE_001",
                name="HIV Patient Follow-up",
                description="HIV patient requires regular monitoring",
                conditions=[
                    {"field": "chronic_conditions", "operator": "contains", "value": "hiv"},
                    {"field": "days_since_last_visit", "operator": ">", "value": 90}
                ],
                action="trigger_follow_up_alert",
                severity=AlertSeverity.HIGH,
                category="follow_up"
            ),
            
            # TB Treatment
            ClinicalRule(
                id="TB_CARE_001",
                name="TB Treatment Monitoring",
                description="TB patient requires treatment monitoring",
                conditions=[
                    {"field": "chronic_conditions", "operator": "contains", "value": "tuberculosis"},
                    {"field": "days_since_last_visit", "operator": ">", "value": 30}
                ],
                action="trigger_follow_up_alert",
                severity=AlertSeverity.HIGH,
                category="follow_up"
            )
        ]
    
    def evaluate_condition(self, patient_data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Evaluate a single condition against patient data"""
        field = condition["field"]
        operator = condition["operator"]
        value = condition["value"]
        
        # Get the actual value from patient data
        actual_value = patient_data.get(field)
        
        if actual_value is None:
            return False
        
        # Handle string contains for chronic conditions
        if operator == "contains" and isinstance(actual_value, str):
            return value.lower() in actual_value.lower()
        
        # Numeric comparisons
        try:
            if operator == ">":
                return float(actual_value) > float(value)
            elif operator == "<":
                return float(actual_value) < float(value)
            elif operator == ">=":
                return float(actual_value) >= float(value)
            elif operator == "<=":
                return float(actual_value) <= float(value)
            elif operator == "==":
                return actual_value == value
            elif operator == "!=":
                return actual_value != value
        except (ValueError, TypeError):
            return False
        
        return False
    
    def evaluate_rule(self, rule: ClinicalRule, patient_data: Dict[str, Any]) -> bool:
        """Evaluate all conditions of a rule (AND logic)"""
        for condition in rule.conditions:
            if not self.evaluate_condition(patient_data, condition):
                return False
        return True
    
    def evaluate_patient(self, patient_data: Dict[str, Any]) -> List[Alert]:
        """
        Evaluate all rules against a patient's data
        Returns list of triggered alerts
        Time Complexity: O(n) where n is number of rules
        """
        alerts = []
        
        for rule in self.rules:
            if self.evaluate_rule(rule, patient_data):
                alert = Alert(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    message=rule.description,
                    severity=rule.severity,
                    patient_id=patient_data.get("id", 0),
                    created_at=datetime.utcnow(),
                    category=rule.category,
                    recommendation=self._get_recommendation(rule)
                )
                alerts.append(alert)
        
        return alerts
    
    def _get_recommendation(self, rule: ClinicalRule) -> str:
        """Get recommendation based on rule category"""
        recommendations = {
            "follow_up": "Schedule follow-up appointment within 7 days",
            "monitoring": "Increase monitoring frequency",
            "vitals": "Immediate clinical assessment required",
            "appointment": "Contact patient to reschedule appointment",
            "medication": "Review medication adherence and refill prescription"
        }
        return recommendations.get(rule.category, "Consult clinical guidelines")
    
    def get_rules_by_category(self, category: str) -> List[ClinicalRule]:
        """Get all rules for a specific category"""
        return [rule for rule in self.rules if rule.category == category]
    
    def add_custom_rule(self, rule: ClinicalRule) -> None:
        """Add a custom clinical rule"""
        self.rules.append(rule)

# Singleton instance
_rule_engine = None

def get_rule_engine() -> RuleBasedEngine:
    """Get or create the rule engine singleton"""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleBasedEngine()
    return _rule_engine
