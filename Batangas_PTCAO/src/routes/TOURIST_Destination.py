# Enhanced TOURIST_Destination.py - API Routes for Tourist Destinations with Municipality Filter and Nearby Destinations

from flask import Blueprint, jsonify, request, render_template
from extension import db
from model import Property, PropertyImage, Room, Amenity, Destination, LongLat, DestinationType
from sqlalchemy import func, desc, text
import os
import math

# Create blueprints for better organization
tourist_api_bp = Blueprint('tourist_api', __name__, url_prefix='/tourist/api')


def init_tourist_api_routes(app):
    """Initialize tourist API routes"""
    app.register_blueprint(tourist_api_bp)


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')

    try:
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r
    except (TypeError, ValueError):
        return float('inf')


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


@tourist_api_bp.route('/nearby-destinations/<int:property_id>', methods=['GET'])
def get_nearby_destinations(property_id):
    """Get nearby destinations for a specific property (within 10km)"""
    try:
        max_distance = float(request.args.get('max_distance', 10))  # Default 10km
        limit = int(request.args.get('limit', 10))  # Default 10 destinations

        # Get the property with coordinates
        property = Property.query.get(property_id)

        if not property:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404

        if not property.coordinates or len(property.coordinates) == 0:
            return jsonify({
                'success': True,
                'nearby_destinations': [],
                'total': 0,
                'message': 'No coordinates available for this property'
            })

        property_coord = property.coordinates[0]
        property_lat = float(property_coord.latitude) if property_coord.latitude else None
        property_lng = float(property_coord.longitude) if property_coord.longitude else None

        if not property_lat or not property_lng:
            return jsonify({
                'success': True,
                'nearby_destinations': [],
                'total': 0,
                'message': 'Invalid coordinates for this property'
            })

        # Get all destinations with coordinates
        destinations = Destination.query.filter(
            Destination.latitude.isnot(None),
            Destination.longitude.isnot(None)
        ).all()

        nearby_destinations = []

        for destination in destinations:
            dest_lat = float(destination.latitude) if destination.latitude else None
            dest_lng = float(destination.longitude) if destination.longitude else None

            if dest_lat and dest_lng:
                distance = calculate_distance(property_lat, property_lng, dest_lat, dest_lng)

                if distance <= max_distance:
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

                    nearby_destinations.append({
                        'id': destination.id,
                        'name': destination.name or 'Unnamed Destination',
                        'description': destination.description or 'Explore this amazing destination in Batangas.',
                        'location_name': destination.location_name or destination.municipality,
                        'municipality': destination.municipality or 'Batangas',
                        'barangay': destination.barangay or '',
                        'destination_type': {
                            'value': destination_type_value
                        },
                        'image_path': image_path,
                        'is_featured': destination.is_featured or False,
                        'distance': round(distance, 2),
                        'latitude': dest_lat,
                        'longitude': dest_lng
                    })

        # Sort by distance and limit results
        nearby_destinations.sort(key=lambda x: x['distance'])
        nearby_destinations = nearby_destinations[:limit]

        return jsonify({
            'success': True,
            'nearby_destinations': nearby_destinations,
            'total': len(nearby_destinations),
            'property_coordinates': {
                'latitude': property_lat,
                'longitude': property_lng
            },
            'max_distance_km': max_distance
        })

    except Exception as e:
        print(f"Error in get_nearby_destinations: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching nearby destinations: {str(e)}'
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
    """Search both properties and destinations with advanced filtering"""
    try:
        query = request.args.get('q', '').strip().lower()
        search_type = request.args.get('type', 'all')  # all, properties, destinations
        municipality = request.args.get('municipality', '')
        property_type = request.args.get('property_type', '')
        destination_type = request.args.get('destination_type', '')

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
                        func.lower(Property.barangay).contains(query),
                        func.lower(Property.accommodation_type).contains(query)
                    )
                )

            if municipality:
                property_query = property_query.filter(
                    func.lower(Property.municipality) == municipality.lower()
                )

            if property_type:
                property_query = property_query.filter(
                    func.lower(Property.accommodation_type).contains(property_type.lower())
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
                        func.lower(Destination.barangay).contains(query),
                        func.lower(Destination.location_name).contains(query)
                    )
                )

            if municipality:
                destination_query = destination_query.filter(
                    func.lower(Destination.municipality) == municipality.lower()
                )

            if destination_type:
                destination_query = destination_query.filter(
                    Destination.destination_type == destination_type
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
            'total_destinations': len(results['destinations']),
            'search_parameters': {
                'query': query,
                'type': search_type,
                'municipality': municipality,
                'property_type': property_type,
                'destination_type': destination_type
            }
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
            .filter(Property.municipality != '') \
            .distinct().all()

        # Get municipalities from destinations
        destination_municipalities = db.session.query(Destination.municipality) \
            .filter(Destination.municipality.isnot(None)) \
            .filter(Destination.municipality != '') \
            .distinct().all()

        # Combine and deduplicate
        municipalities = set()
        for (municipality,) in property_municipalities:
            if municipality and municipality.strip():
                municipalities.add(municipality.strip())

        for (municipality,) in destination_municipalities:
            if municipality and municipality.strip():
                municipalities.add(municipality.strip())

        # Sort municipalities alphabetically
        sorted_municipalities = sorted(list(municipalities))

        return jsonify({
            'success': True,
            'municipalities': sorted_municipalities,
            'total': len(sorted_municipalities)
        })

    except Exception as e:
        print(f"Error in get_municipalities: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching municipalities: {str(e)}'
        }), 500


