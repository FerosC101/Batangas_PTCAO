import bcrypt
from flask import render_template, request, redirect, url_for, session, flash
from flask_jwt_extended import create_access_token, set_access_cookies
from extension import db
from model import User
from enum import Enum

class AccountStatus(Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    MAINTENANCE = 'maintenance'

def init_auth_routes(app):
    @app.route('/')
    def home():
        return render_template('Login.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '').strip()

            if not email or not password:
                flash('Email and password are required', 'error')
                return render_template('Login.html')

            user = User.query.filter_by(email=email).first()

            if not user:
                flash('User not found', 'error')
                return render_template('Login.html')

            if not user.is_active:
                flash('Your account is not yet activated', 'error')
                return render_template('Login.html')

            if user.check_password(password):
                # Convert user_id to string to ensure proper JWT token creation
                access_token = create_access_token(identity=str(user.user_id))

                # Store info in session if needed
                session['account_id'] = user.user_id
                session['account_type'] = 'mto'

                # Create response with redirect
                response = redirect(url_for('dashboard.mto_dashboard'))

                # Set the JWT token as a cookie
                set_access_cookies(response, access_token)

                return response

            flash('Invalid email or password', 'error')
            return render_template('Login.html')

        return render_template('Login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))
