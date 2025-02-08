import bcrypt
from flask import render_template, request, redirect, url_for, session, flash
from flask_jwt_extended import create_access_token
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import User
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
            user_email = request.form.get('email', '').strip().lower()  # Normalize email
            password = request.form.get('password', '').strip()

            if not user_email or not password:
                flash('Email and password are required', 'error')
                return render_template('Login.html')

            print(f"🔍 Checking for user with email: {user_email}")  # Debugging output

            # Check if any users exist before querying
            with app.app_context():
                users_exist = User.query.count()
                if users_exist == 0:
                    print("🚨 No users found in the database! Check if the database is populated.")
                    flash('No users found in the database', 'error')
                    return render_template('Login.html')

            # Retrieve the user and check if found
            print(User.query.filter_by(user_email=user_email))
            user = User.query.filter_by(user_email=user_email).first()

            if not user:
                flash('User not found', 'error')
                print(f"🚨 No user found with email: {user_email}")  # Debugging output
                return render_template('Login.html')

            print(f"✅ Found user: {user.user_email}, Account Status: {user.account_status}")

            # Fix Enum Comparison (ensure correct attribute usage)
            if user.account_status in [AccountStatus.SUSPENDED.value, AccountStatus.MAINTENANCE.value]:
                flash(f'Account is {user.account_status}. Contact support.', 'error')
                print(f"🚨 Account is {user.account_status}, login blocked.")
                return render_template('Login.html')

            # Check password hash correctly
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                print("✅ Password check passed.")
                user.failed_login_attempts = 0
                db.session.commit()

                access_token = create_access_token(identity=user.user_id)
                session['access_token'] = access_token
                session['account_id'] = user.user_id

                return redirect(url_for('homepage'))
            else:
                print("🚨 Invalid password attempt.")
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.account_status = AccountStatus.SUSPENDED.value
                    db.session.commit()
                    flash('Too many failed attempts. Account locked.', 'error')
                    return render_template('Login.html')

                db.session.commit()
                flash('Invalid email or password', 'error')
                return render_template('Login.html')

        return render_template('Login.html')

    @app.route('/logout')
    def logout():
        session.pop('access_token', None)
        session.pop('account_id', None)
        return redirect(url_for('login'))