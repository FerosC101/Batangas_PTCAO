import os

from flask import render_template, request, flash, redirect, url_for, send_from_directory
from flask_jwt_extended import jwt_required

from Batangas_PTCAO.src.model import BusinessRegistration, Room, EventFacility


def init_main_routes(app):
    @app.route('/homepage', methods=['GET', 'POST'])
    @jwt_required()
    def homepage():
        try:
            businesses = BusinessRegistration.query.join(Room).join(EventFacility).all()

            hotel_data = []
            for business in businesses:
                has_image = any(facility.facilities for facility in business.event_facilities)

                # If no facilities, use white placeholder
                first_facility_image = "/api/placeholder/400/200" if has_image else ""

                rooms = business.rooms
                avg_room_price = sum(room.capacity * 1000 for room in rooms) / len(rooms) if rooms else 5000

                amenities = []
                for facility in business.event_facilities:
                    if facility.facilities:
                        amenities.extend(facility.facilities.split(','))

                amenities = list(set(amenities))[:3]

                # Placeholder rating (future: implement actual rating system)
                rating = "★★★★☆"

                # Prepare business details
                business_info = {
                    'name': business.business_name,
                    'location': business.business_address,
                    'image': first_facility_image,
                    'rating': rating,
                    'price': f"₱{int(avg_room_price):,} / night",
                    'amenities': amenities
                }

                hotel_data.append(business_info)

            return render_template('homepage.html', hotels=hotel_data)

        except Exception as e:
            # Log the error for debugging
            print(f"Homepage error: {str(e)}")
            flash('Unable to load hotels', 'error')
            return redirect(url_for('login'))

    @app.route('/static/<path:filename>')
    def serve_static_file(filename):
        if allowed_file(filename):
            return send_from_directory(os.path.join(app.root_path, 'static'), filename)
        else:
            return 'File type not allowed', 400

    def allowed_file(filename):
        ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS