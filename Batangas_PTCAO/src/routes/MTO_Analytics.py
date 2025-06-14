from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from extension import db
from model import (
    User,
    Property,
    VisitorStatistics,
    BarangayMonthlyStatistics,
    PropertyMonthlyStatistics
)

analytics_bp = Blueprint('analytics', __name__, template_folder='templates')

def init_analytics_routes(app):
    app.register_blueprint(analytics_bp, url_prefix='/mto')


@analytics_bp.route('/analytics')
@jwt_required()
def mto_analytics():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    municipality = user.municipality

    # Get initial data to render the template
    today = datetime.now().date()
    last_30_days = today - timedelta(days=30)

    summary_stats = {
        'total_visitors': get_visitor_count(last_30_days, today, municipality=municipality),
        'local_visitors': get_visitor_count(last_30_days, today, 'Local', municipality),
        'foreign_visitors': get_visitor_count(last_30_days, today, 'Foreign', municipality),
        'overnight_stays': get_stay_count(last_30_days, today, 'Overnight', municipality)
    }

    return render_template(
        'MTO_Analytics.html',
        summary_stats=summary_stats,
        municipality=municipality,
        user_id=current_user_id
    )


@analytics_bp.route('/api/analytics/summary', methods=['GET'])
@jwt_required()
def get_analytics_summary():
    try:
        # Get current user's municipality
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Calculate date ranges
        today = datetime.now().date()
        last_30_days = today - timedelta(days=30)
        last_6_months = today - timedelta(days=180)

        # Get summary statistics for the user's municipality
        summary_stats = {
            'total_visitors': get_visitor_count(last_30_days, today, municipality=municipality),
            'local_visitors': get_visitor_count(last_30_days, today, 'Local', municipality),
            'foreign_visitors': get_visitor_count(last_30_days, today, 'Foreign', municipality),
            'overnight_stays': get_stay_count(last_30_days, today, 'Overnight', municipality)
        }

        return jsonify({
            'success': True,
            'data': summary_stats
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/visitor-trends', methods=['GET'])
@jwt_required()
def get_analytics_visitor_trends():
    try:
        # Get current user's municipality
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Get period parameter (default: 6months)
        period = request.args.get('period', '6months')

        # Calculate date range
        today = datetime.now().date()

        if period == '3months':
            start_date = today - timedelta(days=90)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:  # 6months
            start_date = today - timedelta(days=180)

        # Get monthly visitor trends for the municipality
        trends = db.session.query(
            BarangayMonthlyStatistics.year,
            BarangayMonthlyStatistics.month,
            db.func.sum(BarangayMonthlyStatistics.local_visitors).label('local_visitors'),
            db.func.sum(BarangayMonthlyStatistics.foreign_visitors).label('foreign_visitors')
        ).join(
            Property,
            Property.barangay == BarangayMonthlyStatistics.barangay
        ).filter(
            Property.municipality == municipality,
            (
                    (BarangayMonthlyStatistics.year > start_date.year) |
                    (
                            (BarangayMonthlyStatistics.year == start_date.year) &
                            (BarangayMonthlyStatistics.month >= start_date.month)
                    )
            )
        ).group_by(
            BarangayMonthlyStatistics.year,
            BarangayMonthlyStatistics.month
        ).order_by(
            BarangayMonthlyStatistics.year,
            BarangayMonthlyStatistics.month
        ).all()

        # Format the data for the chart
        labels = []
        local_data = []
        foreign_data = []

        for trend in trends:
            month_name = datetime(2000, trend.month, 1).strftime('%b')
            labels.append(f"{month_name} {trend.year}")
            local_data.append(trend.local_visitors)
            foreign_data.append(trend.foreign_visitors)

        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'local_visitors': local_data,
                'foreign_visitors': foreign_data
            },
            'period': period
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/top-destinations', methods=['GET'])
@jwt_required()
def get_analytics_top_destinations():
    try:
        # Get current user's municipality
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Get period parameter (default: month)
        period = request.args.get('period', 'month')

        # Calculate date range
        today = datetime.now().date()

        if period == 'week':
            start_date = today - timedelta(days=7)
            month = today.month
            year = today.year
        elif period == 'year':
            start_date = today - timedelta(days=365)
            month = None
            year = today.year
        else:  # month
            start_date = today - timedelta(days=30)
            month = today.month
            year = today.year

        # Get top destinations by barangay for the municipality
        query = db.session.query(
            Property.barangay,
            db.func.sum(PropertyMonthlyStatistics.total_visitors).label('total_visitors'),
            db.func.sum(PropertyMonthlyStatistics.local_visitors).label('local_visitors'),
            db.func.sum(PropertyMonthlyStatistics.foreign_visitors).label('foreign_visitors')
        ).join(
            PropertyMonthlyStatistics,
            PropertyMonthlyStatistics.property_id == Property.property_id
        ).filter(
            Property.municipality == municipality
        )

        if month:
            query = query.filter(
                PropertyMonthlyStatistics.month == month
            )

        query = query.filter(
            PropertyMonthlyStatistics.year == year
        ).group_by(
            Property.barangay
        ).order_by(
            db.desc('total_visitors')
        ).limit(5)

        top_destinations = query.all()

        result = []
        for dest in top_destinations:
            total = dest.total_visitors or 0
            local = dest.local_visitors or 0
            foreign = dest.foreign_visitors or 0

            if total > 0:
                local_percent = round((local / total) * 100)
                foreign_percent = 100 - local_percent
            else:
                local_percent = 0
                foreign_percent = 0

            # Calculate change percentage (simplified - in real app compare with previous period)
            change_percent = 8  # Example value - would be calculated in real app

            result.append({
                'barangay': dest.barangay,
                'total_visitors': total,
                'local_visitors': local,
                'foreign_visitors': foreign,
                'local_percent': local_percent,
                'foreign_percent': foreign_percent,
                'change_percent': change_percent,
                'change_direction': 'up' if change_percent >= 0 else 'down'
            })

        return jsonify({
            'success': True,
            'data': result,
            'period': period
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def get_visitor_count(start_date, end_date, visitor_type=None, municipality=None):
    query = db.session.query(db.func.sum(VisitorStatistics.count)).join(
        Property,
        Property.property_id == VisitorStatistics.property_id
    ).filter(
        VisitorStatistics.report_date.between(start_date, end_date)
    )

    if visitor_type:
        query = query.filter(VisitorStatistics.visitor_type == visitor_type)

    if municipality:
        query = query.filter(Property.municipality == municipality)

    return query.scalar() or 0


def get_stay_count(start_date, end_date, stay_type, municipality=None):
    query = db.session.query(db.func.sum(VisitorStatistics.count)).join(
        Property,
        Property.property_id == VisitorStatistics.property_id
    ).filter(
        VisitorStatistics.report_date.between(start_date, end_date),
        VisitorStatistics.stay_type == stay_type
    )

    if municipality:
        query = query.filter(Property.municipality == municipality)

    return query.scalar() or 0