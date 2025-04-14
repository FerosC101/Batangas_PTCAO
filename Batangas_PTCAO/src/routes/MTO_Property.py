
from flask import Blueprint, jsonify, request, render_template, url_for, redirect, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from Batangas_PTCAO.src.model import Property, Room, Amenity, TypicalLocation, LongLat, PropertyStatus, User
from Batangas_PTCAO.src.extension import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

properties_bp = Blueprint("properties", __name__, url_prefix="/property")


def init_property_routes(app):
    app.register_blueprint(properties_bp)


@properties_bp.route('/mto/properties')
@jwt_required()
def mto_properties():
    """
    Render the MTO Properties page with the list of all properties
    """
    try:
        # Get current user identity
        current_user_id = get_jwt_identity()

        user = User.query.get(current_user_id)

        if not user or not user.municipality:
            flash('User municipality not found', 'error')
            return redirect(url_for('dashboard.mto_dashboard'))

        properties = Property.query.filter_by(municipality=user.municipality).all()

        return render_template(
            'MTO_Properties.html',
            properties=properties,
            user_id=current_user_id,
            municipality=user.municipality
        )

    except Exception as e:
        flash(f'Failed to load properties: {str(e)}', 'error')
        return redirect(url_for('dashboard.mto_dashboard'))

@properties_bp.route('', methods=['GET'])
@jwt_required()
def get_properties():
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
                'rating': 4.5,  # Placeholder, would be calculated from reviews
                'image_url': f"/static/images/properties/{prop.property_id}.jpg"  # Placeholder
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
    try:
        property = Property.query.get_or_404(property_id)

        rooms_data = []
        for room in property.rooms:
            room_data = {
                'room_id': room.room_id,
                'room_type': room.room_type,
                'day_price': float(room.day_price),
                'overnight_price': float(room.overnight_price),
                'capacity': room.capacity,
                'amenities': [amenity.amenity for amenity in room.amenities]
            }
            rooms_data.append(room_data)

        coordinates = []
        for coord in property.coordinates:
            coordinates.append({
                'longitude': coord.longitude,
                'latitude': coord.latitude
            })

        result = {
            'property_id': property.property_id,
            'property_name': property.property_name,
            'barangay': property.barangay,
            'municipality': property.municipality,
            'accommodation_type': property.accommodation_type,
            'status': property.status.value,
            'description': property.description,
            'amenities': [amenity.amenity for amenity in property.amenities],
            'typical_locations': [location.location for location in property.typical_locations],
            'coordinates': coordinates,
            'rooms': rooms_data,
            'rating': 4.5,  # Placeholder, would be calculated from reviews
            'image_url': f"/static/images/properties/{property.property_id}.jpg"  # Placeholder
        }

        return jsonify({
            'status': 'success',
            'property': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@properties_bp.route('', methods=['POST'])
@jwt_required()
def create_property():
    try:
        data = request.get_json()

        required_fields = ['property_name', 'municipality']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400

        new_property = Property(
            property_name=data['property_name'],
            barangay=data.get('barangay'),
            municipality=data['municipality'],
            accommodation_type=data.get('accommodation_type'),
            status=PropertyStatus(data.get('status', 'Active')),
            description=data.get('description')
        )

        if 'amenities' in data and isinstance(data['amenities'], list):
            for amenity_name in data['amenities']:
                amenity = Amenity(amenity=amenity_name)
                new_property.amenities.append(amenity)

        if 'typical_locations' in data and isinstance(data['typical_locations'], list):
            for location_name in data['typical_locations']:
                location = TypicalLocation(location=location_name)
                new_property.typical_locations.append(location)

        if 'coordinates' in data and isinstance(data['coordinates'], list):
            for coord in data['coordinates']:
                if 'longitude' in coord and 'latitude' in coord:
                    coordinate = LongLat(
                        longitude=coord['longitude'],
                        latitude=coord['latitude']
                    )
                    new_property.coordinates.append(coordinate)

        if 'rooms' in data and isinstance(data['rooms'], list):
            for room_data in data['rooms']:
                room = Room(
                    room_type=room_data.get('room_type'),
                    day_price=room_data.get('day_price'),
                    overnight_price=room_data.get('overnight_price'),
                    capacity=room_data.get('capacity')
                )

                # Add room amenities if provided
                if 'amenities' in room_data and isinstance(room_data['amenities'], list):
                    for amenity_name in room_data['amenities']:
                        amenity = Amenity(amenity=amenity_name)
                        room.amenities.append(amenity)

                new_property.rooms.append(room)

        # Save to database
        db.session.add(new_property)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Property created successfully',
            'property_id': new_property.property_id
        }), 201
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


