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

            if not email or not password:
                flash('Email and password are required', 'error')
                return render_template('Login.html')


            user = User.query.filter_by(email=email).first()

            if not user:
                flash('User not found', 'error')
                return render_template('Login.html')

            try:
                password_correct = user.check_password(password)
            except ValueError:
                password_correct = user.password == password

                if password_correct:
                    user.set_password(password)
                    db.session.commit()

            if password_correct:
                session['access_token'] = create_access_token(identity=user.user_id)
                session['account_id'] = user.user_id
                session['account_type'] = 'mto'
                return redirect(url_for('homepage'))

            flash('Invalid email or password', 'error')
            return render_template('Login.html')

        return render_template('Login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))