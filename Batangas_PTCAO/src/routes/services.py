from flask import render_template, request, redirect, url_for, session, flash
from Batangas_PTCAO.src.model import RegistrationStep

def init_services_routes(app):
    @app.route('/special_services', methods=['GET', 'POST'])
    def special_services():
        if 'registration_data' not in session or 'business' not in session['registration_data']:
            flash('Please complete business registration first', 'error')
            return redirect(url_for('business_registration'))

        if request.method == 'POST':
            rooms_data = []
            room_types = request.form.getlist('room_type[]')
            room_numbers = request.form.getlist('room_number[]')
            room_capacities = request.form.getlist('room_capacity[]')
            room_prices = request.form.getlist('room_price[]')

            for i in range(len(room_types)):
                if room_types[i] and room_numbers[i] and room_capacities[i] and room_prices[i]:
                    rooms_data.append({
                        'type': room_types[i],
                        'number': int(room_numbers[i]),
                        'capacity': int(room_capacities[i]),
                        'price': float(room_prices[i])
                    })

            facilities_data = []
            facility_names = request.form.getlist('facility_name[]')
            facility_capacities = request.form.getlist('facility_capacity[]')
            facility_amenities = request.form.getlist('facility_amenities[]')

            for i in range(len(facility_names)):
                if facility_names[i] and facility_capacities[i] and facility_amenities[i]:
                    facilities_data.append({
                        'name': facility_names[i],
                        'capacity': int(facility_capacities[i]),
                        'amenities': facility_amenities[i]
                    })

            services_data = {
                'accreditation': request.form.get('accreditation'),
                'classification': request.form.get('classification'),
                'rooms': rooms_data,
                'facilities': facilities_data,
                'other_services': request.form.get('services')
            }

            if not services_data['accreditation'] or not services_data['classification']:
                flash('Accreditation and classification are required', 'error')
                return render_template('Special_Service.html')

            session['registration_data']['services'] = services_data
            session['registration_step'] = RegistrationStep.LOGIN_CREDENTIALS

            return redirect(url_for('login_credentials'))

        return render_template('Special_Service.html')