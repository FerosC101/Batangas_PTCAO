# Debug version of PTCAO_Property.py with extensive logging

from flask import Blueprint, jsonify, request, render_template, redirect, flash, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from Batangas_PTCAO.src.model import Property, Room, Amenity, TypicalLocation, LongLat, PropertyStatus, User, \
    PropertyImage, PropertyReport
from Batangas_PTCAO.src.extension import db
from sqlalchemy.exc import SQLAlchemyError
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ptcao_properties_bp = Blueprint("ptcao_properties", __name__, url_prefix='/ptcao')


def init_ptcao_property_routes(app):
    app.register_blueprint(ptcao_properties_bp)


@ptcao_properties_bp.route('/properties')
@jwt_required()
def ptcao_properties():
    """Render the PTCAO Properties page with the list of all properties"""
    logger.debug("=== PTCAO Properties Route Called ===")

    try:
        # Debug: Check if JWT is present
        logger.debug("Attempting to verify JWT...")
        verify_jwt_in_request()
        logger.debug("JWT verification successful")

        # Debug: Get current user
        current_user_id = get_jwt_identity()
        logger.debug(f"Current user ID: {current_user_id}")
        logger.debug(f"User ID type: {type(current_user_id)}")

        # Debug: Check authorization
        if current_user_id != "ptcao":
            logger.warning(f"Authorization failed. Expected 'ptcao', got '{current_user_id}'")
            flash('Unauthorized access', 'error')
            return redirect(url_for('ptcao_dashboard.ptcao_dashboard'))

        logger.debug("Authorization successful, proceeding to load properties...")

        # Debug: Query properties
        properties = Property.query.all()
        logger.debug(f"Found {len(properties)} properties")

        typical_locations = [
            "Beachfront", "Mountain View", "City Center", "Lakeside",
            "Riverside", "Forest", "Countryside", "Island"
        ]

        logger.debug("About to render template...")

        return render_template(
            'PTCAO_Properties.html',
            properties=properties,
            user_id=current_user_id,
            typical_locations=typical_locations
        )

    except Exception as e:
        logger.error(f"Error in ptcao_properties route: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Failed to load properties: {str(e)}', 'error')
        return redirect(url_for('ptcao_dashboard.ptcao_dashboard'))


# Alternative version without JWT for testing
@ptcao_properties_bp.route('/properties-test')
def ptcao_properties_test():
    """Test version without JWT to check if route works"""
    logger.debug("=== PTCAO Properties TEST Route Called ===")

    try:
        properties = Property.query.all()
        logger.debug(f"Found {len(properties)} properties")

        typical_locations = [
            "Beachfront", "Mountain View", "City Center", "Lakeside",
            "Riverside", "Forest", "Countryside", "Island"
        ]

        return render_template(
            'PTCAO_Properties.html',
            properties=properties,
            user_id="ptcao",  # Hardcoded for testing
            typical_locations=typical_locations
        )

    except Exception as e:
        logger.error(f"Error in ptcao_properties_test route: {str(e)}")
        return f"Error: {str(e)}", 500


# Debug route to check JWT status
@ptcao_properties_bp.route('/debug-jwt')
def debug_jwt():
    """Debug route to check JWT status"""
    try:
        from flask_jwt_extended import get_jwt, get_current_user

        # Try to get JWT without requiring it
        try:
            verify_jwt_in_request(optional=True)
            current_user = get_jwt_identity()
            jwt_data = get_jwt()

            return jsonify({
                'jwt_present': True,
                'current_user': current_user,
                'jwt_data': jwt_data
            })
        except Exception as jwt_error:
            return jsonify({
                'jwt_present': False,
                'error': str(jwt_error),
                'cookies': dict(request.cookies)
            })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'cookies': dict(request.cookies)
        })


# Rest of your routes...
@ptcao_properties_bp.route('/api/properties', methods=['GET'])
@jwt_required()
def get_ptcao_properties_api():
    """Get all properties for PTCAO with optional filters"""
    try:
        municipality = request.args.get('municipality')
        accommodation_type = request.args.get('accommodation_type')
        status = request.args.get('status')

        query = Property.query

        if municipality:
            query = query.filter(Property.municipality == municipality)
        if accommodation_type:
            query = query.filter(Property.accommodation_type == accommodation_type)
        if status:
            query = query.filter(Property.status == PropertyStatus(status))

        properties = query.all()

        properties_data = []
        for prop in properties:
            # Get price range if rooms exist
            price_range = None
            if prop.rooms:
                prices = [float(room.overnight_price) for room in prop.rooms if room.overnight_price]
                if prices:
                    price_range = {
                        'min': min(prices),
                        'max': max(prices)
                    }

            # Get first 3 amenities
            amenities = [a.amenity for a in prop.amenities if not a.room_id][:3]
            has_more_amenities = len([a for a in prop.amenities if not a.room_id]) > 3

            properties_data.append({
                'property_id': prop.property_id,
                'property_name': prop.property_name,
                'barangay': prop.barangay,
                'municipality': prop.municipality,
                'accommodation_type': prop.accommodation_type,
                'status': prop.status.value,
                'description': prop.description,
                'amenities': amenities,
                'has_more_amenities': has_more_amenities,
                'price_range': price_range,
                'image_url': prop.images[0].image_path if prop.images else None
            })

        return jsonify({
            'status': 'success',
            'count': len(properties),
            'properties': properties_data
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@ptcao_properties_bp.route('/properties/<int:property_id>', methods=['GET'])
@jwt_required()
def get_ptcao_property(property_id):
    try:
        property = Property.query.options(
            db.joinedload(Property.images),
            db.joinedload(Property.amenities),
            db.joinedload(Property.rooms).joinedload(Room.amenities),
            db.joinedload(Property.coordinates),
            db.joinedload(Property.typical_locations),
            db.joinedload(Property.property_reports)
        ).get_or_404(property_id)

        # Get property report data if exists
        report_data = None
        if property.property_reports:
            report = property.property_reports[0]  # Assuming one report per property
            report_data = {
                'dot_accredited': report.dot_accredited,
                'dot_valid_until': report.dot_accreditation_valid.strftime(
                    '%Y-%m-%d') if report.dot_accreditation_valid else None,
                'ptcao_registered': report.ptcao_registered,
                'ptcao_valid_until': report.ptcao_valid_until.strftime(
                    '%Y-%m-%d') if report.ptcao_valid_until else None,
                'classification': report.classification,
                'male_employees': report.male_employees,
                'female_employees': report.female_employees,
                'total_rooms': report.total_rooms,
                'daytour_capacity': report.daytour_capacity,
                'overnight_capacity': report.overnight_capacity
            }

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
            'report_data': report_data,
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@ptcao_properties_bp.route('/municipalities', methods=['GET'])
@jwt_required()
def get_ptcao_municipalities():
    """Get all unique municipalities for PTCAO filter"""
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


@ptcao_properties_bp.route('/accommodation-types', methods=['GET'])
@jwt_required()
def get_ptcao_accommodation_types():
    """Get all unique accommodation types for PTCAO filter"""
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