@properties_bp.route('/<int:property_id>', methods=['PUT'])
@jwt_required()
def update_property(property_id):
    try:
        property = Property.query.get_or_404(property_id)
        data = request.get_json()

        if 'property_name' in data:
            property.property_name = data['property_name']
        if 'barangay' in data:
            property.barangay = data['barangay']
        if 'municipality' in data:
            property.municipality = data['municipality']
        if 'accommodation_type' in data:
            property.accommodation_type = data['accommodation_type']
        if 'status' in data:
            property.status = PropertyStatus(data['status'])
        if 'description' in data:
            property.description = data['description']

        if 'amenities' in data and isinstance(data['amenities'], list):
            for amenity in property.amenities:
                db.session.delete(amenity)

            for amenity_name in data['amenities']:
                amenity = Amenity(amenity=amenity_name, property_id=property.property_id)
                db.session.add(amenity)

        if 'typical_locations' in data and isinstance(data['typical_locations'], list):
            for location in property.typical_locations:
                db.session.delete(location)

            for location_name in data['typical_locations']:
                location = TypicalLocation(location=location_name, property_id=property.property_id)
                db.session.add(location)

        if 'coordinates' in data and isinstance(data['coordinates'], list):
            for coord in property.coordinates:
                db.session.delete(coord)

            for coord in data['coordinates']:
                if 'longitude' in coord and 'latitude' in coord:
                    coordinate = LongLat(
                        longitude=coord['longitude'],
                        latitude=coord['latitude'],
                        property_id=property.property_id
                    )
                    db.session.add(coordinate)

        if 'rooms' in data and isinstance(data['rooms'], list):
            existing_rooms = {room.room_id: room for room in property.rooms}
            processed_room_ids = set()

            for room_data in data['rooms']:
                room_id = room_data.get('room_id')

                if room_id and room_id in existing_rooms:
                    room = existing_rooms[room_id]
                    processed_room_ids.add(room_id)

                    if 'room_type' in room_data:
                        room.room_type = room_data['room_type']
                    if 'day_price' in room_data:
                        room.day_price = room_data['day_price']
                    if 'overnight_price' in room_data:
                        room.overnight_price = room_data['overnight_price']
                    if 'capacity' in room_data:
                        room.capacity = room_data['capacity']

                    if 'amenities' in room_data and isinstance(room_data['amenities'], list):
                        for amenity in room.amenities:
                            db.session.delete(amenity)

                        for amenity_name in room_data['amenities']:
                            amenity = Amenity(amenity=amenity_name, room_id=room.room_id)
                            db.session.add(amenity)
                else:
                    new_room = Room(
                        property_id=property.property_id,
                        room_type=room_data.get('room_type'),
                        day_price=room_data.get('day_price'),
                        overnight_price=room_data.get('overnight_price'),
                        capacity=room_data.get('capacity')
                    )

                    if 'amenities' in room_data and isinstance(room_data['amenities'], list):
                        for amenity_name in room_data['amenities']:
                            amenity = Amenity(amenity=amenity_name)
                            new_room.amenities.append(amenity)

                    db.session.add(new_room)

            for room_id, room in existing_rooms.items():
                if room_id not in processed_room_ids:
                    db.session.delete(room)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Property updated successfully'
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


# Delete a property
@properties_bp.route('/<int:property_id>', methods=['DELETE'])
@jwt_required()
def delete_property(property_id):
    try:
        property = Property.query.get_or_404(property_id)

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


# Get all unique barangays
@properties_bp.route('/barangays', methods=['GET'])
@jwt_required()
def get_barangays():
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


# Get all unique municipalities
@properties_bp.route('/municipalities', methods=['GET'])
@jwt_required()
def get_municipalities():
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
    try:
        data = request.get_json()
        if 'status' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing status field'
            }), 400

        property = Property.query.get_or_404(property_id)
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

