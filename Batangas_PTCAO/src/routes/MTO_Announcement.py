from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import Announcement, User
import os
from werkzeug.utils import secure_filename

announcement_bp = Blueprint('announcement', __name__, url_prefix='/mto/announcements')

# Allowed file extensions for announcement images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def init_mto_announcement_routes(app):
    """Initialize MTO Announcement routes"""
    app.register_blueprint(announcement_bp)
    # Configure upload folder for announcement images
    app.config['ANNOUNCEMENT_UPLOAD_FOLDER'] = os.path.join(
        os.path.dirname(__file__), '..', 'static', 'uploads', 'announcements'
    )
    # Create the upload directory if it doesn't exist
    os.makedirs(app.config['ANNOUNCEMENT_UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_announcement_routes(app):
    app.register_blueprint(announcement_bp)
    app.config['ANNOUNCEMENT_UPLOAD_FOLDER'] = os.path.join(
        os.path.dirname(__file__), '..', 'static', 'uploads', 'announcements'
    )
    os.makedirs(app.config['ANNOUNCEMENT_UPLOAD_FOLDER'], exist_ok=True)


@announcement_bp.route('/')
@jwt_required()
def mto_announcements():
    """Render the MTO Announcements page"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            flash('User not found', 'error')
            return redirect(url_for('dashboard.mto_dashboard'))

        # Get announcements for the user's municipality
        announcements = Announcement.query.filter_by(
            municipality=current_user.municipality
        ).order_by(Announcement.created_at.desc()).all()

        return render_template(
            'MTO_Announcement.html',
            announcements=announcements,
            municipality=current_user.municipality,
            current_date=datetime.now().strftime('%B %d, %Y')
        )
    except Exception as e:
        current_app.logger.error(f"Error loading announcements: {str(e)}")
        flash('Failed to load announcements', 'error')
        return redirect(url_for('dashboard.mto_dashboard'))


@announcement_bp.route('/api/announcements', methods=['GET'])
@jwt_required()
def get_announcements():
    """Get announcements with pagination and filtering"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status_filter = request.args.get('status', 'all')

        # Base query filtered by municipality
        query = Announcement.query.filter_by(
            municipality=current_user.municipality
        )

        # Apply status filter
        if status_filter == 'active':
            query = query.filter_by(is_active=True)
        elif status_filter == 'inactive':
            query = query.filter_by(is_active=False)

        # Order and paginate
        paginated = query.order_by(Announcement.created_at.desc()).paginate(
            page=page, per_page=per_page
        )

        # Format announcements
        announcements = []
        for announcement in paginated.items:
            announcements.append({
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'image_url': url_for('static',
                                     filename=f'uploads/announcements/{announcement.image}') if announcement.image else None,
                'created_at': announcement.created_at.strftime('%b %d, %Y'),
                'is_active': announcement.is_active
            })

        return jsonify({
            'success': True,
            'data': {
                'announcements': announcements,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@announcement_bp.route('/api/announcements', methods=['POST'])
@jwt_required()
def create_announcement():
    """Create a new announcement for the MTO's municipality"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Debug: Log form data
        current_app.logger.debug(f"Form data: {request.form}")
        current_app.logger.debug(f"Files: {request.files}")

        # Get form data
        title = request.form.get('title')
        content = request.form.get('content')
        is_active = request.form.get('is_active', 'false').lower() == 'true'

        # Validate required fields
        if not title or not content:
            return jsonify({'success': False, 'message': 'Title and content are required'}), 400

        # Handle file upload
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(
                    current_app.config['ANNOUNCEMENT_UPLOAD_FOLDER'],
                    filename
                )
                file.save(file_path)
                image = filename

        # Create new announcement
        new_announcement = Announcement(
            title=title,
            content=content,
            image=image,
            is_active=is_active,
            municipality=current_user.municipality
        )

        db.session.add(new_announcement)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Announcement created successfully',
            'announcement_id': new_announcement.id
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating announcement: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@announcement_bp.route('/api/announcements/<int:announcement_id>', methods=['PUT'])
@jwt_required()
def update_announcement(announcement_id):
    """Update an existing announcement"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        announcement = Announcement.query.filter_by(
            id=announcement_id,
            municipality=current_user.municipality
        ).first()

        if not announcement:
            return jsonify({'success': False, 'message': 'Announcement not found'}), 404

        # Get form data
        announcement.title = request.form.get('title', announcement.title)
        announcement.content = request.form.get('content', announcement.content)
        announcement.is_active = request.form.get('is_active', str(announcement.is_active)).lower() == 'true'

        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # Delete old image if exists
                if announcement.image:
                    try:
                        os.remove(os.path.join(
                            current_app.config['ANNOUNCEMENT_UPLOAD_FOLDER'],
                            announcement.image
                        ))
                    except:
                        pass

                # Save new image
                filename = secure_filename(file.filename)
                file_path = os.path.join(
                    current_app.config['ANNOUNCEMENT_UPLOAD_FOLDER'],
                    filename
                )
                file.save(file_path)
                announcement.image = filename

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Announcement updated successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@announcement_bp.route('/api/announcements/<int:announcement_id>', methods=['DELETE'])
@jwt_required()
def delete_announcement(announcement_id):
    """Delete an announcement"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        announcement = Announcement.query.filter_by(
            id=announcement_id,
            municipality=current_user.municipality
        ).first()

        if not announcement:
            return jsonify({'success': False, 'message': 'Announcement not found'}), 404

        # Delete associated image
        if announcement.image:
            try:
                os.remove(os.path.join(
                    current_app.config['ANNOUNCEMENT_UPLOAD_FOLDER'],
                    announcement.image
                ))
            except:
                pass

        db.session.delete(announcement)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Announcement deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@announcement_bp.route('/api/announcements/<int:announcement_id>/status', methods=['PATCH'])
@jwt_required()
def toggle_announcement_status(announcement_id):
    """Toggle announcement active status"""
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        announcement = Announcement.query.filter_by(
            id=announcement_id,
            municipality=current_user.municipality
        ).first()

        if not announcement:
            return jsonify({'success': False, 'message': 'Announcement not found'}), 404

        announcement.is_active = not announcement.is_active
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Announcement status updated',
            'is_active': announcement.is_active
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500