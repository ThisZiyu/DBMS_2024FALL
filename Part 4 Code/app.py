from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import json
import random
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import joblib
import numpy as np

app = Flask(__name__)
# Set a secret key for session
app.secret_key = 'This_is_a_secret_key'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///insurance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the trained model
try:
    model = joblib.load('health_risk_model.pkl')
except:
    print("Error loading model. Make sure the model file exists.")
    model = None

# Base premium rates by age group
BASE_PREMIUMS = {
    '18-30': 100,
    '31-45': 150,
    '46-60': 200,
    '61+': 250,
    '<18': 100  # Assuming same as 18-30 for minors
}

# Risk adjustment factors
RISK_FACTORS = {
    'Low Risk': 0.8,
    'Medium Risk': 1.0,
    'High Risk': 1.5
}

# Insurance plans structure with percentage adjustments from base premium
INSURANCE_PLANS = {
    'basic': {
        'name': 'Basic Plan',
        'coverage_factor': 1.0,  # Base premium
        'deductible': 2000,
        'primary_care_visit': 30,
        'generic_drugs': 15
    },
    'standard': {
        'name': 'Standard Plan',
        'coverage_factor': 1.5,  # 50% more than base
        'deductible': 1000,
        'primary_care_visit': 20,
        'generic_drugs': 10
    },
    'premium': {
        'name': 'Premium Plan',
        'coverage_factor': 2.0,  # Double the base
        'deductible': 500,
        'primary_care_visit': 10,
        'generic_drugs': 5
    }
}


def predict_risk(health_data):
    """
    Predict risk level based on health factors using the loaded model
    """
    if model is None:
        return "Medium Risk"  # Default if model isn't loaded

    try:
        # Convert input data to model format
        input_data = pd.DataFrame([health_data])
        prediction = model.predict(input_data)[0]
        return prediction
    except Exception as e:
        print(f"Prediction error: {e}")
        return "Medium Risk"


def calculate_premium(health_data):
    """Calculate insurance premium based on health data and risk level"""
    try:
        # Get base premium from age group
        base_premium = BASE_PREMIUMS[health_data['age_group']]

        # Get risk level and corresponding factor
        risk_level = predict_risk(health_data)
        risk_factor = RISK_FACTORS[risk_level]

        # Calculate adjusted base premium
        adjusted_premium = base_premium * risk_factor

        # Calculate premiums for different plans
        premiums = {}
        for plan_id, plan in INSURANCE_PLANS.items():
            plan_premium = adjusted_premium * plan['coverage_factor']
            premiums[f"{plan_id}_premium"] = round(plan_premium, 2)

        premiums['risk_level'] = risk_level
        return premiums

    except Exception as e:
        print(f"Premium calculation error: {e}")
        return None


@app.route('/')
def home():
    """Render the home page with the quote form"""
    return render_template('base.html')


@app.route('/calculate_quote', methods=['POST'])
def calculate_quote():
    """Process the quote form and calculate insurance options"""
    if request.method == 'POST':
        # Collect all health data from form
        health_data = {
            'age_group': request.form.get('age_group'),
            'gender': request.form.get('gender'),
            'race': request.form.get('race'),
            'smoking': request.form.get('smoking'),
            'alcohol': request.form.get('alcohol'),
            'education': request.form.get('education'),
            'bmi_category': request.form.get('bmi_category'),
            'exercise': request.form.get('exercise'),
            'income': request.form.get('income'),
            'disease': request.form.get('disease')
        }

        # Store in session for later use
        session['health_data'] = health_data

        # Calculate premiums
        premium_data = calculate_premium(health_data)

        if premium_data:
            return render_template(
                'quote_results.html',
                health_data=health_data,
                basic_premium=premium_data['basic_premium'],
                standard_premium=premium_data['standard_premium'],
                premium_premium=premium_data['premium_premium'],
                risk_level=premium_data['risk_level']
            )

        flash('Error calculating quote. Please try again.', 'error')
        return redirect(url_for('home'))

    return redirect(url_for('home'))


