from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required
from model import User, Property, Event, TouristReport
from extension import db
from datetime import datetime, timedelta
from sqlalchemy import func


def init_admin_dashboard_routes(app):
    admin_dashboard_bp = Blueprint('admin_dashboard', __name__)

    @admin_dashboard_bp.route('/dashboard')
    @jwt_required()
    def admin_dashboard():
        # Get counts for dashboard cards
        total_users = User.query.filter_by(is_archived=False).count()
        total_properties = Property.query.count()

        total_visitors_result = db.session.query(
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests)
        ).scalar()
        total_visitors = total_visitors_result if total_visitors_result else 0

        total_events = Event.query.count()

        # Get recent activities
        recent_users = User.query.filter_by(is_archived=False).order_by(
            User.created_at.desc()).limit(5).all()

        recent_visitors = TouristReport.query.join(Property).order_by(
            TouristReport.report_date.desc()).limit(5).all()

        # Get visitor statistics
        visitor_stats = get_visitor_stats()

        return render_template('ADMIN_dashboard.html',
                               total_users=total_users,
                               total_properties=total_properties,
                               total_visitors=total_visitors,
                               total_events=total_events,
                               recent_users=recent_users,
                               recent_visitors=recent_visitors,
                               visitor_stats=visitor_stats)

    def get_visitor_stats():
        date_7_days_ago = datetime.now() - timedelta(days=7)

        daily_stats = db.session.query(
            func.date(TouristReport.report_date).label('day'),
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('count')
        ).filter(TouristReport.report_date >= date_7_days_ago
                 ).group_by('day'
                            ).order_by('day').all()

        visitor_type_stats = [
            {'type': 'Day Tour', 'count': db.session.query(func.sum(TouristReport.total_daytour_guests)).scalar() or 0},
            {'type': 'Overnight',
             'count': db.session.query(func.sum(TouristReport.total_overnight_guests)).scalar() or 0}
        ]

        return {
            'daily': [{'day': stat.day.strftime('%Y-%m-%d'), 'count': stat.count or 0} for stat in daily_stats],
            'visitor_type': visitor_type_stats
        }

    @admin_dashboard_bp.route('/dashboard/stats')
    @jwt_required()
    def dashboard_stats():
        stats = get_visitor_stats()
        return jsonify(stats)

    @admin_dashboard_bp.route('/')
    @jwt_required()
    def admin_redirect():
        return redirect(url_for('admin_dashboard.admin_dashboard'))

    app.register_blueprint(admin_dashboard_bp, url_prefix='/admin')