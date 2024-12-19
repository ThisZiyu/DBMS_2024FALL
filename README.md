# Healthcare Plus Insurance System
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1.4+-orange.svg)](https://www.sqlalchemy.org/)

## Overview
Healthcare Plus Insurance System is a web-based application for managing health insurance claims and quotes. It provides functionality for users to get insurance quotes based on their health factors and submit insurance claims.

## Features
- **Insurance Quote Calculator**
  - Risk assessment based on health factors
  - Real-time premium calculation
  - Multiple plan options (Basic, Standard, Premium)

- **Claims Management**
  - Submit new claims
  - Track claim status
  - View claim history
  - Real-time status updates

## Technology Stack
- Backend: Python Flask
- Database: SQLite with SQLAlchemy
- Frontend: HTML, Tailwind CSS
- Additional Libraries: Flask-SQLAlchemy

## Installation

1. Initialize the database:
```bash
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

2. Run the application:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Project Structure
```
healthcare-plus/
│
├── app/
│   ├── app.py
│   └── templates/
│       ├── base.html
│       ├── file_claim.html
│       ├── file_claim.html
│       ├── claim_status.html
│       └── my_claims.html
│
├── instance/
│   └── insurance.db
│
└── README.md
```

## Database Schema

### Claims Table
- claim_number (unique identifier)
- patient_name
- policy_number
- service_date
- service_type
- provider_name
- provider_address
- amount
- status
- created_at
- updated_at

## API Endpoints

### Insurance Quote
- `GET /`: Home page with quote calculator
- `POST /calculate_quote`: Calculate insurance quote
- `GET /get_current_rates`: Get real-time insurance rates

### Claims Management
- `GET /file-claim`: Claim submission form
- `POST /submit_claim`: Submit new claim
- `GET /claim_status/<claim_id>`: View claim status
- `GET /my-claims`: View all claims

## Requirements
```txt
Flask==2.0.1
Flask-SQLAlchemy==2.5.1
SQLAlchemy==1.4.23
python-dotenv==0.19.0
Werkzeug==2.0.1
```