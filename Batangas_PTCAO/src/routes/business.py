from flask import render_template, request, redirect, url_for, session, flash
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import (
    RegistrationStep, Establishment, ContactDetails,
    ManagementDetails, EmployeeCount, DotAccreditation
)
from datetime import datetime


def init_establishment_routes(app):
    @app.route('/establishment_registration', methods=['GET', 'POST'])
    def establishment_registration():
        if request.method == 'POST':
            # Collect establishment data
            try:
                # Convert string date to Date object
                date_established = datetime.strptime(request.form.get('date_established'), '%Y-%m-%d').date()

                establishment_data = {
                    'name': request.form.get('name'),
                    'address': request.form.get('address'),
                    'establishment_type': request.form.get('establishment_type'),
                    'date_established': date_established,
                    'tin': request.form.get('tin'),
                    'male_count': int(request.form.get('male_count', 0)),
                    'female_count': int(request.form.get('female_count', 0)),
                }

                # Handle "Others" type
                if establishment_data['establishment_type'] == 'Others':
                    establishment_data['other_type_details'] = request.form.get('other_type_details')
                    if not establishment_data['other_type_details']:
                        flash('Please specify the establishment type', 'error')
                        return render_template('establishment_registration.html')

                # Management details
                has_managing_company = request.form.get('has_managing_company') == 'true'
                management_data = {
                    'has_managing_company': has_managing_company,
                    'owner_manager_name': request.form.get('owner_manager_name'),
                    'organization_type': request.form.get('organization_type')
                }

                if has_managing_company:
                    management_data['managing_company_name'] = request.form.get('managing_company_name')
                    management_data['managing_company_address'] = request.form.get('managing_company_address')

                    if not management_data['managing_company_name'] or not management_data['managing_company_address']:
                        flash('Managing company details are required', 'error')
                        return render_template('establishment_registration.html')

                # Validate required fields
                if not all([
                    establishment_data['name'],
                    establishment_data['address'],
                    establishment_data['establishment_type'],
                    establishment_data['date_established'],
                    establishment_data['tin'],
                    management_data['owner_manager_name'],
                    management_data['organization_type']
                ]):
                    flash('All required fields must be filled', 'error')
                    return render_template('establishment_registration.html')

                # Store data in session for next steps
                session['registration_data'] = session.get('registration_data', {})
                session['registration_data']['establishment'] = establishment_data
                session['registration_data']['management'] = management_data

                # Update registration step to move to contact info
                session['registration_step'] = RegistrationStep.CONTACT_INFO

                # Proceed to next step
                return redirect(url_for('contact_info_registration'))

            except ValueError as e:
                flash(f'Invalid input: {str(e)}', 'error')
                return render_template('establishment_registration.html')

        # GET request - display the form
        session['registration_step'] = RegistrationStep.BUSINESS_DETAILS  # Using the existing enum value
        session['registration_data'] = {}
        return render_template('establishment_registration.html')

    @app.route('/contact_info_registration', methods=['GET', 'POST'])
    def contact_info_registration():
        # Check if establishment data exists in session
        if 'registration_data' not in session or 'establishment' not in session['registration_data']:
            flash('Please complete establishment information first', 'error')
            return redirect(url_for('establishment_registration'))

        if request.method == 'POST':
            # Collect contact information
            contact_data = {
                'landline': request.form.get('landline'),
                'mobile_number': request.form.get('mobile_number'),
                'email_address': request.form.get('email_address'),
                'website': request.form.get('website'),
                'social_media_accounts': request.form.get('social_media_accounts')
            }

            # Validate that at least one contact method is provided
            if not any([contact_data['landline'], contact_data['mobile_number'], contact_data['email_address']]):
                flash('At least one contact method (landline, mobile, or email) is required', 'error')
                return render_template('contact_info_registration.html')

            # Store contact data in session
            session['registration_data']['contact'] = contact_data

            # Move to next step (DOT Accreditation)
            session['registration_step'] = RegistrationStep.SPECIAL_SERVICES  # Using the existing enum

            return redirect(url_for('accreditation_registration'))

        return render_template('contact_info_registration.html')

    @app.route('/save_establishment_data', methods=['POST'])
    def save_establishment_data():
        """
        Save all establishment data to the database after completing all registration steps
        """
        if 'registration_data' not in session:
            flash('Registration data is missing', 'error')
            return redirect(url_for('establishment_registration'))

        try:
            # Begin database transaction
            db.session.begin_nested()

            # Extract data from session
            establishment_data = session['registration_data']['establishment']
            management_data = session['registration_data']['management']
            contact_data = session['registration_data'].get('contact', {})
            accreditation_data = session['registration_data'].get('accreditation', {})

            # Create new establishment
            new_establishment = Establishment(
                name=establishment_data['name'],
                address=establishment_data['address'],
                establishment_type=establishment_data['establishment_type'],
                date_established=establishment_data['date_established'],
                tin=establishment_data['tin']
            )

            # Handle "Other" establishment type
            if establishment_data['establishment_type'] == 'Others' and 'other_type_details' in establishment_data:
                new_establishment.other_type_details = establishment_data['other_type_details']

            db.session.add(new_establishment)
            db.session.flush()  # Get the establishment_id without committing

            # Create employee count record
            employee_count = EmployeeCount(
                establishment_id=new_establishment.establishment_id,
                male_count=establishment_data['male_count'],
                female_count=establishment_data['female_count']
            )
            db.session.add(employee_count)

            # Create management details
            management_details = ManagementDetails(
                establishment_id=new_establishment.establishment_id,
                has_managing_company=management_data['has_managing_company'],
                owner_manager_name=management_data['owner_manager_name'],
                organization_type=management_data['organization_type']
            )

            if management_data['has_managing_company']:
                management_details.managing_company_name = management_data['managing_company_name']
                management_details.managing_company_address = management_data['managing_company_address']

            db.session.add(management_details)

            # Create contact details if provided
            if contact_data:
                contact = ContactDetails(
                    establishment_id=new_establishment.establishment_id,
                    landline=contact_data.get('landline'),
                    mobile_number=contact_data.get('mobile_number'),
                    email_address=contact_data.get('email_address'),
                    website=contact_data.get('website'),
                    social_media_accounts=contact_data.get('social_media_accounts')
                )
                db.session.add(contact)

            # Create DOT accreditation details if provided
            if accreditation_data:
                accreditation = DotAccreditation(
                    establishment_id=new_establishment.establishment_id,
                    is_accredited=accreditation_data.get('is_accredited', False),
                    category=accreditation_data.get('category'),
                    star_rating=accreditation_data.get('star_rating'),
                    accreditation_type=accreditation_data.get('accreditation_type')
                )
                db.session.add(accreditation)

            # Commit all changes
            db.session.commit()

            # Clear registration data from session
            session.pop('registration_data', None)
            session.pop('registration_step', None)

            flash('Registration completed successfully!', 'success')
            return redirect(url_for('registration_success'))

        except Exception as e:
            db.session.rollback()
            print(f"Error saving establishment data: {str(e)}")
            flash(f"Registration failed: {str(e)}", 'error')
            return redirect(url_for('establishment_registration'))