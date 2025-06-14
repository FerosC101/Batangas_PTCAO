from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from extension import db
from model import Property, User, VisitorStatistics
import pandas as pd
import os

reports_bp = Blueprint('reports', __name__, url_prefix='/mto')

def init_reports_routes(app):
    app.register_blueprint(reports_bp)

@reports_bp.route('/reports')
@jwt_required()
def mto_reports():
    current_user = User.query.get(get_jwt_identity())
    if not current_user:
        return redirect(url_for('auth.login'))
    return render_template('MTO_Reports.html')

@reports_bp.route('/api/reports/properties', methods=['GET'])
@jwt_required()
def get_property_report():
    current_user = User.query.get(get_jwt_identity())

    # Get filters
    date_range = request.args.get('date_range', 'all')
    barangay = request.args.get('barangay', 'all')
    prop_type = request.args.get('type', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    query = Property.query.filter_by(municipality=current_user.municipality)

    if barangay != 'all':
        query = query.filter_by(barangay=barangay)
    if prop_type != 'all':
        query = query.filter_by(accommodation_type=prop_type)

    # Date filtering
    if date_range != 'all':
        today = datetime.now().date()
        if date_range == 'last_week':
            start_date = today - timedelta(days=7)
        elif date_range == 'last_month':
            start_date = today - timedelta(days=30)
        query = query.filter(Property.created_at >= start_date)

    pagination = query.paginate(page=page, per_page=per_page)

    properties = [{
        'ae_id': prop.property_id,
        'name': prop.property_name,
        'barangay': prop.barangay,
        'type': prop.accommodation_type,
        'dot_accredited': prop.dot_accredited,
        'dot_valid': prop.dot_accreditation_valid.strftime('%Y-%m-%d') if prop.dot_accreditation_valid else '',
        'ptcao_registered': prop.ptcao_registered,
        'ptcao_valid': prop.ptcao_valid_until.strftime('%Y-%m-%d') if prop.ptcao_valid_until else '',
        'classification': prop.classification,
        'male_employees': prop.male_employees,
        'female_employees': prop.female_employees,
        'total_rooms': prop.total_rooms,
        'daytour_capacity': prop.daytour_capacity,
        'overnight_capacity': prop.overnight_capacity
    } for prop in pagination.items]

    return jsonify({
        'success': True,
        'data': properties,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@reports_bp.route('/api/reports/update-property', methods=['POST'])
@jwt_required()
def update_property():
    data = request.get_json()
    prop = Property.query.get(data['ae_id'])

    if not prop:
        return jsonify({'success': False, 'message': 'Property not found'}), 404

    # Update fields
    prop.dot_accredited = data.get('dot_accredited', prop.dot_accredited)
    prop.dot_accreditation_valid = datetime.strptime(data['dot_valid'], '%Y-%m-%d').date() if data[
        'dot_valid'] else None
    prop.ptcao_registered = data.get('ptcao_registered', prop.ptcao_registered)
    prop.ptcao_valid_until = datetime.strptime(data['ptcao_valid'], '%Y-%m-%d').date() if data['ptcao_valid'] else None
    prop.classification = data.get('classification', prop.classification)
    prop.male_employees = data.get('male_employees', prop.male_employees)
    prop.female_employees = data.get('female_employees', prop.female_employees)
    prop.total_rooms = data.get('total_rooms', prop.total_rooms)

    db.session.commit()
    return jsonify({'success': True})

@reports_bp.route('/api/reports/upload', methods=['POST'])
@jwt_required()
def upload_report():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename.endswith(('.xlsx', '.xls', '.csv')):
        try:
            df = pd.read_excel(file) if file.filename.endswith(('.xlsx', '.xls')) else pd.read_csv(file)

            for _, row in df.iterrows():
                prop = Property.query.get(row['AE-ID'])
                if prop:
                    # Update properties similar to update_property endpoint
                    pass  # Implement your update logic here

            return jsonify({'success': True, 'message': 'File processed successfully'})

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    return jsonify({'success': False, 'message': 'Invalid file format'}), 400