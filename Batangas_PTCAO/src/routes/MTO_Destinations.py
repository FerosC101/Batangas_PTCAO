from flask import Blueprint, jsonify, request, render_template, url_for, redirect, flash, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload

from extension import db
from model import Property, User, LongLat, Amenity, Room
from sqlalchemy.exc import SQLAlchemyError
import json

destinations_bp = Blueprint('destinations', __name__)


def init_destinations_routes(app):
    app.register_blueprint(destinations_bp)


@destinations_bp.route('/api/destinations/map-data')
@jwt_required()
def get_map_data():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.municipality:
            return jsonify({
                'success': False,
                'message': 'User municipality not found'
            }), 400

        # Updated query with proper eager loading
        properties = Property.query.filter_by(
            municipality=user.municipality,
            status='ACTIVE'
        ).options(
            joinedload(Property.coordinates),
            joinedload(Property.amenities),
            joinedload(Property.rooms),
            joinedload(Property.images)  # Load images
        ).all()

        result = []
        for prop in properties:
            if not prop.coordinates:
                continue

            coord = prop.coordinates[0]

            # Get prices
            prices = [r.overnight_price for r in prop.rooms if r.overnight_price is not None]
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0

            # Get amenities
            amenities = [a.amenity for a in prop.amenities if a.room_id is None]

            # Get first image if available
            image = None
            if prop.images and len(prop.images) > 0:
                image = url_for('static', filename=f'uploads/events/{prop.images[0].image_path}')

            result.append({
                'id': prop.property_id,
                'name': prop.property_name,
                'type': prop.accommodation_type,
                'location': f"{prop.barangay}, {prop.municipality}",
                'price': float(min_price),
                'rating': 4.5,
                'image': image,  # Use the image path
                'coordinates': [float(coord.latitude), float(coord.longitude)],
                'amenities': amenities
            })

        return jsonify({
            'success': True,
            'properties': result,
            'municipality': user.municipality
        })

    except Exception as e:
        current_app.logger.error(f"Error in get_map_data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load property data'
        }), 500

@destinations_bp.route('/api/debug/properties')
def debug_properties():
    """Endpoint for debugging property data"""
    props = Property.query.limit(5).all()
    return jsonify({
        'count': len(props),
        'properties': [{
            'id': p.property_id,
            'name': p.property_name,
            'status': p.status.value,
            'has_coords': bool(p.coordinates),
            'image': bool(p.property_image),
            'municipality': p.municipality
        } for p in props]
    })
@destinations_bp.route('/mto/destinations')
@jwt_required()
def mto_destinations():
    """Render the MTO Destinations page with map view"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.municipality:
            flash('User municipality not found', 'error')
            return redirect(url_for('dashboard.mto_dashboard'))

        return render_template(
            'MTO_Destinations.html',
            user_id=current_user_id,
            municipality=user.municipality
        )

    except Exception as e:
        flash(f'Failed to load destinations: {str(e)}', 'error')
        return redirect(url_for('dashboard.mto_dashboard'))



@destinations_bp.route('/api/destinations/filter-options')
@jwt_required()
def get_filter_options():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.municipality:
            return jsonify({'success': False, 'message': 'User municipality not found'}), 400

        # Get unique property types in the municipality
        types = db.session.query(Property.accommodation_type).filter(
            Property.municipality == user.municipality,
            Property.accommodation_type.isnot(None)
        ).distinct().all()

        # Get unique barangays in the municipality
        barangays = db.session.query(Property.barangay).filter(
            Property.municipality == user.municipality,
            Property.barangay.isnot(None)
        ).distinct().all()

        return jsonify({
            'success': True,
            'types': [t[0] for t in types],
            'barangays': [b[0] for b in barangays]
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500