import os
from flask import render_template, request, flash, redirect, url_for, send_from_directory
from sqlalchemy.orm import joinedload
from extension import db
from model import BusinessRegistration, Room, EventFacility

def init_main_routes(app):
    @app.route('/homepage', methods=['GET', 'POST'])
    def homepage():
        try:
            businesses = BusinessRegistration.query \
                .outerjoin(Room) \
                .outerjoin(EventFacility) \
                .options(
                    joinedload(BusinessRegistration.rooms),
                    joinedload(BusinessRegistration.event_facilities)
                ) \
                .all()

            hotel_data = []
            for business in businesses:
                rooms = getattr(business, "rooms", [])  # Ensure it's a list
                event_facilities = getattr(business, "event_facilities", [])  # Ensure it's a list

                # Calculate average room price safely
                room_prices = [room.capacity * 1000 for room in rooms if room.capacity is not None]
                avg_room_price = sum(room_prices) / len(room_prices) if room_prices else 5000

                # Process amenities
                amenities = set()
                has_image = False

                for facility in event_facilities:
                    if facility.facilities:
                        has_image = True
                        facility_amenities = [
                            amenity.strip() for amenity in facility.facilities.split(',') if amenity.strip()
                        ]
                        amenities.update(facility_amenities)

                # Store business data
                business_info = {
                    'name': business.business_name,
                    'location': business.business_address,
                    'image': "/api/placeholder/400/200" if has_image else "",
                    'rating': "★★★★",  # Placeholder rating (removed emoji)
                    'price': f"₱{int(avg_room_price):,} / night",
                    'amenities': list(amenities)[:3]
                }

                hotel_data.append(business_info)

            return render_template('User_Homepage.html', hotels=hotel_data)

        except Exception as e:
            app.logger.error(f"Homepage error: {str(e)}", exc_info=True)
            flash(f"Error loading hotels: {str(e)}", "error")
            return redirect(url_for('login'))

    @app.route('/static/<path:filename>')
    def serve_static_file(filename):
        if allowed_file(filename):
            return send_from_directory(os.path.join(app.root_path, 'static'), filename)
        return 'File type not allowed', 400

    def allowed_file(filename):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    return app
