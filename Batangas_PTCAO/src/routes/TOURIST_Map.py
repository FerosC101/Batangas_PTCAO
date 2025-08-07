from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import Property, Destination, LongLat, PropertyImage, Room, Amenity, DestinationType, \
    PropertyStatus


def init_tourist_map_routes(app):
    """Initialize the tourist map routes"""

    @app.route('/api/map/properties', methods=['GET'])
    def get_map_properties():
        """Get all properties with coordinates for the map"""
        try:
            # Get query parameters for filtering
            municipality = request.args.get('municipality', '')
            accommodation_type = request.args.get('accommodation_type', '')
            status = request.args.get('status', 'ACTIVE')

            # Base query with joins
            query = db.session.query(Property) \
                .join(LongLat, Property.property_id == LongLat.property_id) \
                .filter(Property.status == PropertyStatus.ACTIVE) \
                .options(
                joinedload(Property.coordinates),
                joinedload(Property.images),
                joinedload(Property.rooms),
                joinedload(Property.amenities)
            )

            # Apply filters
            if municipality:
                query = query.filter(Property.municipality.ilike(f'%{municipality}%'))

            if accommodation_type:
                query = query.filter(Property.accommodation_type.ilike(f'%{accommodation_type}%'))

            properties = query.all()

            properties_data = []
            for prop in properties:
                # Get the first coordinate (assuming one coordinate per property)
                coordinate = prop.coordinates[0] if prop.coordinates else None
                if not coordinate:
                    continue

                # Get the first image
                image_url = None
                if prop.images:
                    image_url = f"/static/uploads/properties/{prop.images[0].image_path}"
                else:
                    # Default image based on accommodation type
                    default_images = {
                        'resort': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                        'hotel': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                        'pension house': 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                        'transient house': 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
                    }
                    image_url = default_images.get(prop.accommodation_type.lower(),
                                                   'https://images.unsplash.com/photo-1571896349842-33c89424de2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80')

                # Get room information
                rooms_info = []
                min_price = None
                max_capacity = 0

                for room in prop.rooms:
                    room_data = {
                        'room_type': room.room_type,
                        'day_price': float(room.day_price) if room.day_price else None,
                        'overnight_price': float(room.overnight_price) if room.overnight_price else None,
                        'capacity': room.capacity or 0
                    }
                    rooms_info.append(room_data)

                    # Calculate min price and max capacity
                    if room.day_price:
                        if min_price is None or float(room.day_price) < min_price:
                            min_price = float(room.day_price)
                    if room.overnight_price:
                        if min_price is None or float(room.overnight_price) < min_price:
                            min_price = float(room.overnight_price)

                    if room.capacity and room.capacity > max_capacity:
                        max_capacity = room.capacity

                # Get amenities
                amenities_list = [amenity.amenity for amenity in prop.amenities]

                # Determine category based on accommodation type
                category_mapping = {
                    'resort': 'resort',
                    'hotel': 'accommodation',
                    'pension house': 'accommodation',
                    'transient house': 'accommodation'
                }
                category = category_mapping.get(prop.accommodation_type.lower(), 'accommodation')

                property_data = {
                    'id': prop.property_id,
                    'name': prop.property_name,
                    'location': f"{prop.barangay}, {prop.municipality}" if prop.barangay else prop.municipality,
                    'municipality': prop.municipality,
                    'barangay': prop.barangay,
                    'lat': coordinate.latitude,
                    'lng': coordinate.longitude,
                    'image': image_url,
                    'description': prop.description or f"Experience the best of {prop.accommodation_type.lower()} accommodation in {prop.municipality}.",
                    'accommodation_type': prop.accommodation_type,
                    'category': category,
                    'status': prop.status.value,
                    'rooms': rooms_info,
                    'amenities': amenities_list,
                    'min_price': min_price,
                    'max_capacity': max_capacity,
                    'tags': [prop.accommodation_type.lower().replace(' ', '_'), category] + amenities_list[:3]
                    # First 3 amenities as tags
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

    @app.route('/api/map/destinations', methods=['GET'])
    def get_map_destinations():
        """Get all destinations with coordinates for the map"""
        try:
            # Get query parameters for filtering
            municipality = request.args.get('municipality', '')
            destination_type = request.args.get('destination_type', '')
            featured_only = request.args.get('featured_only', 'false').lower() == 'true'

            # Base query
            query = db.session.query(Destination)

            # Apply filters
            if municipality:
                query = query.filter(Destination.municipality.ilike(f'%{municipality}%'))

            if destination_type:
                query = query.filter(Destination.destination_type == DestinationType(destination_type))

            if featured_only:
                query = query.filter(Destination.is_featured == True)

            destinations = query.all()

            destinations_data = []
            for dest in destinations:
                # Default image based on destination type
                default_images = {
                    DestinationType.MOUNTAIN: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                    DestinationType.BEACH: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                    DestinationType.ISLAND: 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                    DestinationType.HERITAGE: 'https://images.unsplash.com/photo-1571501679680-de32f1e7aad4?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                    DestinationType.OTHER: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
                }

                image_url = dest.image_path if dest.image_path else default_images.get(dest.destination_type,
                                                                                       default_images[
                                                                                           DestinationType.OTHER])
                if dest.image_path and not dest.image_path.startswith('http'):
                    image_url = f"/static/uploads/destinations/{dest.image_path}"

                # Generate tags based on destination type
                type_tags = {
                    DestinationType.MOUNTAIN: ['hiking', 'nature', 'adventure', 'scenic views'],
                    DestinationType.BEACH: ['beach', 'swimming', 'relaxation', 'water sports'],
                    DestinationType.ISLAND: ['island', 'swimming', 'snorkeling', 'photography'],
                    DestinationType.HERITAGE: ['heritage', 'culture', 'architecture', 'history'],
                    DestinationType.OTHER: ['nature', 'adventure', 'sightseeing']
                }

                destination_data = {
                    'id': dest.id,
                    'name': dest.name,
                    'location': dest.location_name,
                    'municipality': dest.municipality,
                    'barangay': dest.barangay,
                    'lat': dest.latitude,
                    'lng': dest.longitude,
                    'image': image_url,
                    'description': dest.description,
                    'destination_type': dest.destination_type.value,
                    'category': dest.destination_type.value.lower(),
                    'is_featured': dest.is_featured,
                    'tags': type_tags.get(dest.destination_type, ['nature'])
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

    @app.route('/api/map/combined', methods=['GET'])
    def get_combined_map_data():
        """Get both properties and destinations for the map"""
        try:
            # Get query parameters
            municipality = request.args.get('municipality', '')
            category_filter = request.args.get('category',
                                               'all')  # all, accommodation, destination, mountain, beach, heritage

            combined_data = []

            # Fetch properties
            prop_query = db.session.query(Property) \
                .join(LongLat, Property.property_id == LongLat.property_id) \
                .filter(Property.status == PropertyStatus.ACTIVE) \
                .options(
                joinedload(Property.coordinates),
                joinedload(Property.images),
                joinedload(Property.rooms),
                joinedload(Property.amenities)
            )

            if municipality:
                prop_query = prop_query.filter(Property.municipality.ilike(f'%{municipality}%'))

            properties = prop_query.all()

            # Process properties
            for prop in properties:
                coordinate = prop.coordinates[0] if prop.coordinates else None
                if not coordinate:
                    continue

                # Determine if this property should be included based on category filter
                prop_category = 'accommodation'
                if category_filter != 'all' and category_filter != 'accommodation':
                    continue

                # Get image
                image_url = None
                if prop.images:
                    image_url = f"/static/uploads/properties/{prop.images[0].image_path}"
                else:
                    default_images = {
                        'resort': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                        'hotel': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                        'pension house': 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
                    }
                    image_url = default_images.get(prop.accommodation_type.lower(),
                                                   'https://images.unsplash.com/photo-1571896349842-33c89424de2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80')

                # Get min price
                min_price = None
                for room in prop.rooms:
                    if room.day_price:
                        if min_price is None or float(room.day_price) < min_price:
                            min_price = float(room.day_price)
                    if room.overnight_price:
                        if min_price is None or float(room.overnight_price) < min_price:
                            min_price = float(room.overnight_price)

                amenities_list = [amenity.amenity for amenity in prop.amenities]

                combined_data.append({
                    'id': f'property_{prop.property_id}',
                    'type': 'property',
                    'name': prop.property_name,
                    'location': f"{prop.barangay}, {prop.municipality}" if prop.barangay else prop.municipality,
                    'municipality': prop.municipality,
                    'barangay': prop.barangay,
                    'lat': coordinate.latitude,
                    'lng': coordinate.longitude,
                    'image': image_url,
                    'description': prop.description or f"Experience the best of {prop.accommodation_type.lower()} accommodation in {prop.municipality}.",
                    'category': 'accommodation',
                    'accommodation_type': prop.accommodation_type,
                    'min_price': min_price,
                    'amenities': amenities_list,
                    'tags': [prop.accommodation_type.lower().replace(' ', '_'), 'accommodation'] + amenities_list[:3]
                })

            # Fetch destinations
            dest_query = db.session.query(Destination)

            if municipality:
                dest_query = dest_query.filter(Destination.municipality.ilike(f'%{municipality}%'))

            destinations = dest_query.all()

            # Process destinations
            for dest in destinations:
                # Determine if this destination should be included based on category filter
                dest_category = dest.destination_type.value.lower()
                if category_filter != 'all' and category_filter != dest_category and category_filter != 'destination':
                    continue

                default_images = {
                    DestinationType.MOUNTAIN: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                    DestinationType.BEACH: 'https://images.unsplash.com/photo-1544551763-46a013bb70d5?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                    DestinationType.ISLAND: 'https://images.unsplash.com/photo-1559827260-dc66d52bef19?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                    DestinationType.HERITAGE: 'https://images.unsplash.com/photo-1571501679680-de32f1e7aad4?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
                    DestinationType.OTHER: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
                }

                image_url = dest.image_path if dest.image_path else default_images.get(dest.destination_type,
                                                                                       default_images[
                                                                                           DestinationType.OTHER])
                if dest.image_path and not dest.image_path.startswith('http'):
                    image_url = f"/static/uploads/destinations/{dest.image_path}"

                type_tags = {
                    DestinationType.MOUNTAIN: ['hiking', 'nature', 'adventure', 'scenic views'],
                    DestinationType.BEACH: ['beach', 'swimming', 'relaxation', 'water sports'],
                    DestinationType.ISLAND: ['island', 'swimming', 'snorkeling', 'photography'],
                    DestinationType.HERITAGE: ['heritage', 'culture', 'architecture', 'history'],
                    DestinationType.OTHER: ['nature', 'adventure', 'sightseeing']
                }

                combined_data.append({
                    'id': f'destination_{dest.id}',
                    'type': 'destination',
                    'name': dest.name,
                    'location': dest.location_name,
                    'municipality': dest.municipality,
                    'barangay': dest.barangay,
                    'lat': dest.latitude,
                    'lng': dest.longitude,
                    'image': image_url,
                    'description': dest.description,
                    'category': dest_category,
                    'destination_type': dest.destination_type.value,
                    'is_featured': dest.is_featured,
                    'tags': type_tags.get(dest.destination_type, ['nature'])
                })

            return jsonify({
                'success': True,
                'data': combined_data,
                'total': len(combined_data),
                'properties_count': len([item for item in combined_data if item['type'] == 'property']),
                'destinations_count': len([item for item in combined_data if item['type'] == 'destination'])
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error fetching combined map data: {str(e)}'
            }), 500

    @app.route('/api/map/municipalities', methods=['GET'])
    def get_municipalities():
        """Get list of municipalities that have properties or destinations"""
        try:
            # Get municipalities from properties
            property_municipalities = db.session.query(Property.municipality) \
                .filter(Property.status == PropertyStatus.ACTIVE) \
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

    @app.route('/api/map/property/<int:property_id>', methods=['GET'])
    def get_property_details(property_id):
        """Get detailed information about a specific property"""
        try:
            property_obj = db.session.query(Property) \
                .options(
                joinedload(Property.coordinates),
                joinedload(Property.images),
                joinedload(Property.rooms),
                joinedload(Property.amenities)
            ) \
                .filter(Property.property_id == property_id) \
                .first()

            if not property_obj:
                return jsonify({
                    'success': False,
                    'message': 'Property not found'
                }), 404

            coordinate = property_obj.coordinates[0] if property_obj.coordinates else None

            # Get all images
            images = []
            for img in property_obj.images:
                images.append(f"/static/uploads/properties/{img.image_path}")

            # Get all rooms with details
            rooms = []
            for room in property_obj.rooms:
                room_amenities = [amenity.amenity for amenity in room.amenities]
                rooms.append({
                    'room_id': room.room_id,
                    'room_type': room.room_type,
                    'day_price': float(room.day_price) if room.day_price else None,
                    'overnight_price': float(room.overnight_price) if room.overnight_price else None,
                    'capacity': room.capacity,
                    'amenities': room_amenities
                })

            # Get property amenities
            property_amenities = [amenity.amenity for amenity in property_obj.amenities]

            property_details = {
                'id': property_obj.property_id,
                'name': property_obj.property_name,
                'location': f"{property_obj.barangay}, {property_obj.municipality}" if property_obj.barangay else property_obj.municipality,
                'municipality': property_obj.municipality,
                'barangay': property_obj.barangay,
                'lat': coordinate.latitude if coordinate else None,
                'lng': coordinate.longitude if coordinate else None,
                'description': property_obj.description,
                'accommodation_type': property_obj.accommodation_type,
                'status': property_obj.status.value,
                'images': images,
                'rooms': rooms,
                'amenities': property_amenities
            }

            return jsonify({
                'success': True,
                'property': property_details
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error fetching property details: {str(e)}'
            }), 500

    @app.route('/api/map/destination/<int:destination_id>', methods=['GET'])
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

            image_url = destination.image_path if destination.image_path else None
            if destination.image_path and not destination.image_path.startswith('http'):
                image_url = f"/static/uploads/destinations/{destination.image_path}"

            destination_details = {
                'id': destination.id,
                'name': destination.name,
                'location': destination.location_name,
                'municipality': destination.municipality,
                'barangay': destination.barangay,
                'lat': destination.latitude,
                'lng': destination.longitude,
                'description': destination.description,
                'destination_type': destination.destination_type.value,
                'is_featured': destination.is_featured,
                'image': image_url
            }

            return jsonify({
                'success': True,
                'destination': destination_details
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error fetching destination details: {str(e)}'
            }), 500