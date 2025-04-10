from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import User  # Assuming you'll add this model to your model.py

mto_bp = Blueprint('mto', __name__, url_prefix='/mto')


@mto_bp.route('/register', methods=['GET', 'POST'])
def mto_registration():
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full-name')
        municipality = request.form.get('municipality')
        id_number = request.form.get('id-number')
        designation = request.form.get('designation')
        email = request.form.get('email')
        gender = request.form.get('gender')
        birthday = request.form.get('birthday')
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirmation = request.form.get('password-confirmation')

        # Validate data
        if not all([full_name, municipality, id_number, designation, email, gender, birthday, username, password,
                    password_confirmation]):
            flash('All fields are required', 'error')
            return redirect(url_for('mto.mto_registration'))

        # Check if passwords match
        if password != password_confirmation:
            flash('Passwords do not match', 'error')
            return redirect(url_for('mto.mto_registration'))

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another one.', 'error')
            return redirect(url_for('mto.mto_registration'))

        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered', 'error')
            return redirect(url_for('mto.mto_registration'))

        # Create new user
        new_user = User(
            full_name=full_name,
            municipality=municipality,
            id_number=id_number,
            designation=designation,
            email=email,
            gender=gender,
            birthday=birthday,
            username=username,
            password=generate_password_hash(password),
            is_active=False  # Requires admin approval
        )

        try:
            # Add user to database
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Your account will be activated after review.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'error')

    # GET request - render the registration form
    return render_template('Register.html')


@mto_bp.route('/dashboard')
def dashboard():
    if 'account_id' not in session or session.get('account_type') != 'mto':
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))

    return render_template('Dashboard.html')


def init_mto_routes(app):
    app.register_blueprint(mto_bp)