import os

from flask import render_template, request, flash, redirect, url_for, send_from_directory
from Batangas_PTCAO.src.model import BusinessRegistration, Room, EventFacility


def init_main_routes(app):
    @app.route('/homepage', methods=['GET', 'POST'])
    def homepage():
        try:
            businesses = BusinessRegistration.query.join(Room).join(EventFacility).all()

            hotel_data = []
            for business in businesses:
                amenities = []
                for facility in business.event_facilities:
                    amenities.append(facility.facilities.split(','))

        except Exception as e:
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