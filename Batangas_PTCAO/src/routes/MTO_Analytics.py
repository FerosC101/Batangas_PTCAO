from flask import Blueprint, jsonify, request, render_template, current_app, redirect, flash, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import (
    User,
    Property,
    PropertyReport,
    TouristReport,
    BarangayMonthlyStatistics,
    PropertyMonthlyStatistics, VisitorStatistics
)

analytics_bp = Blueprint('analytics', __name__, template_folder='templates')


def init_analytics_routes(app):
    app.register_blueprint(analytics_bp, url_prefix='/mto')


def get_time_period(period):
    today = datetime.now().date()
    if period == 'week':
        return today - timedelta(days=7)
    elif period == 'month':
        return today - timedelta(days=30)
    elif period == 'year':
        return today - timedelta(days=365)
    else:  # Default to month
        return today - timedelta(days=30)


@analytics_bp.route('/analytics')
@jwt_required()
def mto_analytics():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))

    municipality = user.municipality
    today = datetime.now().date()
    last_30_days = today - timedelta(days=30)

    # Initialize visitor stats without revenue
    visitor_stats = {
        'total_visitors': 0,
        'local_visitors': 0,
        'foreign_visitors': 0,
        'daytour_visitors': 0,
        'overnight_visitors': 0
    }

    try:
        # Get visitor statistics from TouristReport (without revenue)
        tourist_stats = db.session.query(
            db.func.sum(TouristReport.total_daytour_guests).label('daytour'),
            db.func.sum(TouristReport.total_overnight_guests).label('overnight')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(last_30_days, today)
        ).first()

        if tourist_stats:
            visitor_stats.update({
                'daytour_visitors': tourist_stats.daytour or 0,
                'overnight_visitors': tourist_stats.overnight or 0
            })

        # Get visitor counts from VisitorStatistics
        visitor_counts = db.session.query(
            db.func.sum(VisitorStatistics.count).label('total'),
            db.func.sum(db.case(
                [(VisitorStatistics.visitor_type == 'Local', VisitorStatistics.count)],
                else_=0
            )).label('local'),
            db.func.sum(db.case(
                [(VisitorStatistics.visitor_type == 'Foreign', VisitorStatistics.count)],
                else_=0
            )).label('foreign')
        ).join(
            Property,
            Property.property_id == VisitorStatistics.property_id
        ).filter(
            Property.municipality == municipality,
            VisitorStatistics.report_date.between(last_30_days, today)
        ).first()

        if visitor_counts:
            visitor_stats.update({
                'total_visitors': visitor_counts.total or 0,
                'local_visitors': visitor_counts.local or 0,
                'foreign_visitors': visitor_counts.foreign or 0
            })

    except Exception as e:
        current_app.logger.error(f"Error loading analytics data: {str(e)}")
        flash('Error loading analytics data', 'error')

    return render_template(
        'MTO_Analytics.html',
        visitor_stats=visitor_stats,
        municipality=municipality,
        current_year=today.year,
        current_month=today.month
    )

@analytics_bp.route('/api/analytics/property', methods=['GET'])
@jwt_required()
def get_property_analytics():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Get property reports summary
        reports = db.session.query(
            db.func.count(PropertyReport.property_id).label('total_reports'),
            db.func.avg(PropertyReport.male_employees).label('avg_male'),
            db.func.avg(PropertyReport.female_employees).label('avg_female'),
            db.func.sum(PropertyReport.total_rooms).label('total_rooms'),
            db.func.sum(PropertyReport.daytour_capacity).label('daytour_cap'),
            db.func.sum(PropertyReport.overnight_capacity).label('overnight_cap')
        ).join(
            Property,
            Property.property_id == PropertyReport.property_id
        ).filter(
            Property.municipality == municipality
        ).first()

        # Get accreditation stats
        accreditation = db.session.query(
            db.func.count(db.case(
                [(PropertyReport.dot_accredited == True, 1)],
                else_=None
            )).label('dot_accredited'),
            db.func.count(db.case(
                [(PropertyReport.ptcao_registered == True, 1)],
                else_=None
            )).label('ptcao_registered')
        ).join(
            Property,
            Property.property_id == PropertyReport.property_id
        ).filter(
            Property.municipality == municipality
        ).first()

        return jsonify({
            'success': True,
            'data': {
                'total_reports': reports.total_reports or 0,
                'avg_male_employees': round(reports.avg_male or 0, 1),
                'avg_female_employees': round(reports.avg_female or 0, 1),
                'total_rooms': reports.total_rooms or 0,
                'daytour_capacity': reports.daytour_cap or 0,
                'overnight_capacity': reports.overnight_cap or 0,
                'dot_accredited': accreditation.dot_accredited or 0,
                'ptcao_registered': accreditation.ptcao_registered or 0
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/tourist', methods=['GET'])
@jwt_required()
def get_tourist_analytics():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        period = request.args.get('period', 'month')
        start_date = get_time_period(period)
        end_date = datetime.now().date()

        # Get tourist reports summary
        reports = db.session.query(
            db.func.sum(TouristReport.total_daytour_guests).label('daytour'),
            db.func.sum(TouristReport.total_overnight_guests).label('overnight'),
            db.func.sum(TouristReport.foreign_daytour_visitors).label('foreign_day'),
            db.func.sum(TouristReport.foreign_overnight_visitors).label('foreign_night'),
            db.func.sum(TouristReport.male_tourists).label('male'),
            db.func.sum(TouristReport.female_tourists).label('female'),
            db.func.sum(TouristReport.total_revenue).label('revenue'),
            db.func.avg(TouristReport.rooms_occupied).label('avg_occupancy')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(start_date, end_date)
        ).first()

        return jsonify({
            'success': True,
            'data': {
                'daytour_visitors': reports.daytour or 0,
                'overnight_visitors': reports.overnight or 0,
                'foreign_daytour': reports.foreign_day or 0,
                'foreign_overnight': reports.foreign_night or 0,
                'male_tourists': reports.male or 0,
                'female_tourists': reports.female or 0,
                'total_revenue': float(reports.revenue) if reports.revenue else 0,
                'avg_occupancy': round(reports.avg_occupancy or 0, 1),
                'period': period
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/trends', methods=['GET'])
@jwt_required()
def get_visitor_trends():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Get monthly trends
        trends = db.session.query(
            db.func.extract('year', TouristReport.report_date).label('year'),
            db.func.extract('month', TouristReport.report_date).label('month'),
            db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            db.func.extract('year', TouristReport.report_date) >= datetime.now().year - 1
        ).group_by(
            'year', 'month'
        ).order_by(
            'year', 'month'
        ).all()

        # Format for chart
        labels = []
        data = []
        for trend in trends:
            month_name = datetime(2000, int(trend.month), 1).strftime('%b')
            labels.append(f"{month_name} {int(trend.year)}")
            data.append(int(trend.total or 0))

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'visitors': data
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500