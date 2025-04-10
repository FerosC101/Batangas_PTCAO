import bcrypt
from flask import render_template, request, redirect, url_for, session, flash
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import User # Assuming MTOUser is added to model.py
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
            user_type = request.form.get('user-type', 'standard')  # Add this field to Login.html

            if not email or not password:
                flash('Email and password are required', 'error')
                return render_template('Login.html')

            # Check if login is for MTO user
            if user_type == 'mto':
                # For MTO users, email field might actually contain username
                mto_user = User.query.filter(
                    (User.email == email) | (User.username == email)
                ).first()

                if not mto_user:
                    flash('MTO user not found', 'error')
                    return render_template('Login.html')

                if not mto_user.is_active:
                    flash('Your account is pending approval. Please contact the administrator.', 'warning')
                    return render_template('Login.html')

                if check_password_hash(mto_user.password, password):
                    session['access_token'] = create_access_token(identity=f"mto_{mto_user.id}")
                    session['account_id'] = mto_user.id
                    session['account_type'] = 'mto'
                    session['municipality'] = mto_user.municipality
                    return redirect(url_for('mto.dashboard'))  # Redirect to MTO dashboard

                flash('Invalid credentials', 'error')
                return render_template('Login.html')

            # Standard user login (existing logic)
            user = User.query.filter_by(user_email=email).first()

            if not user:
                flash('User not found', 'error')
                return render_template('Login.html')

            if user.account_status in [AccountStatus.SUSPENDED.value, AccountStatus.MAINTENANCE.value]:
                flash(f'Account is {user.account_status}. Contact support.', 'error')
                return render_template('Login.html')

            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                user.failed_login_attempts = 0
                db.session.commit()

                session['access_token'] = create_access_token(identity=user.user_id)
                session['account_id'] = user.user_id
                session['account_type'] = 'standard'
                return redirect(url_for('homepage'))

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
        session.clear()
        return redirect(url_for('login'))