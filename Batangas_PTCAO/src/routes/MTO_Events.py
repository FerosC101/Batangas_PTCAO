from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from extension import db
from model import Event, User
import os
from werkzeug.utils import secure_filename

events_bp = Blueprint('events', __name__, url_prefix='/mto/events')

# Allowed file extensions for event images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def init_events_routes(app):
    app.register_blueprint(events_bp)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'events')


@events_bp.route('/')
@jwt_required()
def mto_events():
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            flash('User not found', 'error')
            return redirect(url_for('dashboard.mto_dashboard'))

        upcoming_events = Event.query.filter(
            Event.end_date >= datetime.now().date(),
            Event.municipality == current_user.municipality
        ).order_by(Event.start_date.asc()).all()

        past_events = Event.query.filter(
            Event.end_date < datetime.now().date(),
            Event.municipality == current_user.municipality
        ).order_by(Event.start_date.desc()).limit(3).all()

        return render_template(
            'MTO_Events.html',
            upcoming_events=upcoming_events,
            past_events=past_events,
            user_id=current_user.user_id,
            user_municipality=current_user.municipality
        )
    except Exception as e:
        print(f"Error in mto_events: {str(e)}")
        flash('Failed to load events data', 'error')
        return redirect(url_for('dashboard.mto_dashboard'))


@events_bp.route('/api/events', methods=['GET'])
@jwt_required()
def get_events():
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get filter parameters
        event_type = request.args.get('type', 'upcoming')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Base query filtered by user's municipality
        query = Event.query.filter(
            Event.municipality == current_user.municipality
        )

        if event_type == 'upcoming':
            query = query.filter(Event.end_date >= datetime.now().date())
        else:
            query = query.filter(Event.end_date < datetime.now().date())

        # Pagination
        paginated = query.order_by(Event.start_date.desc()).paginate(page=page, per_page=per_page)

        # Format events
        events = []
        for event in paginated.items:
            events.append({
                'event_id': event.event_id,
                'event_title': event.event_title,
                'description': event.description,
                'start_date': event.start_date.strftime('%Y-%m-%d'),
                'end_date': event.end_date.strftime('%Y-%m-%d'),
                'location': event.location,
                'municipality': event.municipality,
                'category': event.category,
                'image_url': url_for('static',
                                     filename=f'uploads/events/{event.event_image}') if event.event_image else None
            })

        return jsonify({
            'success': True,
            'data': {
                'events': events,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@events_bp.route('/api/events', methods=['POST'])
@jwt_required()
def create_event():
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get form data
        event_title = request.form.get('event_title')
        description = request.form.get('description')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        location = request.form.get('location')
        category = request.form.get('category')

        # Validate required fields
        if not all([event_title, start_date, end_date, location]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Handle file uploads
        event_image = None
        if 'event_image' in request.files:
            file = request.files['event_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                event_image = filename

        # Create new event with user's municipality
        new_event = Event(
            event_title=event_title,
            description=description,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
            end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
            location=location,
            municipality=current_user.municipality,  # Use user's municipality
            event_image=event_image,
            category=category
        )

        db.session.add(new_event)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'event_id': new_event.event_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@events_bp.route('/api/events/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)

        # Get form data
        event.event_title = request.form.get('event_title', event.event_title)
        event.description = request.form.get('description', event.description)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        event.location = request.form.get('location', event.location)
        event.municipality = request.form.get('municipality', event.municipality)
        event.category = request.form.get('category', event.category)

        if start_date:
            event.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            event.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Handle file uploads
        if 'event_image' in request.files:
            file = request.files['event_image']
            if file and allowed_file(file.filename):
                # Delete old image if exists
                if event.event_image:
                    try:
                        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], event.event_image))
                    except:
                        pass

                # Save new image
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                event.event_image = filename

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Event updated successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@events_bp.route('/api/events/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)

        # Delete associated image if exists
        if event.event_image:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], event.event_image))
            except:
                pass

        db.session.delete(event)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Event deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500