@app.route('/get_current_rates')
def get_current_rates():
    try:
        health_data = session.get('health_data')
        if not health_data:
            return jsonify({'error': 'No quote data found'}), 404

        # Calculate new premiums
        premium_data = calculate_premium(health_data)

        # Add small random market fluctuation (-2% to +2%)
        market_fluctuation = random.uniform(-0.02, 0.02)
        premium_data['basic_premium'] *= (1 + market_fluctuation)
        premium_data['standard_premium'] *= (1 + market_fluctuation)
        premium_data['premium_premium'] *= (1 + market_fluctuation)

        # Round all premium values
        for key in ['basic_premium', 'standard_premium', 'premium_premium']:
            premium_data[key] = round(premium_data[key], 2)

        premium_data['last-update-time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(premium_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/select_plan/<plan_id>')
def select_plan(plan_id):
    """Handle plan selection"""
    if plan_id in INSURANCE_PLANS:
        # Store selected plan and health data in database
        health_data = session.get('health_data')
        premium_data = calculate_premium(health_data)

        # Here you would typically store the data in a database
        # For now, we'll just store in session
        session['selected_plan'] = {
            'plan_id': plan_id,
            'health_data': health_data,
            'premium': premium_data[f"{plan_id}_premium"],
            'risk_level': premium_data['risk_level'],
            'selection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        flash('Plan selected successfully!', 'success')
        return redirect(url_for('application_form'))
    return redirect(url_for('home'))


class Claim(db.Model):
    __tablename__ = 'claim'

    id = db.Column(db.Integer, primary_key=True)
    claim_number = db.Column(db.String(20), unique=True, nullable=False)

    # Patient Information
    patient_name = db.Column(db.String(100), nullable=False)
    policy_number = db.Column(db.String(50), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    service_type = db.Column(db.String(50), nullable=False)

    # Provider Information
    provider_name = db.Column(db.String(100), nullable=False)
    provider_address = db.Column(db.String(200), nullable=False)

    # Claim Details
    amount = db.Column(db.Float, nullable=False)

    # Status and Timestamps
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'claim_number': self.claim_number,
            'patient_name': self.patient_name,
            'service_date': self.service_date.strftime('%Y-%m-%d'),
            'service_type': self.service_type,
            'amount': self.amount,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# File Claim routes remain unchanged
@app.route('/file-claim')
def file_claim():
    return render_template('file_claim.html')


@app.route('/submit_claim', methods=['POST'])
def submit_claim():
    try:
        # Generate unique claim number
        claim_number = f"CLM{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"

        # Create new claim
        new_claim = Claim(
            claim_number=claim_number,
            patient_name=request.form['patient_name'],
            policy_number=request.form['policy_number'],
            service_date=datetime.strptime(request.form['service_date'], '%Y-%m-%d'),
            service_type=request.form['service_type'],
            provider_name=request.form['provider_name'],
            provider_address=request.form['provider_address'],
            amount=float(request.form['amount']),
        )

        # Save to database
        db.session.add(new_claim)
        db.session.commit()

        flash('Claim submitted successfully! Your claim number is: ' + claim_number, 'success')
        return redirect(url_for('claim_status', claim_id=new_claim.id))

    except Exception as e:
        db.session.rollback()
        return redirect(url_for('file_claim'))

@app.route('/claim_status/<int:claim_id>')
def claim_status(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    return render_template('claim_status.html', claim=claim)

@app.route('/my-claims')
def my_claims():
    claims = Claim.query.order_by(Claim.created_at.desc()).all()
    return render_template('my_claims.html', claims=claims)

# API endpoint for claim status
@app.route('/api/claim/<claim_number>')
def get_claim_api(claim_number):
    claim = Claim.query.filter_by(claim_number=claim_number).first()
    if claim:
        return jsonify(claim.to_dict())
    return jsonify({'error': 'Claim not found'}), 404

def init_db():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    init_db()  # Initialize databas
    app.run(debug=True)