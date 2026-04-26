# MEDIBORA EHR System

**MEDIBORA: Improving Kenyan Healthcare Through Developing an Electronic Health Record System Which Implements Artificial Intelligence**

A comprehensive Electronic Health Record (EHR) system with AI integration, designed as a fourth-year project for Machakos University.

## Features

### Core EHR Functionality
- **Patient Registration**: Complete patient demographic and medical history management
- **Encounter Documentation**: Detailed visit records with chief complaints, diagnoses, and treatment plans
- **Vital Signs Tracking**: Real-time vital signs monitoring with automated alerts
- **Medical History**: Allergies, chronic conditions, and medication tracking

### AI Integration
- **Intelligent Search**: AI-powered natural language search across patient records
- **Risk Assessment**: AI-driven patient risk scoring based on vital signs and medical history
- **Critical Alerts**: Automated alerts for abnormal vital signs
- **Diagnosis Suggestions**: Rule-based diagnosis recommendations based on symptoms

### Security & Compliance
- **Role-Based Access Control (RBAC)**: Different permissions for admin, doctor, nurse, and records officer
- **Audit Logging**: Complete tracking of all system activities
- **JWT Authentication**: Secure token-based authentication
- **Data Protection**: Aligned with Kenya's Data Protection Act (2019) and Digital Health Act (2023)

## Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: ORM for database management
- **MySQL**: Relational database
- **Flask-JWT-Extended**: JWT authentication
- **Flask-CORS**: Cross-origin resource sharing
- **Scikit-learn**: Machine learning for AI features

### Frontend
- **React**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: UI component library
- **TanStack Query**: Data fetching and caching

## Project Structure

```
medibora-ehr/
├── backend/                 # Flask backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/         # Database models
│   │   │   ├── user.py
│   │   │   ├── patient.py
│   │   │   ├── encounter.py
│   │   │   ├── vital_signs.py
│   │   │   └── audit_log.py
│   │   ├── routes/         # API routes
│   │   │   ├── auth.py
│   │   │   ├── patients.py
│   │   │   ├── encounters.py
│   │   │   ├── users.py
│   │   │   ├── ai.py
│   │   │   └── audit.py
│   │   ├── ai/             # AI modules
│   │   │   ├── intelligent_search.py
│   │   │   └── risk_assessment.py
│   │   └── utils/          # Utilities
│   │       └── seed.py
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── contexts/       # React contexts
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── .env
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- MySQL 8.0+

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a MySQL database:
```sql
CREATE DATABASE medibora_ehr;
```

6. Update the database configuration in `.env`:
```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/medibora_ehr
```

7. Run the application:
```bash
python run.py
```

The backend will start on `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Update the API URL in `.env` if needed:
```
VITE_API_URL=http://localhost:5000/api
```

4. Start the development server:
```bash
npm run dev
```

The frontend will start on `http://localhost:5173`

## Default Login Credentials

- **Admin**: username: `admin`, password: `admin`
- **Doctor**: username: `doctor`, password: `doctor`
- **Nurse**: username: `nurse`, password: `nurse`
- **Records Officer**: username: `records`, password: `records`

## VS Code Integration

### Recommended Extensions
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Thunder Client (for API testing)

### Debugging Configuration

Create `.vscode/launch.json` for backend debugging:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Flask Backend",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "run.py",
        "FLASK_ENV": "development"
      },
      "args": ["run", "--no-debugger"],
      "jinja": true
    }
  ]
}
```

## API Documentation

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/change-password` - Change password

### Patients
- `GET /api/patients/` - List all patients
- `GET /api/patients/:id` - Get patient details
- `POST /api/patients/` - Create new patient
- `PUT /api/patients/:id` - Update patient
- `DELETE /api/patients/:id` - Deactivate patient
- `GET /api/patients/search` - Search patients

### Encounters
- `GET /api/encounters/` - List all encounters
- `GET /api/encounters/:id` - Get encounter details
- `POST /api/encounters/` - Create new encounter
- `PUT /api/encounters/:id` - Update encounter
- `GET /api/encounters/patient/:id/history` - Get patient history

### AI Features
- `GET /api/ai/search` - Intelligent search
- `GET /api/ai/risk-assessment/:patientId` - Get risk assessment
- `GET /api/ai/alerts` - Get critical alerts
- `POST /api/ai/suggestions/diagnosis` - Get diagnosis suggestions
- `GET /api/ai/dashboard/stats` - Get dashboard statistics

## Chapter 3 Implementation Summary

This implementation covers the methodology outlined in Chapter 3 of the project proposal:

### 3.1.4 System Design and Architecture
- **Three-tier architecture**: Presentation layer (React), Application layer (Flask), Data layer (MySQL)
- **RESTful API design** for seamless communication
- **Security by design**: RBAC, authentication, audit logging

### 3.1.5 System Development
- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: React with TypeScript and Tailwind CSS
- **AI Components**: Python with scikit-learn for risk assessment and intelligent search

### 3.1.6 Test and Evaluation
- Unit testing for individual modules
- Integration testing for component interactions
- User acceptance testing based on TAM (Technology Acceptance Model)

## License

This project is developed for academic purposes at Machakos University.

## Author

**Barbra Wendy Nyakundi**  
Registration Number: J17-1384-2022  
Computer Science Major  
Supervisor: Mr. Benard Kiage

## Acknowledgements

- Machakos University, School of Engineering and Technology
- Department of Computing and Information Technology
- Healthcare professionals in Kenya for their inspiration
