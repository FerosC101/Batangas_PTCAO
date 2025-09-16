import traceback

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from extension import db
from model import Property, User, PropertyReport, TouristReport
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
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 401

        # Get filters from request
        date_range = request.args.get('date_range', 'all')
        barangay = request.args.get('barangay', 'all')
        prop_type = request.args.get('type', 'all')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Build query
        query = db.session.query(Property, PropertyReport) \
            .outerjoin(PropertyReport, Property.property_id == PropertyReport.property_id) \
            .filter(Property.municipality == current_user.municipality)

        # Apply filters
        if barangay != 'all':
            query = query.filter(Property.barangay == barangay)
        if prop_type != 'all':
            query = query.filter(Property.accommodation_type == prop_type)

        # Date filtering
        if date_range != 'all':
            today = datetime.now().date()
            if date_range == 'last_week':
                start_date = today - timedelta(days=7)
            elif date_range == 'last_month':
                start_date = today - timedelta(days=30)
            query = query.filter(or_(
                PropertyReport.report_period_start >= start_date,
                PropertyReport.report_period_start == None
            ))

        # Pagination
        pagination = query.paginate(page=page, per_page=per_page)

        # Format response
        properties = [{
            'property_id': prop.property_id,
            'name': prop.property_name,
            'barangay': prop.barangay,
            'type': prop.accommodation_type,
            'dot_accredited': report.dot_accredited if report else False,
            'dot_valid': report.dot_accreditation_valid.strftime('%Y-%m-%d') if report and report.dot_accreditation_valid else '',
            'ptcao_registered': report.ptcao_registered if report else False,
            'ptcao_valid': report.ptcao_valid_until.strftime('%Y-%m-%d') if report and report.ptcao_valid_until else '',
            'classification': report.classification if report else '',
            'male_employees': report.male_employees if report else 0,
            'female_employees': report.female_employees if report else 0,
            'total_employees': (report.male_employees if report else 0) + (report.female_employees if report else 0),
            'daytour_capacity': report.daytour_capacity if report else 0,
            'overnight_capacity': report.overnight_capacity if report else 0,
            'total_rooms': report.total_rooms if report else 0
        } for prop, report in pagination.items]

        return jsonify({
            'success': True,
            'data': properties,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error loading property report: {str(e)}'
        }), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error loading property report: {str(e)}'
        }), 500


@reports_bp.route('/properties', methods=['GET'])
@jwt_required()
def get_properties():
    try:
        current_user = User.query.get(get_jwt_identity())
        properties = Property.query.filter_by(municipality=current_user.municipality).all()

        properties_data = []
        for prop in properties:
            properties_data.append({
                'id': prop.property_id,
                'name': prop.property_name,
                'barangay': prop.barangay,
                'type': prop.accommodation_type
            })

        return jsonify({
            'success': True,
            'data': properties_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@reports_bp.route('/api/reports/property-data', methods=['GET'])
@jwt_required()
def get_property_report_data():
    try:
        current_user = User.query.get(get_jwt_identity())
        if not current_user:
            return jsonify({'success': False, 'message': 'User not found'}), 401

        # Get filters
        date_range = request.args.get('date_range', 'all')
        prop_type = request.args.get('type', 'all')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        query = db.session.query(Property, TouristReport) \
            .join(TouristReport, Property.property_id == TouristReport.property_id) \
            .filter(Property.municipality == current_user.municipality)

        if prop_type != 'all':
            query = query.filter(Property.accommodation_type == prop_type)

        if date_range != 'all':
            today = datetime.now().date()
            if date_range == 'last_week':
                start_date = today - timedelta(days=7)
            elif date_range == 'last_month':
                start_date = today - timedelta(days=30)
            query = query.filter(TouristReport.report_date >= start_date)

        pagination = query.paginate(page=page, per_page=per_page)

        reports = [{
            'property_id': prop.property_id,
            'name': prop.property_name,
            'barangay': prop.barangay,
            'type': prop.accommodation_type,
            'day_tour_guests': report.total_daytour_guests,
            'overnight_guests': report.total_overnight_guests,
            'total_guests': report.total_daytour_guests + report.total_overnight_guests,
            'rooms_occupied': report.rooms_occupied,
            'foreign_daytour': report.foreign_daytour_visitors,
            'foreign_overnight': report.foreign_overnight_visitors,
            'male_tourists': report.male_tourists,
            'female_tourists': report.female_tourists
        } for prop, report in pagination.items]

        return jsonify({
            'success': True,
            'data': reports,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error loading tourist report: {str(e)}'
        }), 500

@reports_bp.route('/api/reports/update-property', methods=['POST'])
@jwt_required()
def update_property_report():
    data = request.get_json()
    property_id = data['property_id']

    # Find or create report
    report = PropertyReport.query.filter_by(property_id=property_id).first()
    if not report:
        report = PropertyReport(property_id=property_id)
        db.session.add(report)

    # Update fields
    report.dot_accredited = data.get('dot_accredited', report.dot_accredited)
    report.ptcao_registered = data.get('ptcao_registered', report.ptcao_registered)
    report.classification = data.get('classification', report.classification)
    report.male_employees = data.get('male_employees', report.male_employees)
    report.female_employees = data.get('female_employees', report.female_employees)
    report.total_rooms = data.get('total_rooms', report.total_rooms)
    report.daytour_capacity = data.get('daytour_capacity', report.daytour_capacity)
    report.overnight_capacity = data.get('overnight_capacity', report.overnight_capacity)

    # Handle dates
    if data.get('dot_valid'):
        report.dot_accreditation_valid = datetime.strptime(data['dot_valid'], '%Y-%m-%d').date()
    if data.get('ptcao_valid'):
        report.ptcao_valid_until = datetime.strptime(data['ptcao_valid'], '%Y-%m-%d').date()

    report.report_period_start = datetime.now().date() - timedelta(days=30)
    report.report_period_end = datetime.now().date()

    db.session.commit()
    return jsonify({'success': True})


@reports_bp.route('/api/reports/add-tourist', methods=['POST'])
@jwt_required()
def add_tourist_report():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['property_id', 'report_date', 'day_tour_guests', 'overnight_guests']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Create new report
        report = TouristReport(
            property_id=data['property_id'],
            report_date=datetime.strptime(data['report_date'], '%Y-%m-%d').date(),
            total_daytour_guests=data['day_tour_guests'],
            total_overnight_guests=data['overnight_guests'],
            rooms_occupied=data.get('rooms_occupied', 0),
            foreign_daytour_visitors=data.get('foreign_daytour', 0),
            foreign_overnight_visitors=data.get('foreign_overnight', 0),
            male_tourists=data.get('male_tourists', 0),
            female_tourists=data.get('female_tourists', 0)
        )

        db.session.add(report)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Tourist report added successfully',
            'report_id': report.report_id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error adding tourist report: {str(e)}'
        }), 500


