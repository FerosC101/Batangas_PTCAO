from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
from model import User, Property, TouristReport
from extension import db
from sqlalchemy import func

def init_admin_reports_routes(app):
    admin_reports_bp = Blueprint('admin_reports', __name__)

    def generate_visitor_report_data():
        results = db.session.query(
            TouristReport.report_date,
            Property.municipality,
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors'),
            func.sum(TouristReport.total_daytour_guests - TouristReport.foreign_daytour_visitors +
                    TouristReport.total_overnight_guests - TouristReport.foreign_overnight_visitors).label('local_visitors'),
            func.sum(TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors).label('foreign_visitors')
        ).join(Property).group_by(
            TouristReport.report_date,
            Property.municipality
        ).order_by(
            TouristReport.report_date.desc()
        ).all()

        return [{
            'date': r.report_date.strftime('%Y-%m-%d'),
            'municipality': r.municipality,
            'local_visitors': r.local_visitors or 0,
            'foreign_visitors': r.foreign_visitors or 0,
            'total_visitors': r.total_visitors or 0
        } for r in results]

    def generate_property_report_data():
        properties = Property.query.all()
        return [{
            'property_id': p.property_id,
            'property_name': p.property_name,
            'municipality': p.municipality,
            'barangay': p.barangay,
            'type': p.accommodation_type,
            'status': p.status.value
        } for p in properties]

    def generate_user_report_data():
        users = User.query.filter_by(is_archived=False).all()
        return [{
            'user_id': u.user_id,
            'name': u.full_name,
            'municipality': u.municipality,
            'designation': u.designation,
            'join_date': u.created_at.strftime('%Y-%m-%d'),
            'status': 'Active' if u.is_active else 'Suspended'
        } for u in users]

    @admin_reports_bp.route('/admin/reports')
    @jwt_required()
    def admin_reports():
        return render_template('ADMIN_reports.html')

    @admin_reports_bp.route('/admin/reports/visitors')
    @jwt_required()
    def visitor_reports():
        data = generate_visitor_report_data()
        return jsonify(data)

    @admin_reports_bp.route('/admin/reports/properties')
    @jwt_required()
    def property_reports():
        data = generate_property_report_data()
        return jsonify(data)

    @admin_reports_bp.route('/admin/reports/users')
    @jwt_required()
    def user_reports():
        data = generate_user_report_data()
        return jsonify(data)

    @admin_reports_bp.route('/admin/reports/export/<report_type>')
    @jwt_required()
    def export_report(report_type):
        if report_type == 'visitors':
            data = generate_visitor_report_data()
            filename = f"visitors_report_{datetime.now().strftime('%Y%m%d')}.csv"
            headers = ['Date', 'Municipality', 'Local Visitors', 'Foreign Visitors', 'Total Visitors']
        elif report_type == 'properties':
            data = generate_property_report_data()
            filename = f"properties_report_{datetime.now().strftime('%Y%m%d')}.csv"
            headers = ['Property ID', 'Property Name', 'Municipality', 'Barangay', 'Type', 'Status']
        elif report_type == 'users':
            data = generate_user_report_data()
            filename = f"users_report_{datetime.now().strftime('%Y%m%d')}.csv"
            headers = ['User ID', 'Name', 'Municipality', 'Designation', 'Join Date', 'Status']
        else:
            return jsonify({'error': 'Invalid report type'}), 400

        csv = ','.join(headers) + '\n'
        for item in data:
            row = []
            for header in headers:
                key = header.lower().replace(' ', '_')
                if key in item:
                    row.append(str(item[key]))
                elif key == 'status' and report_type == 'properties':
                    row.append(item['status'])
                else:
                    row.append('')
            csv += ','.join(row) + '\n'

        return jsonify({
            'filename': filename,
            'content': csv
        })

    app.register_blueprint(admin_reports_bp)