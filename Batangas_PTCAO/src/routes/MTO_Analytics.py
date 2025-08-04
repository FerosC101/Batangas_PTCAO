from flask import Blueprint, jsonify, request, render_template, current_app, redirect, flash, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from extension import db
from model import (
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

    # Initialize default values
    summary_data = {
        'total_visitors': 0,
        'local_visitors': 0,
        'foreign_visitors': 0,
        'overnight_stays': 0
    }

    try:
        # Get visitor statistics from TouristReport
        tourist_stats = db.session.query(
            db.func.coalesce(db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests), 0).label('total'),
            db.func.coalesce(db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests -
                                       (TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors)), 0).label('local'),
            db.func.coalesce(db.func.sum(TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors), 0).label('foreign'),
            db.func.coalesce(db.func.sum(TouristReport.total_overnight_guests), 0).label('overnight')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(last_30_days, today)
        ).first()

        if tourist_stats:
            summary_data = {
                'total_visitors': tourist_stats.total,
                'local_visitors': tourist_stats.local,
                'foreign_visitors': tourist_stats.foreign,
                'overnight_stays': tourist_stats.overnight
            }

        # Get top destinations (barangays with most visitors)
        top_destinations = db.session.query(
            Property.barangay,
            db.func.coalesce(db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests), 0).label('total_visitors')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            Property.barangay.isnot(None),
            TouristReport.report_date.between(last_30_days, today)
        ).group_by(
            Property.barangay
        ).order_by(
            db.desc('total_visitors')
        ).limit(5).all()

        # Get all barangays in municipality
        barangays = db.session.query(
            Property.barangay
        ).filter(
            Property.municipality == municipality,
            Property.barangay.isnot(None)
        ).distinct().order_by(
            Property.barangay
        ).all()

    except Exception as e:
        current_app.logger.error(f"Error loading analytics data: {str(e)}")
        flash('Error loading analytics data', 'error')
        top_destinations = []
        barangays = []

    return render_template(
        'MTO_Analytics.html',
        summary_stats=summary_data,
        top_destinations=[{'barangay': d[0], 'total_visitors': d[1]} for d in top_destinations],
        barangays=[b[0] for b in barangays],
        municipality=municipality,
        current_year=today.year,
        current_month=today.month
    )


# Key Issues Found and Fixed:

# 1. VISITOR TRENDS ENDPOINT ISSUES:
@analytics_bp.route('/api/analytics/visitor-trends', methods=['GET'])
@jwt_required()
def get_visitor_trends():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        period = request.args.get('period', '6months')
        today = datetime.now().date()

        # Fix date range calculation
        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'month':
            start_date = today - timedelta(days=30)
        elif period == '3months':
            start_date = today - timedelta(days=90)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:  # default to 6 months
            start_date = today - timedelta(days=180)

        print(f"Fetching trends for municipality: {municipality}")
        print(f"Date range: {start_date} to {today}")

        # FIXED: Remove the problematic debug lines and use consistent TouristReport query
        trends = db.session.query(
            db.func.extract('year', TouristReport.report_date).label('year'),
            db.func.extract('month', TouristReport.report_date).label('month'),
            db.func.coalesce(db.func.sum(
                TouristReport.total_daytour_guests +
                TouristReport.total_overnight_guests -
                (TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors)
            ), 0).label('local'),
            db.func.coalesce(db.func.sum(
                TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors
            ), 0).label('foreign'),
            db.func.coalesce(db.func.sum(
                TouristReport.total_daytour_guests
            ), 0).label('daytour'),
            db.func.coalesce(db.func.sum(
                TouristReport.total_overnight_guests
            ), 0).label('overnight')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(start_date, today)
        ).group_by(
            'year', 'month'
        ).order_by(
            'year', 'month'
        ).all()

        print(f"Query results: {len(trends)} records found")

        # Format for chart
        labels = []
        local_data = []
        foreign_data = []
        daytour_data = []
        overnight_data = []

        if trends:
            for trend in trends:
                month_name = datetime(2000, int(trend.month), 1).strftime('%b')
                labels.append(f"{month_name} {int(trend.year)}")
                local_data.append(int(trend.local))
                foreign_data.append(int(trend.foreign))
                daytour_data.append(int(trend.daytour))
                overnight_data.append(int(trend.overnight))
        else:
            # Return current month with zeros instead of empty
            current_month = today.strftime('%b %Y')
            labels = [current_month]
            local_data = [0]
            foreign_data = [0]
            daytour_data = [0]
            overnight_data = [0]

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'local_visitors': local_data,
                'foreign_visitors': foreign_data,
                'daytour_visitors': daytour_data,
                'overnight_visitors': overnight_data
            }
        }), 200

    except Exception as e:
        print(f"Error in visitor trends: {str(e)}")
        current_app.logger.error(f"Error fetching visitor trends: {str(e)}")

        # Return proper error response with empty data structure
        return jsonify({
            'success': False,
            'message': str(e),
            'data': {
                'labels': [],
                'local_visitors': [],
                'foreign_visitors': [],
                'daytour_visitors': [],
                'overnight_visitors': []
            }
        }), 500