@reports_bp.route('/api/reports/upload', methods=['POST'])
@jwt_required()
def upload_report():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    file = request.files['file']
    report_type = request.form.get('report_type')

    if not report_type:
        return jsonify({'success': False, 'message': 'Report type not specified'}), 400

    if file.filename.endswith(('.xlsx', '.xls', '.csv')):
        try:
            df = pd.read_excel(file) if file.filename.endswith(('.xlsx', '.xls')) else pd.read_csv(file)
            current_user = User.query.get(get_jwt_identity())

            if report_type == 'property':
                for _, row in df.iterrows():
                    report = PropertyReport(
                        property_id=row['property_id'],
                        dot_accredited=row.get('dot_accredited', False),
                        dot_accreditation_valid=pd.to_datetime(row['dot_valid_until']) if pd.notna(
                            row.get('dot_valid_until')) else None,
                        ptcao_registered=row.get('ptcao_registered', False),
                        ptcao_valid_until=pd.to_datetime(row['ptcao_valid_until']) if pd.notna(
                            row.get('ptcao_valid_until')) else None,
                        classification=row.get('classification', ''),
                        male_employees=row.get('male_employees', 0),
                        female_employees=row.get('female_employees', 0),
                        total_rooms=row.get('total_rooms', 0),
                        daytour_capacity=row.get('daytour_capacity', 0),
                        overnight_capacity=row.get('overnight_capacity', 0),
                        report_period_start=datetime.now().date() - timedelta(days=30),
                        report_period_end=datetime.now().date()
                    )
                    db.session.add(report)

            elif report_type == 'tourist':
                for _, row in df.iterrows():
                    report = TouristReport(
                        property_id=row['property_id'],
                        report_date=pd.to_datetime(row['report_date']).date(),
                        total_daytour_guests=row.get('day_tour_guests', 0),
                        total_overnight_guests=row.get('overnight_guests', 0),
                        rooms_occupied=row.get('rooms_occupied', 0),
                        foreign_daytour_visitors=row.get('foreign_daytour', 0),
                        foreign_overnight_visitors=row.get('foreign_overnight', 0),
                        male_tourists=row.get('male_tourists', 0),
                        female_tourists=row.get('female_tourists', 0)
                    )
                    db.session.add(report)

            db.session.commit()
            return jsonify({'success': True, 'message': f'{len(df)} records processed successfully'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    return jsonify({'success': False, 'message': 'Invalid file format'}), 400