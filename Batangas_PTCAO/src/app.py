import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import User, BusinessRegistration, Room, EventFacility, SpecialServices, RegistrationStep, Amenity
from Batangas_PTCAO.src.config import Config

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from enum import Enum

class AccountStatus(Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    MAINTENANCE = 'maintenance'

app = Flask(__name__, template_folder='routes', static_folder='static')
app.config.from_object(Config)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')

jwt = JWTManager(app)
db.init_app(app)

@app.route('/')
def home():
    return render_template('Login.html')

# needs test case for incorrect password input
# need to add file handling if wrong password input
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Server-side input validation
        user_email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not user_email or not password:
            flash('Email and password are required', 'error')
            return render_template('Login.html')

        user = User.query.filter_by(user_email=user_email).first()

        if not user:
            flash('User not found', 'error')
            return render_template('Login.html')

        if user.account_status == AccountStatus.SUSPENDED:
            flash('Account is suspended. Contact support.', 'error')
            return render_template('Login.html')

        if user.account_status == AccountStatus.MAINTENANCE:
            flash('System under maintenance', 'error')
            return render_template('Login.html')

        if user.check_password(password):
            # Reset failed attempts
            user.failed_login_attempts = 0
            db.session.commit()

            # Generate JWT token
            access_token = create_access_token(identity=user.user_id)
            session['access_token'] = access_token
            session['account_id'] = user.user_id

            return redirect(url_for('dashboard'))
        else:
            # Increment failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.account_status = AccountStatus.SUSPENDED
                db.session.commit()
                flash('Too many failed attempts. Account locked.', 'error')
                return render_template('Login.html')

            db.session.commit()
            flash('Invalid email or password', 'error')
            return render_template('Login.html')

    return render_template('Login.html')
# Ready for testing
#
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('business_registration'))

    session['registration_step'] = RegistrationStep.BUSINESS_DETAILS
    session['registration_data'] = {}
    return render_template('Registration.html')


@app.route('/login_credentials', methods=['GET', 'POST'])
def login_credentials():
    if 'registration_data' not in session or 'services' not in session['registration_data']:
        flash('Please complete special services first', 'error')
        return redirect(url_for('special_services'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')

        if not username or not password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('LoginCredentials.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('LoginCredentials.html')

        if User.query.filter_by(user_email=username).first():
            flash('Username already exists', 'error')
            return render_template('LoginCredentials.html')

        try:
            # Start database transaction
            db.session.begin_nested()

            # Create user
            new_user = User(user_email=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush()  # Get the user_id

            # Create business registration
            business_data = session['registration_data']['business']
            new_business = BusinessRegistration(
                account_id=new_user.user_id,
                business_registration_no=business_data['business_registration_no'],
                business_name=business_data['business_name'],
                official_contact_no=business_data['official_contact_no'],
                business_address=business_data['business_address'],
                taxpayer_name=business_data['taxpayer_name'],
                total_employees=business_data['total_employees'],
                total_rooms=business_data['total_rooms'],
                total_beds=business_data['total_beds']
            )
            db.session.add(new_business)
            db.session.flush()  # Get the business_id

            # Create special services
            services_data = session['registration_data']['services']
            new_services = SpecialServices(
                business_id=new_business.business_id,
                accreditation_type=services_data['accreditation'],
                ae_classification=services_data['classification']
            )
            db.session.add(new_services)

            # Add rooms
            for room_data in services_data['rooms']:
                new_room = Room(
                    business_id=new_business.business_id,
                    room_type=room_data['type'],
                    total_number=room_data['number'],
                    capacity=room_data['capacity']
                )
                db.session.add(new_room)

            # Add event facilities
            for facility_data in services_data['facilities']:
                new_facility = EventFacility(
                    business_id=new_business.business_id,
                    room_name=facility_data['name'],
                    capacity=facility_data['capacity'],
                    facilities=facility_data['amenities']
                )
                db.session.add(new_facility)

            # Commit all changes
            db.session.commit()

            # Clear registration data
            session.pop('registration_data', None)
            session.pop('registration_step', None)

            return render_template('Success_Template.html')

        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")  # For debugging
            flash('Registration failed. Please try again.', 'error')
            return render_template('LoginCredentials.html')

    return render_template('LoginCredentials.html')
#Tested and Running
@app.route('/business_registration', methods=['GET', 'POST'])
def business_registration():
    if request.method == 'POST':
        business_data = {
            'business_registration_no': request.form.get('business-registration'),
            'business_name': request.form.get('business-name'),
            'official_contact_no': request.form.get('official-contact'),
            'business_address': request.form.get('business-address'),
            'taxpayer_name': request.form.get('taxpayer-name'),
            'total_employees': request.form.get('total-employees'),
            'total_rooms': request.form.get('total-rooms'),
            'total_beds': request.form.get('total-beds')
        }

        if not all(business_data.values()):
            flash('All fields are required', 'error')
            return render_template('Registration.html')

        try:
            # Convert numeric fields
            business_data['total_employees'] = int(business_data['total_employees'])
            business_data['total_rooms'] = int(business_data['total_rooms'])
            business_data['total_beds'] = int(business_data['total_beds'])
        except ValueError:
            flash('Invalid numeric values provided', 'error')
            return render_template('Registration.html')

        session['registration_data'] = session.get('registration_data', {})
        session['registration_data']['business'] = business_data
        session['registration_step'] = RegistrationStep.SPECIAL_SERVICES

        return redirect(url_for('special_services'))

    return render_template('Registration.html')

#Tested and Running
@app.route('/special_services', methods=['GET', 'POST'])
def special_services():
    if 'registration_data' not in session or 'business' not in session['registration_data']:
        flash('Please complete business registration first', 'error')
        return redirect(url_for('business_registration'))

    if request.method == 'POST':
        # Process rooms data
        rooms_data = []
        room_types = request.form.getlist('room_type[]')
        room_numbers = request.form.getlist('room_number[]')
        room_capacities = request.form.getlist('room_capacity[]')

        for i in range(len(room_types)):
            if room_types[i] and room_numbers[i] and room_capacities[i]:
                rooms_data.append({
                    'type': room_types[i],
                    'number': int(room_numbers[i]),
                    'capacity': int(room_capacities[i])
                })

        # Process event facilities data
        facilities_data = []
        facility_names = request.form.getlist('facility_name[]')
        facility_capacities = request.form.getlist('facility_capacity[]')
        facility_amenities = request.form.getlist('facility_amenities[]')

        for i in range(len(facility_names)):
            if facility_names[i] and facility_capacities[i] and facility_amenities[i]:
                facilities_data.append({
                    'name': facility_names[i],
                    'capacity': int(facility_capacities[i]),
                    'amenities': facility_amenities[i]
                })

        services_data = {
            'accreditation': request.form.get('accreditation'),
            'classification': request.form.get('classification'),
            'rooms': rooms_data,
            'facilities': facilities_data,
            'other_services': request.form.get('services')
        }

        if not services_data['accreditation'] or not services_data['classification']:
            flash('Accreditation and classification are required', 'error')
            return render_template('Special_Service.html')

        session['registration_data']['services'] = services_data
        session['registration_step'] = RegistrationStep.LOGIN_CREDENTIALS

        return redirect(url_for('login_credentials'))

    return render_template('Special_Service.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/static/<path:filename>')
def serve_static_file(filename):
    if allowed_file(filename):
        return send_from_directory(os.path.join(app.root_path, 'static'), filename)
    else:
        return 'File type not allowed', 400

def allowed_file(filename):
    ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True)