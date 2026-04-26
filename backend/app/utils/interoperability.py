"""
Interoperability Module for MEDIBORA
Supports FHIR (Fast Healthcare Interoperability Resources) and HL7 standards
for data exchange with external healthcare systems
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class ResourceType(Enum):
    """FHIR Resource Types"""
    PATIENT = "Patient"
    OBSERVATION = "Observation"
    ENCOUNTER = "Encounter"
    CONDITION = "Condition"
    MEDICATION = "Medication"
    MEDICATION_REQUEST = "MedicationRequest"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    ALLERGY_INTOLERANCE = "AllergyIntolerance"
    IMMUNIZATION = "Immunization"
    ORGANIZATION = "Organization"
    PRACTITIONER = "Practitioner"

@dataclass
class FHIRResource:
    """Represents a FHIR resource"""
    resource_type: ResourceType
    id: str
    meta: Dict[str, Any]
    data: Dict[str, Any]

class FHIRConverter:
    """
    Converts MEDIBORA data to/from FHIR format
    Implements FHIR R4 standard
    """
    
    BASE_URL = "https://medibora.co.ke/fhir"
    
    @staticmethod
    def patient_to_fhir(patient: Any) -> Dict[str, Any]:
        """Convert MEDIBORA Patient to FHIR Patient resource"""
        return {
            "resourceType": "Patient",
            "id": str(patient.id),
            "meta": {
                "versionId": "1",
                "lastUpdated": patient.updated_at.isoformat() if hasattr(patient, 'updated_at') else datetime.utcnow().isoformat(),
                "source": "#medibora-ehr"
            },
            "identifier": [
                {
                    "system": "http://medibora.co.ke/patient-id",
                    "value": patient.patient_id
                }
            ],
            "active": patient.is_active if hasattr(patient, 'is_active') else True,
            "name": [
                {
                    "use": "official",
                    "family": patient.last_name,
                    "given": [patient.first_name]
                }
            ],
            "gender": patient.gender.lower() if hasattr(patient, 'gender') else "unknown",
            "birthDate": patient.date_of_birth.isoformat() if hasattr(patient, 'date_of_birth') else None,
            "telecom": [
                {
                    "system": "phone",
                    "value": patient.phone,
                    "use": "mobile"
                } if hasattr(patient, 'phone') and patient.phone else None,
                {
                    "system": "email",
                    "value": patient.email,
                    "use": "home"
                } if hasattr(patient, 'email') and patient.email else None
            ],
            "address": [
                {
                    "use": "home",
                    "city": patient.city if hasattr(patient, 'city') else None,
                    "state": patient.county if hasattr(patient, 'county') else None,
                    "country": "Kenya"
                }
            ] if hasattr(patient, 'city') or hasattr(patient, 'county') else [],
            "contact": [
                {
                    "relationship": [
                        {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/patient-contactrelationship",
                                    "code": "E"
                                }
                            ]
                        }
                    ],
                    "name": {
                        "text": patient.emergency_contact_name
                    } if hasattr(patient, 'emergency_contact_name') else None,
                    "telecom": [
                        {
                            "system": "phone",
                            "value": patient.emergency_contact_phone
                        }
                    ] if hasattr(patient, 'emergency_contact_phone') else []
                }
            ] if hasattr(patient, 'emergency_contact_name') else []
        }
    
    @staticmethod
    def fhir_to_patient(fhir_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert FHIR Patient resource to MEDIBORA Patient data"""
        name = fhir_data.get("name", [{}])[0]
        telecom = fhir_data.get("telecom", [])
        address = fhir_data.get("address", [{}])[0]
        
        phone = next((t.get("value") for t in telecom if t.get("system") == "phone"), None)
        email = next((t.get("value") for t in telecom if t.get("system") == "email"), None)
        
        return {
            "first_name": name.get("given", [""])[0] if name else "",
            "last_name": name.get("family", "") if name else "",
            "gender": fhir_data.get("gender", "unknown"),
            "date_of_birth": fhir_data.get("birthDate"),
            "phone": phone,
            "email": email,
            "city": address.get("city") if address else None,
            "county": address.get("state") if address else None,
            "is_active": fhir_data.get("active", True)
        }
    
    @staticmethod
    def vital_signs_to_fhir_observation(vitals: Any, patient_id: int) -> Dict[str, Any]:
        """Convert MEDIBORA Vital Signs to FHIR Observation resource"""
        observations = []
        
        # Blood Pressure
        if hasattr(vitals, 'blood_pressure_systolic') and vitals.blood_pressure_systolic:
            observations.append({
                "resourceType": "Observation",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                                "display": "Vital Signs"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "85354-9",
                            "display": "Blood pressure panel"
                        }
                    ]
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "effectiveDateTime": vitals.recorded_at.isoformat() if hasattr(vitals, 'recorded_at') else datetime.utcnow().isoformat(),
                "component": [
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "8480-6",
                                    "display": "Systolic blood pressure"
                                }
                            ]
                        },
                        "valueQuantity": {
                            "value": vitals.blood_pressure_systolic,
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    },
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "8462-4",
                                    "display": "Diastolic blood pressure"
                                }
                            ]
                        },
                        "valueQuantity": {
                            "value": vitals.blood_pressure_diastolic,
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    }
                ]
            })
        
        # Heart Rate
        if hasattr(vitals, 'heart_rate') and vitals.heart_rate:
            observations.append({
                "resourceType": "Observation",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8867-4",
                            "display": "Heart rate"
                        }
                    ]
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "effectiveDateTime": vitals.recorded_at.isoformat() if hasattr(vitals, 'recorded_at') else datetime.utcnow().isoformat(),
                "valueQuantity": {
                    "value": vitals.heart_rate,
                    "unit": "beats/min",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min"
                }
            })
        
        # Temperature
        if hasattr(vitals, 'temperature') and vitals.temperature:
            observations.append({
                "resourceType": "Observation",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "8310-5",
                            "display": "Body temperature"
                        }
                    ]
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "effectiveDateTime": vitals.recorded_at.isoformat() if hasattr(vitals, 'recorded_at') else datetime.utcnow().isoformat(),
                "valueQuantity": {
                    "value": vitals.temperature,
                    "unit": "Cel",
                    "system": "http://unitsofmeasure.org",
                    "code": "Cel"
                }
            })
        
        return observations
    
    @staticmethod
    def encounter_to_fhir(encounter: Any) -> Dict[str, Any]:
        """Convert MEDIBORA Encounter to FHIR Encounter resource"""
        return {
            "resourceType": "Encounter",
            "id": str(encounter.id),
            "status": "finished" if encounter.status == "completed" else "in-progress" if encounter.status == "active" else "cancelled",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB" if encounter.visit_type == "outpatient" else "IMP" if encounter.visit_type == "inpatient" else "EMER"
            },
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "185349003",
                            "display": "Encounter for check up"
                        }
                    ]
                }
            ],
            "subject": {
                "reference": f"Patient/{encounter.patient_id}"
            },
            "participant": [
                {
                    "individual": {
                        "reference": f"Practitioner/{encounter.provider_id}"
                    }
                }
            ],
            "period": {
                "start": encounter.visit_date.isoformat() if hasattr(encounter, 'visit_date') else datetime.utcnow().isoformat()
            },
            "reasonCode": [
                {
                    "text": encounter.chief_complaint if hasattr(encounter, 'chief_complaint') else ""
                }
            ],
            "diagnosis": [
                {
                    "condition": {
                        "text": encounter.diagnosis_primary if hasattr(encounter, 'diagnosis_primary') else ""
                    }
                }
            ] if hasattr(encounter, 'diagnosis_primary') and encounter.diagnosis_primary else []
        }
    
    @staticmethod
    def condition_to_fhir(condition_text: str, patient_id: int) -> Dict[str, Any]:
        """Convert condition text to FHIR Condition resource"""
        return {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active"
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed"
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "problem-list-item"
                        }
                    ]
                }
            ],
            "code": {
                "text": condition_text
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            }
        }
    
    @staticmethod
    def create_bundle(resources: List[Dict[str, Any]], bundle_type: str = "collection") -> Dict[str, Any]:
        """Create a FHIR Bundle containing multiple resources"""
        return {
            "resourceType": "Bundle",
            "id": f"bundle-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "meta": {
                "lastUpdated": datetime.utcnow().isoformat()
            },
            "type": bundle_type,
            "total": len(resources),
            "entry": [
                {
                    "fullUrl": f"{FHIRConverter.BASE_URL}/{resource.get('resourceType')}/{resource.get('id')}",
                    "resource": resource
                }
                for resource in resources
            ]
        }

