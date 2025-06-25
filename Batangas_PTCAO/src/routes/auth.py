import bcrypt
from flask import render_template, request, redirect, url_for, session, flash
from flask_jwt_extended import create_access_token, set_access_cookies
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import User
from enum import Enum


class AccountStatus(Enum):
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    MAINTENANCE = 'maintenance'


def init_auth_routes(app):
    # Built-in admin account credentials
    ADMIN_EMAIL = "admin@ptcao.gov.ph"
    ADMIN_PASSWORD = "Admin@1234"

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

            # Check for built-in admin account
            if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                # Create a dummy admin user object
                admin_user = type('obj', (object,), {
                    'user_id': 'admin',
                    'is_active': True,
                    'check_password': lambda x: x == ADMIN_PASSWORD
                })

                access_token = create_access_token(identity="admin")
                session['account_id'] = "admin"
                session['account_type'] = "admin"

                response = redirect(url_for('admin_dashboard'))  # Make sure you have this route defined
                set_access_cookies(response, access_token)
                return response

            user = User.query.filter_by(email=email).first()

            if not user:
                flash('User not found', 'error')
                return render_template('Login.html')

            if not user.is_active:
                flash('Your account is not yet activated', 'error')
                return render_template('Login.html')

            if user.check_password(password):
                access_token = create_access_token(identity=str(user.user_id))
                session['account_id'] = user.user_id
                session['account_type'] = 'mto'

                response = redirect(url_for('dashboard.mto_dashboard'))
                set_access_cookies(response, access_token)
                return response

            flash('Invalid email or password', 'error')
            return render_template('Login.html')

        return render_template('Login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))