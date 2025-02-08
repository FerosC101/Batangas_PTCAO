import os
from flask import render_template, request, flash, redirect, url_for, send_from_directory
from flask_jwt_extended import jwt_required

from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import BusinessRegistration, Room, EventFacility


def init_main_routes(app):
    @app.route('/homepage', methods=['GET', 'POST'])
    @jwt_required()
    def homepage():
        try:
            # Optimize query with eager loading
            businesses = BusinessRegistration.query \
                .join(Room) \
                .join(EventFacility) \
                .options(
                db.joinedload(BusinessRegistration.rooms),
                db.joinedload(BusinessRegistration.event_facilities)
            ) \
                .all()

            hotel_data = []
            for business in businesses:
                # Calculate room statistics
                rooms = business.rooms
                if rooms:
                    room_prices = [room.capacity * 1000 for room in rooms]
                    avg_room_price = sum(room_prices) / len(rooms)
                else:
                    avg_room_price = 5000

                # Process facilities and amenities
                amenities = set()
                has_image = False

                for facility in business.event_facilities:
                    if facility.facilities:
                        has_image = True
                        facility_amenities = [
                            amenity.strip()
                            for amenity in facility.facilities.split(',')
                            if amenity.strip()
                        ]
                        amenities.update(facility_amenities)

                # Format business data
                business_info = {
                    'name': business.business_name,
                    'location': business.business_address,
                    'image': "/api/placeholder/400/200" if has_image else "",
                    'rating': "★★★★☆",  # Placeholder rating
                    'price': f"₱{int(avg_room_price):,} / night",
                    'amenities': list(amenities)[:3]  # Take first 3 unique amenities
                }

                hotel_data.append(business_info)

            return render_template('homepage.html', hotels=hotel_data)

        except Exception as e:
            # Log the error for debugging
            app.logger.error(f"Homepage error: {str(e)}")
            flash('Unable to load hotels', 'error')
            return redirect(url_for('login'))

    @app.route('/static/<path:filename>')
    def serve_static_file(filename):
        if allowed_file(filename):
            return send_from_directory(os.path.join(app.root_path, 'static'), filename)
        return 'File type not allowed', 400

    def allowed_file(filename):
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Changed to set for faster lookup
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    return app