# Fixed TOURIST_Destination.py - API Routes for Tourist Destinations

from flask import Blueprint, jsonify, request
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import Property, PropertyImage, Room, Amenity, Destination, LongLat, DestinationType
from sqlalchemy import func, desc
import os

# Create blueprints for better organization
tourist_api_bp = Blueprint('tourist_api', __name__, url_prefix='/tourist/api')


def init_tourist_api_routes(app):
    """Initialize tourist API routes"""
    app.register_blueprint(tourist_api_bp)


@tourist_api_bp.route('/properties', methods=['GET'])
def get_tourist_properties():
    """Get all active properties with their details for tourists"""
    try:
        # Query properties with related data using the correct relationship approach
        properties = Property.query.filter(Property.status == 'ACTIVE').all()

        properties_data = []

        for property in properties:
            # Get the main image (first image) with proper path handling
            main_image = None
            if property.images and len(property.images) > 0:
                image_filename = property.images[0].image_path
                # Ensure proper path formatting
                if not image_filename.startswith('/'):
                    main_image = f"/static/uploads/events/{image_filename}"
                else:
                    main_image = image_filename
            else:
                main_image = "/static/images/default-property.jpg"

            # Get amenities safely
            amenities = []
            if property.amenities:
                amenities = [{'amenity': amenity.amenity} for amenity in property.amenities]

            # Get rooms with proper price handling
            rooms = []
            total_rooms = 0
            price_range = None

            if property.rooms:
                for room in property.rooms:
                    room_data = {
                        'room_type': room.room_type or 'Standard Room',
                        'capacity': room.capacity or 1,
                        'day_price': float(room.day_price) if room.day_price else None,
                        'overnight_price': float(room.overnight_price) if room.overnight_price else None
                    }
                    rooms.append(room_data)
                    total_rooms += 1

                # Calculate price range from rooms
                prices = []
                for room in rooms:
                    if room['day_price']:
                        prices.append(room['day_price'])
                    if room['overnight_price']:
                        prices.append(room['overnight_price'])

                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    if min_price == max_price:
                        price_range = f"₱{min_price:,.0f}"
                    else:
                        price_range = f"₱{min_price:,.0f} - ₱{max_price:,.0f}"
                else:
                    price_range = "Contact for pricing"
            else:
                price_range = "Contact for pricing"

            # Get coordinates safely
            coordinates = None
            if property.coordinates and len(property.coordinates) > 0:
                coord = property.coordinates[0]
                coordinates = {
                    'latitude': float(coord.latitude) if coord.latitude else 0,
                    'longitude': float(coord.longitude) if coord.longitude else 0
                }

            property_data = {
                'property_id': property.property_id,
                'property_name': property.property_name or 'Unnamed Property',
                'barangay': property.barangay or '',
                'municipality': property.municipality or 'Batangas',
                'accommodation_type': property.accommodation_type or 'Property',
                'status': property.status.value if hasattr(property.status, 'value') else str(property.status),
                'description': property.description or f'Beautiful {property.accommodation_type or "property"} in {property.municipality or "Batangas"}',
                'main_image': main_image,
                'amenities': amenities,
                'rooms': rooms,
                'total_rooms': total_rooms,
                'price_range': price_range,
                'coordinates': coordinates
            }

            properties_data.append(property_data)

        return jsonify({
            'success': True,
            'properties': properties_data,
            'total': len(properties_data)
        })

    except Exception as e:
        print(f"Error in get_tourist_properties: {str(e)}")  # For debugging
        return jsonify({
            'success': False,
            'message': f'Error fetching properties: {str(e)}'
        }), 500


@tourist_api_bp.route('/destinations', methods=['GET'])
def get_tourist_destinations():
    """Get all destinations for tourists"""
    try:
        # Query all destinations with proper ordering
        destinations = Destination.query.order_by(
            desc(Destination.is_featured),
            Destination.name
        ).all()

        destinations_data = []

        for destination in destinations:
            # Handle image path safely
            image_path = "/static/images/default-destination.jpg"  # Default fallback
            if destination.image_path:
                # Check if it's already a full path
                if destination.image_path.startswith('/'):
                    image_path = destination.image_path
                elif destination.image_path.startswith('http'):
                    image_path = destination.image_path
                else:
                    image_path = f"/static/uploads/destinations/{destination.image_path}"

            # Handle destination type safely
            destination_type_value = 'Other'
            if destination.destination_type:
                if hasattr(destination.destination_type, 'value'):
                    destination_type_value = destination.destination_type.value
                else:
                    destination_type_value = str(destination.destination_type)

            destination_data = {
                'id': destination.id,
                'name': destination.name or 'Unnamed Destination',
                'description': destination.description or 'Explore this amazing destination in Batangas.',
                'location_name': destination.location_name or destination.municipality,
                'longitude': float(destination.longitude) if destination.longitude else 0,
                'latitude': float(destination.latitude) if destination.latitude else 0,
                'barangay': destination.barangay or '',
                'municipality': destination.municipality or 'Batangas',
                'destination_type': {
                    'value': destination_type_value
                },
                'image_path': image_path,
                'is_featured': destination.is_featured or False,
                'created_at': destination.created_at.isoformat() if destination.created_at else None
            }

            destinations_data.append(destination_data)

        return jsonify({
            'success': True,
            'destinations': destinations_data,
            'total': len(destinations_data)
        })

    except Exception as e:
        print(f"Error in get_tourist_destinations: {str(e)}")  # For debugging
        return jsonify({
            'success': False,
            'message': f'Error fetching destinations: {str(e)}'
        }), 500


