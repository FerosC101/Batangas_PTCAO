from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required
from Batangas_PTCAO.src.model import User, VisitorRecord, Property, Event
from Batangas_PTCAO.src.extension import db
from datetime import datetime, timedelta
from sqlalchemy import func, extract

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)


@admin_dashboard_bp.route('/admin/dashboard')
@jwt_required()
def admin_dashboard():
    # Get counts for dashboard cards
    total_users = User.query.count()
    total_properties = Property.query.count()
    total_visitors = VisitorRecord.query.with_entities(
        func.sum(VisitorRecord.adults + VisitorRecord.children)).scalar() or 0
    total_events = Event.query.count()

    # Get recent activities
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_visitors = VisitorRecord.query.order_by(VisitorRecord.created_at.desc()).limit(5).all()

    # Get visitor statistics for the chart
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
    # Get visitor counts for last 7 days
    date_7_days_ago = datetime.now() - timedelta(days=7)

    daily_stats = db.session.query(
        func.date(VisitorRecord.date).label('day'),
        func.sum(VisitorRecord.adults + VisitorRecord.children).label('count')
    ).filter(VisitorRecord.date >= date_7_days_ago
             ).group_by('day'
                        ).order_by('day').all()

    # Get visitor counts by municipality
    municipality_stats = db.session.query(
        VisitorRecord.municipality,
        func.sum(VisitorRecord.adults + VisitorRecord.children).label('count')
    ).group_by(VisitorRecord.municipality
               ).order_by(func.sum(VisitorRecord.adults + VisitorRecord.children).desc()
                          ).limit(5).all()

    # Get visitor type distribution
    visitor_type_stats = db.session.query(
        VisitorRecord.visitor_type,
        func.sum(VisitorRecord.adults + VisitorRecord.children).label('count')
    ).group_by(VisitorRecord.visitor_type).all()

    return {
        'daily': [{'day': stat.day.strftime('%Y-%m-%d'), 'count': stat.count} for stat in daily_stats],
        'municipality': [{'name': stat.municipality, 'count': stat.count} for stat in municipality_stats],
        'visitor_type': [{'type': stat.visitor_type, 'count': stat.count} for stat in visitor_type_stats]
    }


@admin_dashboard_bp.route('/admin/dashboard/stats')
@jwt_required()
def dashboard_stats():
    stats = get_visitor_stats()
    return jsonify(stats)