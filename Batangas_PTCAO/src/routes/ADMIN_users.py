from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from Batangas_PTCAO.src.model import User, db
from Batangas_PTCAO.src.extension import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

admin_users_bp = Blueprint('admin_users', __name__)


@admin_users_bp.route('/admin/users')
@jwt_required()
def admin_users():
    current_user_id = get_jwt_identity()
    admin_user = User.query.get(current_user_id)

    users = User.query.filter_by(is_active=True).all()
    suspended_users = User.query.filter_by(is_active=False).all()

    return render_template('ADMIN_users.html',
                           active_users=users,
                           suspended_users=suspended_users)


@admin_users_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user_id': user.user_id,
        'full_name': user.full_name,
        'municipality': user.municipality,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active
    })


@admin_users_bp.route('/admin/users', methods=['POST'])
@jwt_required()
def create_user():
    data = request.form
    try:
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400

        new_user = User(
            full_name=data['full_name'],
            municipality=data['municipality'],
            id_number=data['id_number'],
            designation=data['designation'],
            email=data['email'],
            gender=data['gender'],
            birthday=datetime.strptime(data['birthday'], '%Y-%m-%d').date(),
            username=data['username'],
            is_active=data.get('is_active', 'false').lower() == 'true'
        )
        new_user.set_password(data['password'])

        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_users_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.form

    try:
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'municipality' in data:
            user.municipality = data['municipality']
        if 'email' in data:
            if User.query.filter(User.email == data['email'], User.user_id != user_id).first():
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        if 'username' in data:
            if User.query.filter(User.username == data['username'], User.user_id != user_id).first():
                return jsonify({'error': 'Username already in use'}), 400
            user.username = data['username']
        if 'is_active' in data:
            user.is_active = data['is_active'].lower() == 'true'
        if 'password' in data and data['password']:
            user.set_password(data['password'])

        db.session.commit()
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_users_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_users_bp.route('/admin/users/export', methods=['GET'])
@jwt_required()
def export_users():
    users = User.query.all()
    user_list = []

    for user in users:
        user_list.append({
            'user_id': user.user_id,
            'full_name': user.full_name,
            'municipality': user.municipality,
            'username': user.username,
            'email': user.email,
            'status': 'Active' if user.is_active else 'Inactive',
            'created_at': user.created_at.strftime('%Y-%m-%d')
        })

    return jsonify(user_list)