@tourist_api_bp.route('/property/<int:property_id>', methods=['GET'])
def get_property_details(property_id):
    """Get detailed information about a specific property"""
    try:
        property = Property.query.get(property_id)

        if not property:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404

        # Get all images
        images = []
        if property.images:
            for img in property.images:
                image_path = img.image_path
                if not image_path.startswith('/'):
                    image_path = f"/static/uploads/properties/{image_path}"
                images.append(image_path)

        # Get amenities
        amenities = []
        if property.amenities:
            amenities = [{'amenity': amenity.amenity} for amenity in property.amenities]

        # Get rooms with amenities
        rooms = []
        if property.rooms:
            for room in property.rooms:
                room_amenities = []
                if room.amenities:
                    room_amenities = [{'amenity': amenity.amenity} for amenity in room.amenities]

                room_data = {
                    'room_id': room.room_id,
                    'room_type': room.room_type or 'Standard Room',
                    'capacity': room.capacity or 1,
                    'day_price': float(room.day_price) if room.day_price else None,
                    'overnight_price': float(room.overnight_price) if room.overnight_price else None,
                    'amenities': room_amenities
                }
                rooms.append(room_data)

        # Get coordinates
        coordinates = None
        if property.coordinates and len(property.coordinates) > 0:
            coord = property.coordinates[0]
            coordinates = {
                'latitude': float(coord.latitude) if coord.latitude else 0,
                'longitude': float(coord.longitude) if coord.longitude else 0
            }

        # Get typical locations
        typical_locations = []
        if property.typical_locations:
            typical_locations = [loc.location for loc in property.typical_locations]

        property_data = {
            'property_id': property.property_id,
            'property_name': property.property_name or 'Unnamed Property',
            'barangay': property.barangay or '',
            'municipality': property.municipality or 'Batangas',
            'accommodation_type': property.accommodation_type or 'Property',
            'status': property.status.value if hasattr(property.status, 'value') else str(property.status),
            'description': property.description or f'Beautiful {property.accommodation_type or "property"} in {property.municipality or "Batangas"}',
            'images': images,
            'main_image': images[0] if images else "/static/images/default-property.jpg",
            'amenities': amenities,
            'rooms': rooms,
            'coordinates': coordinates,
            'typical_locations': typical_locations
        }

        return jsonify({
            'success': True,
            'property': property_data
        })

    except Exception as e:
        print(f"Error in get_property_details: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching property details: {str(e)}'
        }), 500


@tourist_api_bp.route('/destination/<int:destination_id>', methods=['GET'])
def get_destination_details(destination_id):
    """Get detailed information about a specific destination"""
    try:
        destination = Destination.query.get(destination_id)

        if not destination:
            return jsonify({
                'success': False,
                'message': 'Destination not found'
            }), 404

        # Handle image path
        image_path = "/static/images/default-destination.jpg"
        if destination.image_path:
            if destination.image_path.startswith('/'):
                image_path = destination.image_path
            elif destination.image_path.startswith('http'):
                image_path = destination.image_path
            else:
                image_path = f"/static/uploads/destinations/{destination.image_path}"

        # Handle destination type
        destination_type_value = 'Other'
        if destination.destination_type:
            if hasattr(destination.destination_type, 'value'):
                destination_type_value = destination.destination_type.value
            else:
                destination_type_value = str(destination.destination_type)

        destination_data = {
            'id': destination.id,
            'name': destination.name or 'Unnamed Destination',
            'description': destination.description or 'Explore this amazing destination in Batangas.',
            'location_name': destination.location_name or destination.municipality,
            'longitude': float(destination.longitude) if destination.longitude else 0,
            'latitude': float(destination.latitude) if destination.latitude else 0,
            'barangay': destination.barangay or '',
            'municipality': destination.municipality or 'Batangas',
            'destination_type': {
                'value': destination_type_value
            },
            'image_path': image_path,
            'is_featured': destination.is_featured or False,
            'created_at': destination.created_at.isoformat() if destination.created_at else None,
            'updated_at': destination.updated_at.isoformat() if destination.updated_at else None
        }

        return jsonify({
            'success': True,
            'destination': destination_data
        })

    except Exception as e:
        print(f"Error in get_destination_details: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching destination details: {str(e)}'
        }), 500