# 2. TOP DESTINATIONS ENDPOINT - Add debugging and fix query
@analytics_bp.route('/api/analytics/top-destinations', methods=['GET'])
@jwt_required()
def get_top_destinations():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Get parameters
        period = request.args.get('period', 'month')
        barangay = request.args.get('barangay', 'all')

        print(f"Top destinations - Municipality: {municipality}, Period: {period}, Barangay: {barangay}")

        # Calculate date range
        today = datetime.now().date()
        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'month':
            start_date = today - timedelta(days=30)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:  # default to month
            start_date = today - timedelta(days=30)

        print(f"Date range: {start_date} to {today}")

        # Base query - Check if TouristReport has data first
        total_reports = db.session.query(db.func.count(TouristReport.report_id)).join(
            Property, Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(start_date, today)
        ).scalar()

        print(f"Total tourist reports found: {total_reports}")

        query = db.session.query(
            Property.barangay,
            db.func.coalesce(db.func.sum(
                TouristReport.total_daytour_guests + TouristReport.total_overnight_guests
            ), 0).label('total_visitors'),
            db.func.coalesce(db.func.sum(
                TouristReport.total_daytour_guests + TouristReport.total_overnight_guests -
                (TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors)
            ), 0).label('local_visitors'),
            db.func.coalesce(db.func.sum(
                TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors
            ), 0).label('foreign_visitors')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            Property.barangay.isnot(None),
            TouristReport.report_date.between(start_date, today)
        ).group_by(
            Property.barangay
        )

        # Apply barangay filter if needed
        if barangay != 'all':
            query = query.filter(Property.barangay == barangay)

        # Execute query and get results
        results = query.order_by(
            db.desc('total_visitors')
        ).limit(10).all()

        print(f"Query results: {len(results)} destinations found")

        # Calculate percentages
        destinations = []
        for result in results:
            total = result.total_visitors or 1  # Avoid division by zero
            local_percent = round((result.local_visitors / total) * 100) if total else 0
            foreign_percent = round((result.foreign_visitors / total) * 100) if total else 0

            destinations.append({
                'barangay': result.barangay,
                'total_visitors': result.total_visitors,
                'local_visitors': result.local_visitors,
                'foreign_visitors': result.foreign_visitors,
                'local_percent': local_percent,
                'foreign_percent': foreign_percent,
                'change_percent': 0  # You can implement trend calculation if needed
            })

        print(f"Processed destinations: {destinations}")

        return jsonify({
            'success': True,
            'data': destinations
        }), 200

    except Exception as e:
        print(f"Error in top destinations: {str(e)}")
        current_app.logger.error(f"Error fetching top destinations: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        }), 500


# 3. SUMMARY STATS ENDPOINT - Fix VisitorStatistics usage
@analytics_bp.route('/api/analytics/summary', methods=['GET'])
@jwt_required()
def get_summary_stats():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Get date range from query params
        date_range = request.args.get('date_range', '6months')
        barangay = request.args.get('barangay', 'all')
        property_type = request.args.get('property_type', 'all')
        visitor_type = request.args.get('visitor_type', 'all')

        # Calculate date range
        today = datetime.now().date()
        if date_range == 'week':
            start_date = today - timedelta(days=7)
        elif date_range == 'month':
            start_date = today - timedelta(days=30)
        elif date_range == '3months':
            start_date = today - timedelta(days=90)
        elif date_range == 'year':
            start_date = today - timedelta(days=365)
        else:  # default to 6 months
            start_date = today - timedelta(days=180)

        print(f"Summary stats - Municipality: {municipality}, Date range: {start_date} to {today}")

        # FIXED: Use TouristReport instead of VisitorStatistics for consistency
        stats = db.session.query(
            db.func.coalesce(db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests),
                             0).label('total_visitors'),
            db.func.coalesce(db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests -
                                         (
                                                     TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors)),
                             0).label('local_visitors'),
            db.func.coalesce(
                db.func.sum(TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors),
                0).label('foreign_visitors'),
            db.func.coalesce(db.func.sum(TouristReport.total_overnight_guests), 0).label('overnight_stays')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(start_date, today)
        )

        # Apply filters
        if barangay != 'all':
            stats = stats.filter(Property.barangay == barangay)
        if property_type != 'all':
            stats = stats.filter(Property.accommodation_type == property_type)

        result = stats.first()

        print(f"Summary stats result: {result}")

        return jsonify({
            'success': True,
            'data': {
                'total_visitors': result.total_visitors or 0,
                'local_visitors': result.local_visitors or 0,
                'foreign_visitors': result.foreign_visitors or 0,
                'overnight_stays': result.overnight_stays or 0
            }
        }), 200

    except Exception as e:
        print(f"Error in summary stats: {str(e)}")
        current_app.logger.error(f"Error fetching summary stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/barangays', methods=['GET'])
@jwt_required()
def get_barangays():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        barangays = db.session.query(
            Property.barangay
        ).filter(
            Property.municipality == municipality,
            Property.barangay.isnot(None)
        ).distinct().order_by(
            Property.barangay
        ).all()

        return jsonify({
            'success': True,
            'barangays': [b[0] for b in barangays]
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500







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


@analytics_bp.route('/api/analytics/debug', methods=['GET'])
@jwt_required()
def debug_analytics_data():
    """Debug endpoint to check data availability"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Check if we have properties
        property_count = db.session.query(db.func.count(Property.property_id)).filter(
            Property.municipality == municipality
        ).scalar()

        # Check if we have tourist reports
        report_count = db.session.query(db.func.count(TouristReport.report_id)).join(
            Property, Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality
        ).scalar()

        # Check recent reports (last 30 days)
        today = datetime.now().date()
        recent_reports = db.session.query(db.func.count(TouristReport.report_id)).join(
            Property, Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date >= today - timedelta(days=30)
        ).scalar()

        # Get sample data
        sample_reports = db.session.query(
            Property.barangay,
            TouristReport.report_date,
            TouristReport.total_daytour_guests,
            TouristReport.total_overnight_guests
        ).join(
            Property, Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality
        ).limit(5).all()

        return jsonify({
            'success': True,
            'debug_info': {
                'municipality': municipality,
                'property_count': property_count,
                'total_report_count': report_count,
                'recent_reports_count': recent_reports,
                'sample_reports': [
                    {
                        'barangay': r.barangay,
                        'date': str(r.report_date),
                        'daytour': r.total_daytour_guests,
                        'overnight': r.total_overnight_guests
                    } for r in sample_reports
                ]
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

