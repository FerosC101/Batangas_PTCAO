# [file name]: MTO_Property.py
import uuid

from flask import Blueprint, jsonify, request, render_template, url_for, redirect, flash, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from Batangas_PTCAO.src.model import Property, Room, Amenity, TypicalLocation, LongLat, PropertyStatus, User, \
    PropertyImage
from Batangas_PTCAO.src.extension import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

properties_bp = Blueprint("properties", __name__, url_prefix="/property")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads/properties'


def init_property_routes(app):
    app.register_blueprint(properties_bp)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@properties_bp.route('/mto/property')
@jwt_required()
def mto_properties():
    """Render the MTO Properties page with the list of all properties"""
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)

        if not user or not user.municipality:
            flash('User municipality not found', 'error')
            return redirect(url_for('dashboard.mto_dashboard'))

        properties = Property.query.filter_by(municipality=user.municipality).all()

        # Define typical locations for dropdown
        typical_locations = [
            "Beachfront", "Mountain View", "City Center", "Lakeside",
            "Riverside", "Forest", "Countryside", "Island"
        ]

        return render_template(
            'MTO_Properties.html',
            properties=properties,
            user_id=current_user_id,
            municipality=user.municipality,
            typical_locations=typical_locations
        )
    except Exception as e:
        flash(f'Failed to load properties: {str(e)}', 'error')
        return redirect(url_for('dashboard.mto_dashboard'))


