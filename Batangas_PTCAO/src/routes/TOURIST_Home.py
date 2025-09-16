from flask import Blueprint, jsonify, render_template
from datetime import datetime, timedelta
from model import Property, TouristReport, PropertyImage, Event, Announcement
from sqlalchemy import func, desc, or_

tourist_home_bp = Blueprint('tourist_home', __name__, url_prefix='/tourist')


def init_tourist_home_routes(app):
    app.register_blueprint(tourist_home_bp)


@tourist_home_bp.route('/api/home/featured-destinations')
def get_featured_destinations():
    try:
        # Calculate date range for popular properties (last 30 days)
        date_threshold = datetime.now() - timedelta(days=30)

        # Get top properties based on tourist reports in last 30 days
        popular_properties = TouristReport.query.with_entities(
            TouristReport.property_id,
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors')
        ).filter(
            TouristReport.report_date >= date_threshold
        ).group_by(
            TouristReport.property_id
        ).order_by(
            desc('total_visitors')
        ).limit(6).all()

        # Get full property details for the popular properties
        properties_data = []
        for prop in popular_properties:
            property = Property.query.get(prop.property_id)
            if property:
                # Get first image if available from static/uploads/properties
                image_path = '/static/images/default-destination.jpg'
                if property.images:
                    # Use the image path from PropertyImage model, ensuring it points to uploads folder
                    stored_image_path = property.images[0].image_path
                    # Check if the path already includes /static/uploads/, if not prepend it
                    if not stored_image_path.startswith('/static/uploads/'):
                        if stored_image_path.startswith('static/uploads/'):
                            image_path = '/' + stored_image_path
                        elif stored_image_path.startswith('uploads/'):
                            image_path = '/static/' + stored_image_path
                        else:
                            # Assume it's just the filename and it's in properties folder
                            image_path = '/static/uploads/events/' + stored_image_path
                    else:
                        image_path = stored_image_path

                properties_data.append({
                    'id': property.property_id,
                    'name': property.property_name,
                    'description': property.description or f"Popular {property.accommodation_type or 'property'} in {property.municipality or 'Batangas'}",
                    'municipality': property.municipality or "Batangas",
                    'image_path': image_path,
                    'type': property.accommodation_type or "Resort",
                    'barangay': property.barangay or ""
                })

        # If no popular properties found, get some featured properties as fallback
        if not properties_data:
            fallback_properties = Property.query.filter(
                Property.status == 'ACTIVE'
            ).limit(6).all()

            for property in fallback_properties:
                image_path = '/static/images/default-destination.jpg'
                if property.images:
                    stored_image_path = property.images[0].image_path
                    if not stored_image_path.startswith('/static/uploads/'):
                        if stored_image_path.startswith('static/uploads/'):
                            image_path = '/' + stored_image_path
                        elif stored_image_path.startswith('uploads/'):
                            image_path = '/static/' + stored_image_path
                        else:
                            image_path = '/static/uploads/properties/' + stored_image_path
                    else:
                        image_path = stored_image_path

                properties_data.append({
                    'id': property.property_id,
                    'name': property.property_name,
                    'description': property.description or f"Beautiful {property.accommodation_type or 'property'} in {property.municipality or 'Batangas'}",
                    'municipality': property.municipality or "Batangas",
                    'image_path': image_path,
                    'type': property.accommodation_type or "Resort",
                    'barangay': property.barangay or ""
                })

        return jsonify(properties_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tourist_home_bp.route('/api/home/upcoming-events')
def get_upcoming_events():
    try:
        today = datetime.today().date()
        events = Event.query.filter(
            Event.end_date >= today
        ).order_by(
            Event.start_date
        ).limit(4).all()

        events_data = []
        for e in events:
            # Handle event image path similar to properties
            image_path = '/static/images/default-event.jpg'
            if e.event_image:
                stored_image_path = e.event_image
                if not stored_image_path.startswith('/static/uploads/'):
                    if stored_image_path.startswith('static/uploads/'):
                        image_path = '/' + stored_image_path
                    elif stored_image_path.startswith('uploads/'):
                        image_path = '/static/' + stored_image_path
                    else:
                        # Assume it's in events folder
                        image_path = '/static/uploads/events/' + stored_image_path
                else:
                    image_path = stored_image_path

            events_data.append({
                'id': e.event_id,
                'title': e.event_title,
                'description': e.description or "Join us for this exciting event!",
                'start_date': e.start_date.strftime('%Y-%m-%d'),
                'end_date': e.end_date.strftime('%Y-%m-%d'),
                'municipality': e.municipality or "Batangas",
                'location': e.location or "Various Locations",
                'image_path': image_path,
                'day': e.start_date.day,
                'month': e.start_date.strftime('%b')
            })

        return jsonify(events_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tourist_home_bp.route('/api/home/recent-announcements')
def get_recent_announcements():
    try:
        announcements = Announcement.query.filter(
            Announcement.is_active == True
        ).order_by(
            Announcement.created_at.desc()
        ).limit(5).all()

        return jsonify([{
            'id': a.id,
            'title': a.title,
            'content': a.content or "Important announcement for visitors",
            'date': a.created_at.strftime('%B %d, %Y'),
            'municipality': a.municipality or "Batangas"
        } for a in announcements])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tourist_home_bp.route('/home')
def tourist_home():
    return render_template('TOURIST_Home.html')


@tourist_home_bp.route('/destinations')
def tourist_destinations():
    return render_template('TOURIST_Destination.html')


@tourist_home_bp.route('/map')
def tourist_map():
    return render_template('TOURIST_Map.html')


@tourist_home_bp.route('/events')
def tourist_events():
    return render_template('TOURIST_Event.html')


@tourist_home_bp.route('/about')
def tourist_about():
    return render_template('TOURIST_About.html')