@tourist_api_bp.route('/search', methods=['GET'])
def search_properties_and_destinations():
    """Search both properties and destinations"""
    try:
        query = request.args.get('q', '').strip().lower()
        search_type = request.args.get('type', 'all')  # all, properties, destinations
        municipality = request.args.get('municipality', '')

        results = {
            'properties': [],
            'destinations': []
        }

        if search_type in ['all', 'properties']:
            # Search properties
            property_query = Property.query.filter(Property.status == 'ACTIVE')

            if query:
                property_query = property_query.filter(
                    db.or_(
                        func.lower(Property.property_name).contains(query),
                        func.lower(Property.description).contains(query),
                        func.lower(Property.municipality).contains(query),
                        func.lower(Property.barangay).contains(query)
                    )
                )

            if municipality:
                property_query = property_query.filter(
                    func.lower(Property.municipality) == municipality.lower()
                )

            properties = property_query.limit(20).all()

            for property in properties:
                main_image = "/static/images/default-property.jpg"
                if property.images and len(property.images) > 0:
                    image_filename = property.images[0].image_path
                    if not image_filename.startswith('/'):
                        main_image = f"/static/uploads/properties/{image_filename}"
                    else:
                        main_image = image_filename

                results['properties'].append({
                    'property_id': property.property_id,
                    'property_name': property.property_name or 'Unnamed Property',
                    'barangay': property.barangay or '',
                    'municipality': property.municipality or 'Batangas',
                    'accommodation_type': property.accommodation_type or 'Property',
                    'description': property.description or f'Beautiful {property.accommodation_type or "property"}',
                    'main_image': main_image,
                    'type': 'property'
                })

        if search_type in ['all', 'destinations']:
            # Search destinations
            destination_query = Destination.query

            if query:
                destination_query = destination_query.filter(
                    db.or_(
                        func.lower(Destination.name).contains(query),
                        func.lower(Destination.description).contains(query),
                        func.lower(Destination.municipality).contains(query),
                        func.lower(Destination.barangay).contains(query)
                    )
                )

            if municipality:
                destination_query = destination_query.filter(
                    func.lower(Destination.municipality) == municipality.lower()
                )

            destinations = destination_query.limit(20).all()

            for destination in destinations:
                image_path = "/static/images/default-destination.jpg"
                if destination.image_path:
                    if destination.image_path.startswith('/'):
                        image_path = destination.image_path
                    elif destination.image_path.startswith('http'):
                        image_path = destination.image_path
                    else:
                        image_path = f"/static/uploads/destinations/{destination.image_path}"

                destination_type_value = 'Other'
                if destination.destination_type:
                    if hasattr(destination.destination_type, 'value'):
                        destination_type_value = destination.destination_type.value
                    else:
                        destination_type_value = str(destination.destination_type)

                results['destinations'].append({
                    'id': destination.id,
                    'name': destination.name or 'Unnamed Destination',
                    'location_name': destination.location_name or destination.municipality,
                    'municipality': destination.municipality or 'Batangas',
                    'barangay': destination.barangay or '',
                    'destination_type': destination_type_value,
                    'description': destination.description or 'Amazing destination',
                    'image_path': image_path,
                    'is_featured': destination.is_featured or False,
                    'type': 'destination'
                })

        return jsonify({
            'success': True,
            'results': results,
            'total_properties': len(results['properties']),
            'total_destinations': len(results['destinations'])
        })

    except Exception as e:
        print(f"Error in search: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error searching: {str(e)}'
        }), 500


@tourist_api_bp.route('/municipalities', methods=['GET'])
def get_municipalities():
    """Get all municipalities that have properties or destinations"""
    try:
        # Get municipalities from properties
        property_municipalities = db.session.query(Property.municipality) \
            .filter(Property.status == 'ACTIVE') \
            .filter(Property.municipality.isnot(None)) \
            .distinct().all()

        # Get municipalities from destinations
        destination_municipalities = db.session.query(Destination.municipality) \
            .filter(Destination.municipality.isnot(None)) \
            .distinct().all()

        # Combine and deduplicate
        municipalities = set()
        for (municipality,) in property_municipalities:
            if municipality and municipality.strip():
                municipalities.add(municipality.strip())

        for (municipality,) in destination_municipalities:
            if municipality and municipality.strip():
                municipalities.add(municipality.strip())

        return jsonify({
            'success': True,
            'municipalities': sorted(list(municipalities))
        })

    except Exception as e:
        print(f"Error in get_municipalities: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching municipalities: {str(e)}'
        }), 500