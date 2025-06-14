from flask import Blueprint, jsonify, request, render_template, url_for, redirect, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from extension import db
from model import Property, User, LongLat, Amenity, Room
from sqlalchemy.exc import SQLAlchemyError
import json

destinations_bp = Blueprint('destinations', __name__)


def init_destinations_routes(app):
    app.register_blueprint(destinations_bp)


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


@destinations_bp.route('/api/destinations/map-data')
@jwt_required()
def get_map_data():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or not user.municipality:
            return jsonify({'success': False, 'message': 'User municipality not found'}), 400

        # Get filter parameters
        search = request.args.get('search', '')
        property_type = request.args.get('type', '')
        barangay = request.args.get('barangay', '')

        # Base query
        query = Property.query.filter_by(municipality=user.municipality, status='Active')

        # Apply filters
        if search:
            query = query.filter(Property.property_name.ilike(f'%{search}%'))
        if property_type and property_type != 'All Types':
            query = query.filter(Property.accommodation_type == property_type)
        if barangay and barangay != 'All Barangays':
            query = query.filter(Property.barangay == barangay)

        properties = query.all()

        # Prepare response data
        result = []
        for prop in properties:
            # Get coordinates
            coords = LongLat.query.filter_by(property_id=prop.property_id).first()
            if not coords:
                continue

            # Get amenities
            amenities = [a.amenity for a in prop.amenities]

            # Get price range from rooms
            rooms = Room.query.filter_by(property_id=prop.property_id).all()
            min_price = min([r.overnight_price for r in rooms]) if rooms else 0
            max_price = max([r.overnight_price for r in rooms]) if rooms else 0

            result.append({
                'id': prop.property_id,
                'name': prop.property_name,
                'type': prop.accommodation_type,
                'location': f"{prop.barangay}, {prop.municipality}",
                'price': float(min_price) if min_price else 0,
                'rating': 4.5,  # Placeholder - would come from reviews in a real app
                'image': f"/static/uploads/properties/{prop.property_id}.jpg",  # Placeholder path
                'description': prop.description or "No description available",
                'amenities': amenities,
                'coordinates': [float(coords.latitude), float(coords.longitude)],
                'phone': "09123456789",  # Placeholder - would come from contact info in a real app
                'email': "info@example.com",  # Placeholder
                'website': "www.example.com",  # Placeholder
                'overnightRate': f"₱{min_price:,.2f} - ₱{max_price:,.2f}" if min_price and max_price else "Not available",
                'dayTourRate': "₱500 - ₱2,000",  # Placeholder
                'gallery': [
                    f"/static/uploads/properties/{prop.property_id}_1.jpg",  # Placeholder paths
                    f"/static/uploads/properties/{prop.property_id}_2.jpg"
                ]
            })

        return jsonify({
            'success': True,
            'properties': result,
            'municipality': user.municipality
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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