@tourist_api_bp.route('/accommodation-types', methods=['GET'])
def get_accommodation_types():
    """Get all accommodation types available"""
    try:
        accommodation_types = db.session.query(Property.accommodation_type) \
            .filter(Property.status == 'ACTIVE') \
            .filter(Property.accommodation_type.isnot(None)) \
            .filter(Property.accommodation_type != '') \
            .distinct().all()

        types = []
        for (acc_type,) in accommodation_types:
            if acc_type and acc_type.strip():
                types.append(acc_type.strip())

        return jsonify({
            'success': True,
            'accommodation_types': sorted(types),
            'total': len(types)
        })

    except Exception as e:
        print(f"Error in get_accommodation_types: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching accommodation types: {str(e)}'
        }), 500


@tourist_api_bp.route('/destination-types', methods=['GET'])
def get_destination_types():
    """Get all destination types available"""
    try:
        destination_types = db.session.query(Destination.destination_type).distinct().all()

        types = []
        for (dest_type,) in destination_types:
            if dest_type:
                if hasattr(dest_type, 'value'):
                    types.append(dest_type.value)
                else:
                    types.append(str(dest_type))

        return jsonify({
            'success': True,
            'destination_types': sorted(list(set(types))),
            'total': len(set(types))
        })

    except Exception as e:
        print(f"Error in get_destination_types: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching destination types: {str(e)}'
        }), 500


# Template routes
@tourist_api_bp.route('/home')
def tourist_home():
    return render_template('TOURIST_Home.html')


@tourist_api_bp.route('/destinations')
def tourist_destinations():
    return render_template('TOURIST_Destination.html')


@tourist_api_bp.route('/map')
def tourist_map():
    return render_template('TOURIST_Map.html')


@tourist_api_bp.route('/events')
def tourist_events():
    return render_template('TOURIST_Event.html')


@tourist_api_bp.route('/about')
def tourist_about():
    return render_template('TOURIST_About.html')


@tourist_api_bp.route('/contact')
def tourist_contact():
    return render_template('TOURIST_Contact.html')


# Additional utility routes for enhanced functionality
@tourist_api_bp.route('/statistics', methods=['GET'])
def get_tourism_statistics():
    """Get basic tourism statistics for the homepage or dashboard"""
    try:
        # Count active properties
        total_properties = Property.query.filter(Property.status == 'ACTIVE').count()

        # Count destinations
        total_destinations = Destination.query.count()

        # Count featured destinations
        featured_destinations = Destination.query.filter(Destination.is_featured == True).count()

        # Count municipalities with properties
        municipalities_with_properties = db.session.query(Property.municipality) \
            .filter(Property.status == 'ACTIVE') \
            .filter(Property.municipality.isnot(None)) \
            .distinct().count()

        # Get accommodation type breakdown
        accommodation_breakdown = db.session.query(
            Property.accommodation_type,
            func.count(Property.property_id).label('count')
        ).filter(
            Property.status == 'ACTIVE',
            Property.accommodation_type.isnot(None)
        ).group_by(Property.accommodation_type).all()

        accommodation_stats = {}
        for acc_type, count in accommodation_breakdown:
            accommodation_stats[acc_type] = count

        # Get destination type breakdown
        destination_breakdown = db.session.query(
            Destination.destination_type,
            func.count(Destination.id).label('count')
        ).filter(
            Destination.destination_type.isnot(None)
        ).group_by(Destination.destination_type).all()

        destination_stats = {}
        for dest_type, count in destination_breakdown:
            type_value = dest_type.value if hasattr(dest_type, 'value') else str(dest_type)
            destination_stats[type_value] = count

        return jsonify({
            'success': True,
            'statistics': {
                'total_properties': total_properties,
                'total_destinations': total_destinations,
                'featured_destinations': featured_destinations,
                'municipalities_covered': municipalities_with_properties,
                'accommodation_breakdown': accommodation_stats,
                'destination_breakdown': destination_stats
            }
        })

    except Exception as e:
        print(f"Error in get_tourism_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching statistics: {str(e)}'
        }), 500


