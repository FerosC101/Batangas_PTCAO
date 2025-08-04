from flask import render_template, request, jsonify, redirect, url_for, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from extension import db
from model import User
from sqlalchemy import or_
from datetime import datetime


def init_admin_users_routes(app):
    admin_users_bp = Blueprint('admin_users', __name__)

    @admin_users_bp.route('/users')
    @jwt_required()
    def admin_users():
        active_users = User.query.filter(
            or_(User.is_archived == False, User.is_archived == None),
            User.is_active == True
        ).all()

        suspended_users = User.query.filter(
            or_(User.is_archived == False, User.is_archived == None),
            User.is_active == False
        ).all()

        archived_users = User.query.filter_by(is_archived=True).all()

        return render_template('ADMIN_User.html',
                               active_users=active_users,
                               suspended_users=suspended_users,
                               archived_users=archived_users)

    @admin_users_bp.route('/users/<int:user_id>', methods=['GET'])
    @jwt_required()
    def get_user(user_id):
        user = User.query.get_or_404(user_id)
        return jsonify({
            'user_id': user.user_id,
            'full_name': user.full_name,
            'municipality': user.municipality,
            'id_number': user.id_number,
            'designation': user.designation,
            'email': user.email,
            'gender': user.gender,
            'birthday': user.birthday.strftime('%Y-%m-%d'),
            'username': user.username,
            'is_active': user.is_active,
            'is_archived': getattr(user, 'is_archived', False)
        })

    @admin_users_bp.route('/users', methods=['POST'])
    @jwt_required()
    def create_user():
        data = request.form

        # Validate required fields
        required_fields = ['full_name', 'email', 'username', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400

        # Create new user
        new_user = User(
            full_name=data['full_name'],
            municipality=data.get('municipality', ''),
            id_number=data.get('id_number', ''),
            designation=data.get('designation', ''),
            email=data['email'],
            gender=data.get('gender', ''),
            birthday=datetime.strptime(data['birthday'], '%Y-%m-%d').date() if 'birthday' in data else None,
            username=data['username'],
            is_active=data.get('is_active', 'false').lower() == 'true',
            is_archived=False  # New users are never archived
        )
        new_user.set_password(data['password'])

        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User created successfully'}), 201

    @admin_users_bp.route('/users/<int:user_id>/status', methods=['PUT'])
    @jwt_required()
    def update_user_status(user_id):
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        if not data or 'action' not in data:
            return jsonify({'error': 'Missing action'}), 400

        action = data['action']

        if action == 'suspend':
            user.is_active = False
            if hasattr(user, 'is_archived'):
                user.is_archived = False
        elif action == 'activate':
            user.is_active = True
            if hasattr(user, 'is_archived'):
                user.is_archived = False
        elif action == 'archive' and hasattr(user, 'is_archived'):
            user.is_active = False
            user.is_archived = True
        elif action == 'restore' and hasattr(user, 'is_archived'):
            user.is_archived = False
        else:
            return jsonify({'error': 'Invalid action'}), 400

        db.session.commit()
        return jsonify({'message': f'User status updated: {action}'}), 200

    @admin_users_bp.route('/users/<int:user_id>', methods=['DELETE'])
    @jwt_required()
    def delete_user(user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200

    app.register_blueprint(admin_users_bp, url_prefix='/admin')