class HL7Converter:
    """
    Converts MEDIBORA data to/from HL7 v2.x format
    """
    
    @staticmethod
    def patient_to_hl7(patient: Any) -> str:
        """Convert MEDIBORA Patient to HL7 ADT^A04 message"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        message = [
            f"MSH|^~\\&|MEDIBORA|HOSPITAL|EXTERNAL|EXTERNAL|{timestamp}||ADT^A04|{patient.patient_id}|P|2.5",
            f"EVN|A04|{timestamp}",
            f"PID|1||{patient.patient_id}^^^MEDIBORA||{patient.last_name}^{patient.first_name}||{patient.date_of_birth.strftime('%Y%m%d')}|{patient.gender[0].upper() if patient.gender else 'U'}",
            f"PV1|1|O|||||{patient.registered_by if hasattr(patient, 'registered_by') else ''}|||||||||||||||||||||||||||||||{timestamp}"
        ]
        
        return "\r".join(message)
    
    @staticmethod
    def observation_to_hl7(vitals: Any, patient_id: int) -> str:
        """Convert vital signs to HL7 ORU^R01 message"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        message = [
            f"MSH|^~\\&|MEDIBORA|HOSPITAL|EXTERNAL|EXTERNAL|{timestamp}||ORU^R01|{timestamp}|P|2.5",
            f"PID|1||{patient_id}",
            f"OBR|1|||VITALS^Vital Signs|||{timestamp}"
        ]
        
        # Add observations
        obx_count = 1
        if hasattr(vitals, 'blood_pressure_systolic') and vitals.blood_pressure_systolic:
            message.append(f"OBX|{obx_count}|NM|8480-6^Systolic BP||{vitals.blood_pressure_systolic}|mm[Hg]|||||F")
            obx_count += 1
        
        if hasattr(vitals, 'heart_rate') and vitals.heart_rate:
            message.append(f"OBX|{obx_count}|NM|8867-4^Heart Rate||{vitals.heart_rate}|/min|||||F")
            obx_count += 1
        
        if hasattr(vitals, 'temperature') and vitals.temperature:
            message.append(f"OBX|{obx_count}|NM|8310-5^Temperature||{vitals.temperature}|Cel|||||F")
            obx_count += 1
        
        return "\r".join(message)

