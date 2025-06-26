from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
import random

admin_reports_bp = Blueprint('admin_reports', __name__)


# Mock data generators
def generate_municipalities():
    return [
        "Batangas City", "Lipa City", "Tanauan City", "Sto. Tomas",
        "Bauan", "San Juan", "Nasugbu", "Taal", "Lemery", "Calatagan"
    ]


def generate_property_types():
    return ["Hotel", "Resort", "Homestay", "Inn", "Bed & Breakfast"]


def generate_visitor_report_data():
    municipalities = generate_municipalities()
    data = []
    for i in range(30):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        for municipality in random.sample(municipalities, 5):
            data.append({
                'date': date,
                'municipality': municipality,
                'local_visitors': random.randint(5, 50),
                'foreign_visitors': random.randint(0, 20),
                'total_visitors': random.randint(10, 70),
                'revenue': random.randint(5000, 50000)
            })
    return data


def generate_property_report_data():
    property_types = generate_property_types()
    municipalities = generate_municipalities()
    data = []
    for i in range(50):
        data.append({
            'property_id': f"PROP-{1000 + i}",
            'property_name': f"{random.choice(property_types)} {random.choice(['Sunrise', 'Ocean', 'Mountain', 'Paradise', 'Haven'])}",
            'municipality': random.choice(municipalities),
            'type': random.choice(property_types),
            'visitors': random.randint(50, 500),
            'revenue': random.randint(20000, 200000),
            'rating': round(random.uniform(3.0, 5.0), 1)
        })
    return data


def generate_user_report_data():
    designations = ["MTO Officer", "Admin", "Manager", "Staff", "Supervisor"]
    municipalities = generate_municipalities()
    data = []
    for i in range(30):
        join_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
        data.append({
            'user_id': f"USER-{100 + i}",
            'name': f"{random.choice(['Juan', 'Maria', 'Pedro', 'Ana', 'Roberto'])} {random.choice(['Dela Cruz', 'Santos', 'Reyes', 'Gonzales', 'Lim'])}",
            'municipality': random.choice(municipalities),
            'designation': random.choice(designations),
            'join_date': join_date,
            'last_login': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
            'status': random.choice(['Active', 'Suspended', 'Inactive'])
        })
    return data


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
        headers = ['Date', 'Municipality', 'Local Visitors', 'Foreign Visitors', 'Total Visitors', 'Revenue']
    elif report_type == 'properties':
        data = generate_property_report_data()
        filename = f"properties_report_{datetime.now().strftime('%Y%m%d')}.csv"
        headers = ['Property ID', 'Property Name', 'Municipality', 'Type', 'Visitors', 'Revenue', 'Rating']
    elif report_type == 'users':
        data = generate_user_report_data()
        filename = f"users_report_{datetime.now().strftime('%Y%m%d')}.csv"
        headers = ['User ID', 'Name', 'Municipality', 'Designation', 'Join Date', 'Last Login', 'Status']
    else:
        return jsonify({'error': 'Invalid report type'}), 400

    # Generate CSV
    csv = ','.join(headers) + '\n'
    for item in data:
        csv += ','.join([str(item[h.lower().replace(' ', '_')]) for h in headers]) + '\n'

    return jsonify({
        'filename': filename,
        'content': csv
    })