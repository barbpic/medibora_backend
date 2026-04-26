from app import db
from app.models.user import User
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.vital_signs import VitalSigns
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed database with initial data if empty."""
    
    # Check if users exist
    if User.query.first():
        return
    
    print("Seeding database with initial data...")
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@medibora.co.ke',
        first_name='System',
        last_name='Administrator',
        role='admin',
        department='IT',
        is_active=True
    )
    admin.set_password('admin')
    db.session.add(admin)
    
    # Create doctor user
    doctor = User(
        username='doctor',
        email='doctor@medibora.co.ke',
        first_name='John',
        last_name='Kamau',
        role='doctor',
        department='General Medicine',
        phone='+254712345678',
        is_active=True
    )
    doctor.set_password('doctor')
    db.session.add(doctor)
    
    # Create nurse user
    nurse = User(
        username='nurse',
        email='nurse@medibora.co.ke',
        first_name='Mary',
        last_name='Wanjiku',
        role='nurse',
        department='Outpatient',
        phone='+254723456789',
        is_active=True
    )
    nurse.set_password('nurse')
    db.session.add(nurse)
    
    # Create records officer
    records = User(
        username='records',
        email='records@medibora.co.ke',
        first_name='Grace',
        last_name='Atieno',
        role='records_officer',
        department='Health Records',
        phone='+254734567890',
        is_active=True
    )
    records.set_password('records')
    db.session.add(records)
    
    db.session.commit()
    
    # Create sample patients with NHIF numbers
    sample_patients = [
        {
            'first_name': 'Barbra',
            'last_name': 'Nyakundi',
            'dob': '1995-03-15',
            'gender': 'female',
            'phone': '+254711111111',
            'county': 'Machakos',
            'conditions': 'Influenza with pneumonia',
            'blood_type': 'O+',
            'nhif': 'NHIF001234'
        },
        {
            'first_name': 'Samuel',
            'last_name': 'Odhiambo',
            'dob': '1978-07-22',
            'gender': 'male',
            'phone': '+254722222222',
            'county': 'Nairobi',
            'conditions': 'Hypertension',
            'blood_type': 'A+',
            'nhif': 'NHIF002345'
        },
        {
            'first_name': 'Fatuma',
            'last_name': 'Hassan',
            'dob': '1965-11-08',
            'gender': 'female',
            'phone': '+254733333333',
            'county': 'Mombasa',
            'conditions': 'Diabetes Type 2',
            'blood_type': 'B+',
            'nhif': 'NHIF003456'
        },
        {
            'first_name': 'Peter',
            'last_name': 'Kariuki',
            'dob': '1988-05-30',
            'gender': 'male',
            'phone': '+254744444444',
            'county': 'Uasin Gishu',
            'conditions': 'Asthma',
            'blood_type': 'O+',
            'nhif': 'NHIF004567'
        },
        {
            'first_name': 'Agnes',
            'last_name': 'Mutua',
            'dob': '1972-09-14',
            'gender': 'female',
            'phone': '+254755555555',
            'county': 'Machakos',
            'conditions': '',
            'blood_type': 'AB+',
            'nhif': 'NHIF005678'
        },
        {
            'first_name': 'Ben',
            'last_name': 'Mullins',
            'dob': '1960-01-20',
            'gender': 'male',
            'phone': '+254766666666',
            'county': 'Nairobi',
            'conditions': 'Arthritis',
            'blood_type': 'A-',
            'nhif': 'NHIF006789'
        },
        {
            'first_name': 'Winnie',
            'last_name': 'Chebet',
            'dob': '2001-12-05',
            'gender': 'female',
            'phone': '+254777777777',
            'county': 'Kisumu',
            'conditions': '',
            'blood_type': 'O+',
            'nhif': 'NHIF007890'
        },
        {
            'first_name': 'Joseph',
            'last_name': 'Otieno',
            'dob': '1955-06-18',
            'gender': 'male',
            'phone': '+254788888888',
            'county': 'Nairobi',
            'conditions': 'Hypertension',
            'blood_type': 'B+',
            'nhif': 'NHIF008901'
        }
    ]
    
    year_suffix = datetime.now().year % 100
    for i, p_data in enumerate(sample_patients):
        patient = Patient(
            patient_id=f'MED{year_suffix}{i+1:03d}',
            first_name=p_data['first_name'],
            last_name=p_data['last_name'],
            date_of_birth=datetime.strptime(p_data['dob'], '%Y-%m-%d').date(),
            gender=p_data['gender'],
            blood_type=p_data.get('blood_type'),
            phone=p_data['phone'],
            county=p_data['county'],
            chronic_conditions=p_data['conditions'],
            insurance_provider='NHIF',
            insurance_number=p_data['nhif'],
            registered_by=doctor.id
        )
        db.session.add(patient)
        db.session.flush()
        
        # Create sample encounter
        encounter = Encounter(
            encounter_id=f'ENC{year_suffix}{i+1:03d}',
            patient_id=patient.id,
            provider_id=doctor.id,
            visit_type='outpatient',
            chief_complaint='General checkup and follow-up' if p_data['conditions'] else 'General consultation',
            diagnosis_primary=p_data['conditions'] if p_data['conditions'] else 'Healthy',
            assessment='Clinical presentation consistent with influenza. Rapid influenza test pending.' if 'Influenza' in p_data['conditions'] else 'Patient in stable condition.',
            visit_date=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        db.session.add(encounter)
        db.session.flush()
        
        # Create sample vital signs
        vital_signs = VitalSigns(
            patient_id=patient.id,
            encounter_id=encounter.id,
            recorded_by=nurse.id,
            temperature=round(random.uniform(36.0, 37.5), 1),
            heart_rate=random.randint(65, 85),
            respiratory_rate=random.randint(14, 20),
            blood_pressure_systolic=random.randint(110, 140),
            blood_pressure_diastolic=random.randint(70, 90),
            oxygen_saturation=round(random.uniform(95.0, 99.0), 1),
            weight=round(random.uniform(55.0, 85.0), 1),
            height=random.randint(160, 180),
            pain_score=random.randint(0, 3)
        )
        vital_signs.calculate_bmi()
        vital_signs.check_critical_values()
        db.session.add(vital_signs)
    
    db.session.commit()
    print("Database seeding completed!")