class InteroperabilityService:
    """
    Main service for handling interoperability operations
    """
    
    def __init__(self):
        self.fhir_converter = FHIRConverter()
        self.hl7_converter = HL7Converter()
    
    def export_patient_fhir(self, patient: Any) -> str:
        """Export patient data as FHIR JSON"""
        fhir_data = self.fhir_converter.patient_to_fhir(patient)
        return json.dumps(fhir_data, indent=2)
    
    def export_patient_hl7(self, patient: Any) -> str:
        """Export patient data as HL7 message"""
        return self.hl7_converter.patient_to_hl7(patient)
    
    def import_patient_fhir(self, fhir_json: str) -> Dict[str, Any]:
        """Import patient data from FHIR JSON"""
        fhir_data = json.loads(fhir_json)
        return self.fhir_converter.fhir_to_patient(fhir_data)
    
    def create_patient_summary_bundle(self, patient: Any, encounters: List[Any], vitals: List[Any]) -> str:
        """Create a FHIR Bundle with patient summary"""
        resources = []
        
        # Add patient
        resources.append(self.fhir_converter.patient_to_fhir(patient))
        
        # Add encounters
        for encounter in encounters:
            resources.append(self.fhir_converter.encounter_to_fhir(encounter))
        
        # Add vital signs observations
        for vital in vitals:
            observations = self.fhir_converter.vital_signs_to_fhir_observation(vital, patient.id)
            resources.extend(observations)
        
        bundle = self.fhir_converter.create_bundle(resources)
        return json.dumps(bundle, indent=2)

# Singleton instance
_interop_service = None

def get_interoperability_service() -> InteroperabilityService:
    """Get or create the interoperability service singleton"""
    global _interop_service
    if _interop_service is None:
        _interop_service = InteroperabilityService()
    return _interop_service
