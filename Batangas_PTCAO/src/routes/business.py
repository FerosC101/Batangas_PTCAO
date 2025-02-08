from flask import render_template, request, redirect, url_for, session, flash
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import User, BusinessRegistration, Room, EventFacility, SpecialServices, Amenity
from Batangas_PTCAO.src.model import RegistrationStep

def init_business_routes(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            return redirect(url_for('business_registration'))

        session['registration_step'] = RegistrationStep.BUSINESS_DETAILS
        session['registration_data'] = {}
        return render_template('Registration.html')

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
                db.session.begin_nested()

                new_user = User(user_email=username)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.flush()

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
                db.session.flush()

                services_data = session['registration_data']['services']
                new_services = SpecialServices(
                    business_id=new_business.business_id,
                    accreditation_type=services_data['accreditation'],
                    ae_classification=services_data['classification']
                )
                db.session.add(new_services)

                for room_data in services_data['rooms']:
                    new_room = Room(
                        business_id=new_business.business_id,
                        room_type=room_data['type'],
                        total_number=room_data['number'],
                        capacity=room_data['capacity'],
                        price=0.0
                    )
                    db.session.add(new_room)

                for facility_data in services_data['facilities']:
                    new_facility = EventFacility(
                        business_id=new_business.business_id,
                        room_name=facility_data['name'],
                        capacity=facility_data['capacity'],
                        facilities=facility_data['amenities']
                    )
                    db.session.add(new_facility)

                db.session.commit()
                session.pop('registration_data', None)
                session.pop('registration_step', None)

                return render_template('Success_Template.html')

            except Exception as e:
                db.session.rollback()
                print(f"Registration error: {str(e)}")
                flash('Registration failed. Please try again.', 'error')
                return render_template('LoginCredentials.html')

        return render_template('LoginCredentials.html')