@properties_bp.route('', methods=['GET'])
@jwt_required()
def get_properties():
    """Get all properties with optional filters"""
    try:
        barangay = request.args.get('barangay')
        municipality = request.args.get('municipality')
        accommodation_type = request.args.get('accommodation_type')
        status = request.args.get('status')

        query = Property.query

        if barangay:
            query = query.filter(Property.barangay == barangay)
        if municipality:
            query = query.filter(Property.municipality == municipality)
        if accommodation_type:
            query = query.filter(Property.accommodation_type == accommodation_type)
        if status:
            query = query.filter(Property.status == PropertyStatus(status))

        properties = query.all()

        result = []
        for prop in properties:
            room_price = None
            if prop.rooms:
                room_price = float(prop.rooms[0].overnight_price)

            amenities = [amenity.amenity for amenity in prop.amenities]

            property_data = {
                'property_id': prop.property_id,
                'property_name': prop.property_name,
                'barangay': prop.barangay,
                'municipality': prop.municipality,
                'accommodation_type': prop.accommodation_type,
                'status': prop.status.value,
                'description': prop.description,
                'amenities': amenities,
                'room_price': room_price,
                'rating': 4.5,
                'image_url': f"/static/uploads/properties/{prop.property_image}" if prop.property_image else None
            }
            result.append(property_data)

        return jsonify({
            'status': 'success',
            'count': len(properties),
            'properties': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('/<int:property_id>', methods=['GET'])
@jwt_required()
def get_property(property_id):
    print(f"Fetching property ID: {property_id}")
    try:
        property = Property.query.options(
            db.joinedload(Property.images),
            db.joinedload(Property.amenities),
            db.joinedload(Property.rooms).joinedload(Room.amenities),
            db.joinedload(Property.coordinates),
            db.joinedload(Property.typical_locations)
        ).get_or_404(property_id)

        # Prepare property data
        property_data = {
            'property_id': property.property_id,
            'property_name': property.property_name,
            'barangay': property.barangay,
            'municipality': property.municipality,
            'accommodation_type': property.accommodation_type,
            'status': property.status.value,
            'description': property.description,
            'images': [{'id': img.id, 'image_path': img.image_path} for img in property.images],
            'amenities': [{'amenity_id': a.amenity_id, 'amenity': a.amenity} for a in property.amenities if
                          a.room_id is None],
            'coordinates': [{'id': c.id, 'longitude': c.longitude, 'latitude': c.latitude} for c in
                            property.coordinates],
            'typical_locations': [{'id': tl.id, 'location': tl.location} for tl in property.typical_locations],
            'rooms': []
        }

        # Prepare room data
        for room in property.rooms:
            room_data = {
                'room_id': room.room_id,
                'room_type': room.room_type,
                'day_price': float(room.day_price),
                'overnight_price': float(room.overnight_price),
                'capacity': room.capacity,
                'amenities': [{'amenity_id': a.amenity_id, 'amenity': a.amenity} for a in room.amenities]
            }
            property_data['rooms'].append(room_data)

        return jsonify({
            'status': 'success',
            'property': property_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error fetching property: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('', methods=['POST'])
@jwt_required()
def create_property():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.municipality:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        # Handle form data
        data = request.form.to_dict()
        files = request.files.getlist('property_images')

        # Create property
        new_property = Property(
            property_name=data['property_name'],
            barangay=data['barangay'],
            municipality=user.municipality,
            accommodation_type=data['accommodation_type'],
            status=PropertyStatus(data.get('status', 'ACTIVE')),
            description=data.get('description')
        )

        db.session.add(new_property)
        db.session.flush()  # Generate the ID

        # Handle coordinates
        if 'longitude' in data and 'latitude' in data:
            db.session.add(LongLat(
                property_id=new_property.property_id,
                longitude=float(data['longitude']),
                latitude=float(data['latitude'])
            ))

        # Handle typical locations
        typical_locations = request.form.getlist('typical_locations[]')
        for location in typical_locations:
            if location.strip():
                db.session.add(TypicalLocation(
                    property_id=new_property.property_id,
                    location=location.strip()
                ))

        # Handle file uploads
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{new_property.property_id}_{file.filename}")
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                db.session.add(PropertyImage(
                    property_id=new_property.property_id,
                    image_path=filename
                ))

        # Handle amenities
        amenities = request.form.getlist('amenities[]')
        for amenity in amenities:
            if amenity.strip():
                db.session.add(Amenity(
                    property_id=new_property.property_id,
                    amenity=amenity.strip()
                ))

        # Handle rooms
        room_indices = set()
        for key in request.form.keys():
            if key.startswith('rooms['):
                index = key.split('[')[1].split(']')[0]
                room_indices.add(index)

        for index in room_indices:
            room = Room(
                property_id=new_property.property_id,
                room_type=request.form.get(f'rooms[{index}][room_type]'),
                day_price=float(request.form.get(f'rooms[{index}][day_price]', 0)),
                overnight_price=float(request.form.get(f'rooms[{index}][overnight_price]', 0)),
                capacity=int(request.form.get(f'rooms[{index}][capacity]', 1))
            )
            db.session.add(room)
            db.session.flush()

        amenities = request.form.getlist('amenities[]')
        for amenity in amenities:
            if amenity.strip():  # Skip empty amenities
                amenity_record = Amenity(
                    property_id=new_property.property_id,
                    amenity=amenity.strip()
                )
                db.session.add(amenity_record)
                db.session.flush()

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Property created successfully',
            'property_id': new_property.property_id
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating property: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('/update/<int:property_id>', methods=['POST'])
@jwt_required()
def update_property(property_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        property = Property.query.get_or_404(property_id)

        if property.municipality != user.municipality:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        # Handle form data
        data = request.form.to_dict()
        files = request.files.getlist('property_images')

        # Update basic property info
        property.property_name = data.get('property_name', property.property_name)
        property.barangay = data.get('barangay', property.barangay)
        property.accommodation_type = data.get('accommodation_type', property.accommodation_type)
        property.status = PropertyStatus(data.get('status', property.status.value))
        property.description = data.get('description', property.description)

        if 'longitude' in data and 'latitude' in data:
            LongLat.query.filter_by(property_id=property_id).delete()
            db.session.add(LongLat(
                property_id=property_id,
                longitude=float(data['longitude']),
                latitude=float(data['latitude'])
            ))

        # Update typical locations
        TypicalLocation.query.filter_by(property_id=property_id).delete()
        typical_locations = request.form.getlist('typical_locations[]')
        for location in typical_locations:
            if location.strip():
                db.session.add(TypicalLocation(
                    property_id=property_id,
                    location=location.strip()
                ))

        amenities = request.form.getlist('amenities[]')
        if amenities:
            Amenity.query.filter_by(property_id=property_id, room_id=None).delete()
            for amenity in amenities:
                if amenity:
                    db.session.add(Amenity(
                        property_id=property_id,
                        amenity=amenity
                    ))

        # Handle rooms
        room_indices = set()
        for key in request.form.keys():
            if key.startswith('rooms['):
                index = key.split('[')[1].split(']')[0]
                room_indices.add(index)

        if room_indices:
            Room.query.filter_by(property_id=property_id).delete()

            for index in room_indices:
                room_data = {
                    'room_type': request.form.get(f'rooms[{index}][room_type]'),
                    'day_price': request.form.get(f'rooms[{index}][day_price]'),
                    'overnight_price': request.form.get(f'rooms[{index}][overnight_price]'),
                    'capacity': request.form.get(f'rooms[{index}][capacity]')
                }

                if room_data['room_type']:
                    room = Room(
                        property_id=property_id,
                        room_type=room_data['room_type'],
                        day_price=float(room_data.get('day_price', 0)),
                        overnight_price=float(room_data.get('overnight_price', 0)),
                        capacity=int(room_data.get('capacity', 1))
                    )
                    db.session.add(room)

        # Handle file uploads
        for file in files:
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{property_id}_{secure_filename(property.property_name)}_{uuid.uuid4().hex[:8]}.{ext}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                db.session.add(PropertyImage(
                    property_id=property_id,
                    image_path=filename
                ))

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Property updated successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('/<int:property_id>/images', methods=['POST'])
@jwt_required()
def upload_property_images(property_id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        property = Property.query.get_or_404(property_id)

        if property.municipality != user.municipality:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        files = request.files.getlist('property_image')
        if not files:
            return jsonify({'status': 'error', 'message': 'No files uploaded'}), 400

        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{property_id}_{secure_filename(property.property_name)}_{uuid.uuid4().hex[:8]}.{ext}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                property_image = PropertyImage(
                    property_id=property_id,
                    image_path=filename
                )
                db.session.add(property_image)
                uploaded_files.append(filename)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Images uploaded successfully',
            'files': uploaded_files
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@properties_bp.route('/<int:property_id>', methods=['DELETE'])
@jwt_required()
def delete_property(property_id):
    """Delete a property"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        property = Property.query.get_or_404(property_id)

        if property.municipality != user.municipality:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        db.session.delete(property)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Property deleted successfully'
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('/barangays', methods=['GET'])
@jwt_required()
def get_barangays():
    """Get all unique barangays"""
    try:
        barangays = db.session.query(Property.barangay).distinct().filter(Property.barangay != None).all()
        barangay_list = [barangay[0] for barangay in barangays]

        return jsonify({
            'status': 'success',
            'barangays': barangay_list
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('/municipalities', methods=['GET'])
@jwt_required()
def get_municipalities():
    """Get all unique municipalities"""
    try:
        municipalities = db.session.query(Property.municipality).distinct().filter(Property.municipality != None).all()
        municipality_list = [municipality[0] for municipality in municipalities]

        return jsonify({
            'status': 'success',
            'municipalities': municipality_list
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('/accommodation-types', methods=['GET'])
@jwt_required()
def get_accommodation_types():
    """Get all unique accommodation types"""
    try:
        types = db.session.query(Property.accommodation_type).distinct().filter(
            Property.accommodation_type != None).all()
        type_list = [type[0] for type in types]

        return jsonify({
            'status': 'success',
            'accommodation_types': type_list
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('/<int:property_id>/status', methods=['PATCH'])
@jwt_required()
def change_property_status(property_id):
    """Change property status"""
    try:
        data = request.get_json()
        if 'status' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing status field'
            }), 400

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        property = Property.query.get_or_404(property_id)

        if property.municipality != user.municipality:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        property.status = PropertyStatus(data['status'])
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Property status updated to {data["status"]}'
        }), 200
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'Invalid status value: {str(e)}'
        }), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500