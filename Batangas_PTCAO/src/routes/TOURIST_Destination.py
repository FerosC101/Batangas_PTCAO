# Add this to your existing routes or create a new file: TOURIST_API.py

from flask import Blueprint, jsonify, request
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import Property, PropertyImage, Room, Amenity, Destination, LongLat
from sqlalchemy import func, desc
import os


def init_tourist_api_routes(app):
    @app.route('/api/tourist/properties', methods=['GET'])
    def get_tourist_properties():
        """Get all active properties with their details for tourists"""
        try:
            # Query properties with related data
            properties = db.session.query(Property) \
                .filter(Property.status == 'ACTIVE') \
                .all()

            properties_data = []

            for property in properties:
                # Get the main image (first image)
                main_image = None
                if property.images:
                    main_image = f"/static/uploads/properties/{property.images[0].image_path}"

                # Get amenities
                amenities = [{'amenity': amenity.amenity} for amenity in property.amenities]

                # Get rooms
                rooms = []
                total_rooms = 0
                price_range = None

                for room in property.rooms:
                    room_data = {
                        'room_type': room.room_type,
                        'capacity': room.capacity,
                        'day_price': float(room.day_price) if room.day_price else None,
                        'overnight_price': float(room.overnight_price) if room.overnight_price else None
                    }
                    rooms.append(room_data)
                    total_rooms += 1

                # Calculate price range from rooms
                if rooms:
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

                # Get coordinates
                coordinates = None
                if property.coordinates:
                    coord = property.coordinates[0]
                    coordinates = {
                        'latitude': coord.latitude,
                        'longitude': coord.longitude
                    }

                property_data = {
                    'property_id': property.property_id,
                    'property_name': property.property_name,
                    'barangay': property.barangay,
                    'municipality': property.municipality,
                    'accommodation_type': property.accommodation_type,
                    'status': property.status.value,
                    'description': property.description,
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
            return jsonify({
                'success': False,
                'message': f'Error fetching properties: {str(e)}'
            }), 500

    @app.route('/api/tourist/destinations', methods=['GET'])
    def get_tourist_destinations():
        """Get all destinations for tourists"""
        try:
            # Query all destinations, featured first
            destinations = db.session.query(Destination) \
                .order_by(desc(Destination.is_featured), Destination.name) \
                .all()

            destinations_data = []

            for destination in destinations:
                # Get the image path
                image_path = None
                if destination.image_path:
                    image_path = f"/static/uploads/destinations/{destination.image_path}"

                destination_data = {
                    'id': destination.id,
                    'name': destination.name,
                    'description': destination.description,
                    'location_name': destination.location_name,
                    'longitude': destination.longitude,
                    'latitude': destination.latitude,
                    'barangay': destination.barangay,
                    'municipality': destination.municipality,
                    'destination_type': destination.destination_type.value,
                    'image_path': image_path,
                    'is_featured': destination.is_featured,
                    'created_at': destination.created_at.isoformat() if destination.created_at else None
                }

                destinations_data.append(destination_data)

            return jsonify({
                'success': True,
                'destinations': destinations_data,
                'total': len(destinations_data)
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error fetching destinations: {str(e)}'
            }), 500

    @app.route('/api/tourist/property/<int:property_id>', methods=['GET'])
    def get_property_details(property_id):
        """Get detailed information about a specific property"""
        try:
            property = db.session.query(Property) \
                .filter(Property.property_id == property_id) \
                .first()

            if not property:
                return jsonify({
                    'success': False,
                    'message': 'Property not found'
                }), 404

            # Get all images
            images = []
            if property.images:
                for img in property.images:
                    images.append(f"/static/uploads/properties/{img.image_path}")

            # Get amenities
            amenities = [{'amenity': amenity.amenity} for amenity in property.amenities]

            # Get rooms with amenities
            rooms = []
            for room in property.rooms:
                room_amenities = [{'amenity': amenity.amenity} for amenity in room.amenities]
                room_data = {
                    'room_id': room.room_id,
                    'room_type': room.room_type,
                    'capacity': room.capacity,
                    'day_price': float(room.day_price) if room.day_price else None,
                    'overnight_price': float(room.overnight_price) if room.overnight_price else None,
                    'amenities': room_amenities
                }
                rooms.append(room_data)

            # Get coordinates
            coordinates = None
            if property.coordinates:
                coord = property.coordinates[0]
                coordinates = {
                    'latitude': coord.latitude,
                    'longitude': coord.longitude
                }

            # Get typical locations
            typical_locations = []
            if property.typical_locations:
                typical_locations = [loc.location for loc in property.typical_locations]

            property_data = {
                'property_id': property.property_id,
                'property_name': property.property_name,
                'barangay': property.barangay,
                'municipality': property.municipality,
                'accommodation_type': property.accommodation_type,
                'status': property.status.value,
                'description': property.description,
                'images': images,
                'main_image': images[0] if images else None,
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
            return jsonify({
                'success': False,
                'message': f'Error fetching property details: {str(e)}'
            }), 500

    @app.route('/api/tourist/destination/<int:destination_id>', methods=['GET'])
    def get_destination_details(destination_id):
        """Get detailed information about a specific destination"""
        try:
            destination = db.session.query(Destination) \
                .filter(Destination.id == destination_id) \
                .first()

            if not destination:
                return jsonify({
                    'success': False,
                    'message': 'Destination not found'
                }), 404

            # Get the image path
            image_path = None
            if destination.image_path:
                image_path = f"/static/uploads/destinations/{destination.image_path}"

            destination_data = {
                'id': destination.id,
                'name': destination.name,
                'description': destination.description,
                'location_name': destination.location_name,
                'longitude': destination.longitude,
                'latitude': destination.latitude,
                'barangay': destination.barangay,
                'municipality': destination.municipality,
                'destination_type': destination.destination_type.value,
                'image_path': image_path,
                'is_featured': destination.is_featured,
                'created_at': destination.created_at.isoformat() if destination.created_at else None,
                'updated_at': destination.updated_at.isoformat() if destination.updated_at else None
            }

            return jsonify({
                'success': True,
                'destination': destination_data
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error fetching destination details: {str(e)}'
            }), 500

    @app.route('/api/tourist/search', methods=['GET'])
    def search_properties_and_destinations():
        """Search both properties and destinations"""
        try:
            query = request.args.get('q', '').strip().lower()
            property_type = request.args.get('type', 'all')  # all, properties, destinations
            municipality = request.args.get('municipality', '')

            results = {
                'properties': [],
                'destinations': []
            }

            if property_type in ['all', 'properties']:
                # Search properties
                property_query = db.session.query(Property) \
                    .filter(Property.status == 'ACTIVE')

                if query:
                    property_query = property_query.filter(
                        func.lower(Property.property_name).contains(query) |
                        func.lower(Property.description).contains(query) |
                        func.lower(Property.municipality).contains(query) |
                        func.lower(Property.barangay).contains(query)
                    )

                if municipality:
                    property_query = property_query.filter(
                        func.lower(Property.municipality) == municipality.lower()
                    )

                properties = property_query.limit(20).all()

                for property in properties:
                    main_image = None
                    if property.images:
                        main_image = f"/static/uploads/properties/{property.images[0].image_path}"

                    results['properties'].append({
                        'property_id': property.property_id,
                        'property_name': property.property_name,
                        'barangay': property.barangay,
                        'municipality': property.municipality,
                        'accommodation_type': property.accommodation_type,
                        'description': property.description,
                        'main_image': main_image,
                        'type': 'property'
                    })

            if property_type in ['all', 'destinations']:
                # Search destinations
                destination_query = db.session.query(Destination)

                if query:
                    destination_query = destination_query.filter(
                        func.lower(Destination.name).contains(query) |
                        func.lower(Destination.description).contains(query) |
                        func.lower(Destination.municipality).contains(query) |
                        func.lower(Destination.barangay).contains(query)
                    )

                if municipality:
                    destination_query = destination_query.filter(
                        func.lower(Destination.municipality) == municipality.lower()
                    )

                destinations = destination_query.limit(20).all()

                for destination in destinations:
                    image_path = None
                    if destination.image_path:
                        image_path = f"/static/uploads/destinations/{destination.image_path}"

                    results['destinations'].append({
                        'id': destination.id,
                        'name': destination.name,
                        'location_name': destination.location_name,
                        'municipality': destination.municipality,
                        'barangay': destination.barangay,
                        'destination_type': destination.destination_type.value,
                        'description': destination.description,
                        'image_path': image_path,
                        'is_featured': destination.is_featured,
                        'type': 'destination'
                    })

            return jsonify({
                'success': True,
                'results': results,
                'total_properties': len(results['properties']),
                'total_destinations': len(results['destinations'])
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error searching: {str(e)}'
            }), 500

    @app.route('/api/tourist/municipalities', methods=['GET'])
    def get_municipalities():
        """Get all municipalities that have properties or destinations"""
        try:
            # Get municipalities from properties
            property_municipalities = db.session.query(Property.municipality) \
                .filter(Property.status == 'ACTIVE') \
                .distinct().all()

            # Get municipalities from destinations
            destination_municipalities = db.session.query(Destination.municipality) \
                .distinct().all()

            # Combine and deduplicate
            municipalities = set()
            for (municipality,) in property_municipalities:
                if municipality:
                    municipalities.add(municipality)

            for (municipality,) in destination_municipalities:
                if municipality:
                    municipalities.add(municipality)

            return jsonify({
                'success': True,
                'municipalities': sorted(list(municipalities))
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error fetching municipalities: {str(e)}'
            }), 500