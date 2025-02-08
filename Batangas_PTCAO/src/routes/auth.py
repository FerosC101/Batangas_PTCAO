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
            user_email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

            if not user_email or not password:
                flash('Email and password are required', 'error')
                return render_template('Login.html')

            user = User.query.filter_by(user_email=user_email).first()

            if not user:
                flash('User not found', 'error')
                return render_template('Login.html')

            if user.account_status in [AccountStatus.SUSPENDED.value, AccountStatus.MAINTENANCE.value]:
                flash(f'Account is {user.account_status}. Contact support.', 'error')
                return render_template('Login.html')

            # 🛠️ Fix: Ensure bcrypt correctly checks the password
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                user.failed_login_attempts = 0
                db.session.commit()

                access_token = create_access_token(identity=user.user_id)
                session['access_token'] = access_token
                session['account_id'] = user.user_id

                return redirect(url_for('dashboard'))
            else:
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