@tourist_api_bp.route('/featured', methods=['GET'])
def get_featured_content():
    """Get featured destinations and top properties"""
    try:
        # Get featured destinations
        featured_destinations = Destination.query.filter(
            Destination.is_featured == True
        ).order_by(Destination.name).limit(6).all()

        # Get top properties (you can modify this logic based on your criteria)
        top_properties = Property.query.filter(
            Property.status == 'ACTIVE'
        ).order_by(Property.property_name).limit(6).all()

        # Format featured destinations
        featured_dest_data = []
        for destination in featured_destinations:
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

            featured_dest_data.append({
                'id': destination.id,
                'name': destination.name or 'Unnamed Destination',
                'description': destination.description or 'Explore this amazing destination in Batangas.',
                'municipality': destination.municipality or 'Batangas',
                'destination_type': destination_type_value,
                'image_path': image_path,
                'latitude': float(destination.latitude) if destination.latitude else 0,
                'longitude': float(destination.longitude) if destination.longitude else 0
            })

        # Format top properties
        top_prop_data = []
        for property in top_properties:
            main_image = "/static/images/default-property.jpg"
            if property.images and len(property.images) > 0:
                image_filename = property.images[0].image_path
                if not image_filename.startswith('/'):
                    main_image = f"/static/uploads/properties/{image_filename}"
                else:
                    main_image = image_filename

            top_prop_data.append({
                'property_id': property.property_id,
                'property_name': property.property_name or 'Unnamed Property',
                'municipality': property.municipality or 'Batangas',
                'accommodation_type': property.accommodation_type or 'Property',
                'description': property.description or f'Beautiful {property.accommodation_type or "property"}',
                'main_image': main_image
            })

        return jsonify({
            'success': True,
            'featured_destinations': featured_dest_data,
            'top_properties': top_prop_data,
            'total_featured_destinations': len(featured_dest_data),
            'total_top_properties': len(top_prop_data)
        })

    except Exception as e:
        print(f"Error in get_featured_content: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching featured content: {str(e)}'
        }), 500


@tourist_api_bp.route('/properties/by-municipality/<municipality>', methods=['GET'])
def get_properties_by_municipality(municipality):
    """Get all properties in a specific municipality"""
    try:
        properties = Property.query.filter(
            Property.status == 'ACTIVE',
            func.lower(Property.municipality) == municipality.lower()
        ).all()

        properties_data = []
        for property in properties:
            main_image = "/static/images/default-property.jpg"
            if property.images and len(property.images) > 0:
                image_filename = property.images[0].image_path
                if not image_filename.startswith('/'):
                    main_image = f"/static/uploads/properties/{image_filename}"
                else:
                    main_image = image_filename

            # Get coordinates
            coordinates = None
            if property.coordinates and len(property.coordinates) > 0:
                coord = property.coordinates[0]
                coordinates = {
                    'latitude': float(coord.latitude) if coord.latitude else 0,
                    'longitude': float(coord.longitude) if coord.longitude else 0
                }

            properties_data.append({
                'property_id': property.property_id,
                'property_name': property.property_name or 'Unnamed Property',
                'barangay': property.barangay or '',
                'municipality': property.municipality or 'Batangas',
                'accommodation_type': property.accommodation_type or 'Property',
                'description': property.description or f'Beautiful {property.accommodation_type or "property"}',
                'main_image': main_image,
                'coordinates': coordinates
            })

        return jsonify({
            'success': True,
            'properties': properties_data,
            'municipality': municipality,
            'total': len(properties_data)
        })

    except Exception as e:
        print(f"Error in get_properties_by_municipality: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching properties for {municipality}: {str(e)}'
        }), 500


@tourist_api_bp.route('/destinations/by-municipality/<municipality>', methods=['GET'])
def get_destinations_by_municipality(municipality):
    """Get all destinations in a specific municipality"""
    try:
        destinations = Destination.query.filter(
            func.lower(Destination.municipality) == municipality.lower()
        ).order_by(desc(Destination.is_featured), Destination.name).all()

        destinations_data = []
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

            destinations_data.append({
                'id': destination.id,
                'name': destination.name or 'Unnamed Destination',
                'description': destination.description or 'Explore this amazing destination in Batangas.',
                'location_name': destination.location_name or destination.municipality,
                'municipality': destination.municipality or 'Batangas',
                'barangay': destination.barangay or '',
                'destination_type': destination_type_value,
                'image_path': image_path,
                'is_featured': destination.is_featured or False,
                'latitude': float(destination.latitude) if destination.latitude else 0,
                'longitude': float(destination.longitude) if destination.longitude else 0
            })

        return jsonify({
            'success': True,
            'destinations': destinations_data,
            'municipality': municipality,
            'total': len(destinations_data)
        })

    except Exception as e:
        print(f"Error in get_destinations_by_municipality: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching destinations for {municipality}: {str(e)}'
        }), 500