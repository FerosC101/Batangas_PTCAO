from flask import Blueprint, jsonify, request, render_template, current_app, url_for, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload
from extension import db
from model import Property, LongLat, Amenity, Room, PropertyImage
from datetime import datetime
import logging

ptcao_destinations_bp = Blueprint('ptcao_destinations', __name__)

def init_ptcao_destinations_routes(app):
    app.register_blueprint(ptcao_destinations_bp)

@ptcao_destinations_bp.route('/ptcao/destinations')
@jwt_required()
def ptcao_destinations():
    """Render the PTCAO Destinations page with map view"""
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != "ptcao":
            return redirect(url_for('login'))

        return render_template('PTCAO_Destinations.html')
    except Exception as e:
        current_app.logger.error(f"Error loading PTCAO destinations: {str(e)}")
        return redirect(url_for('login'))

@ptcao_destinations_bp.route('/api/ptcao/destinations/map-data')
@jwt_required()
def get_ptcao_map_data():
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != "ptcao":
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        # Query all active properties with their relationships
        properties = db.session.query(Property).filter(
            Property.status == 'ACTIVE'
        ).options(
            joinedload(Property.coordinates),
            joinedload(Property.amenities),
            joinedload(Property.images)
        ).all()

        result = []
        for prop in properties:
            if not prop.coordinates:
                continue  # Skip properties without coordinates

            # Get the first coordinate pair
            coord = prop.coordinates[0] if prop.coordinates else None
            if not coord:
                continue

            # Get property-level amenities (limit to 3)
            amenities = [a.amenity for a in prop.amenities if a.room_id is None][:3]

            # Get the first image if available
            image_url = None
            if prop.images and len(prop.images) > 0:
                image_url = url_for('static', filename=f'uploads/events/{prop.images[0].image_path}')

            # Get the lowest price from rooms
            min_price = 0
            if prop.rooms:
                prices = [r.overnight_price for r in prop.rooms if r.overnight_price is not None]
                min_price = min(prices) if prices else 0

            result.append({
                'id': prop.property_id,
                'name': prop.property_name,
                'type': prop.accommodation_type or 'Not specified',
                'location': f"{prop.barangay or ''}, {prop.municipality or ''}",
                'price': float(min_price),
                'image': image_url,
                'coordinates': [float(coord.latitude), float(coord.longitude)],
                'amenities': amenities,
                'municipality': prop.municipality
            })

        return jsonify({
            'success': True,
            'properties': result
        })

    except Exception as e:
        current_app.logger.error(f"Error in get_ptcao_map_data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load property data'
        }), 500

@ptcao_destinations_bp.route('/api/ptcao/destinations/filter-options')
@jwt_required()
def get_ptcao_filter_options():
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != "ptcao":
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        # Get all unique property types
        types = db.session.query(Property.accommodation_type).filter(
            Property.accommodation_type.isnot(None)
        ).distinct().all()

        # Get all unique municipalities
        municipalities = db.session.query(Property.municipality).filter(
            Property.municipality.isnot(None)
        ).distinct().all()

        return jsonify({
            'success': True,
            'types': [t[0] for t in types],
            'municipalities': [m[0] for m in municipalities]
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500