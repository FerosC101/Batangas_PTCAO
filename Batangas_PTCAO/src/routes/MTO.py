from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import User
from datetime import datetime

mto_bp = Blueprint('mto', __name__, url_prefix='/mto')


def init_mto_routes(app):
    app.register_blueprint(mto_bp)


@mto_bp.route('/register', methods=['GET', 'POST'])
def mto_registration():
    if request.method == 'POST':
        try:
            # Get and validate form data
            required_fields = [
                'full-name', 'municipality', 'id-number', 'designation',
                'email', 'gender', 'birthday', 'username',
                'password', 'password-confirmation'
            ]

            form_data = {field: request.form.get(field, '').strip() for field in required_fields}

            # Check for empty fields
            if not all(form_data.values()):
                flash('All fields are required', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Validate password match
            if form_data['password'] != form_data['password-confirmation']:
                flash('Passwords do not match', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Check for existing username
            if User.query.filter_by(username=form_data['username']).first():
                flash('Username already exists. Please choose another one.', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Check for existing email
            if User.query.filter_by(email=form_data['email'].lower()).first():
                flash('Email already registered', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Check for existing ID number
            if User.query.filter_by(id_number=form_data['id-number']).first():
                flash('ID number already registered', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Parse birthday
            try:
                birthday = datetime.strptime(form_data['birthday'], '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for birthday', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Create new user
            new_user = User(
                full_name=form_data['full-name'],
                municipality=form_data['municipality'],
                id_number=form_data['id-number'],
                designation=form_data['designation'],
                email=form_data['email'].lower(),
                gender=form_data['gender'],
                birthday=birthday,
                username=form_data['username'],
                is_active=False  # Requires admin approval
            )

            # Set password using bcrypt
            new_user.set_password(form_data['password'])

            # Save to database
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! Your account will be activated after review.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'error')
            return redirect(url_for('mto.mto_registration'))

    return render_template('Register.html')

@mto_bp.route('/dashboard')
def dashboard():
    if 'account_id' not in session or session.get('account_type') != 'mto':
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))

    return render_template('MTO_Dashboard.html')