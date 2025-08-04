from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from extension import db
from model import (
    Property,
    PropertyReport,
    TouristReport,
    User
)
from sqlalchemy import func, extract, case, and_, or_
import pandas as pd
import os
from werkzeug.utils import secure_filename

ptcao_dashboard_bp = Blueprint('ptcao_dashboard', __name__)

def init_ptcao_dashboard_routes(app):
    app.register_blueprint(ptcao_dashboard_bp)
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder


@ptcao_dashboard_bp.route('/ptcao/dashboard')
@jwt_required()
def ptcao_dashboard():
    try:
        current_user_id = get_jwt_identity()

        if current_user_id != "ptcao":
            flash('Unauthorized access', 'error')
            return redirect(url_for('login'))

        current_year = datetime.now().year

        # Initialize dashboard stats
        dashboard_stats = {
            'active_properties': 0,
            'total_visitors': 0,
            'local_visitors': 0,
            'foreign_visitors': 0,
            'daytour_visitors': 0,
            'overnight_visitors': 0
        }

        # 1. Get property statistics
        prop_stats = db.session.query(
            func.count(Property.property_id).label('total_properties')
        ).join(
            PropertyReport, PropertyReport.property_id == Property.property_id
        ).filter(
            Property.status == 'ACTIVE'
        ).first()

        if prop_stats:
            dashboard_stats['active_properties'] = prop_stats.total_properties or 0

        # 2. Get visitor statistics from TouristReport
        visitor_data = db.session.query(
            func.sum(TouristReport.total_daytour_guests).label('daytour'),
            func.sum(TouristReport.total_overnight_guests).label('overnight'),
            func.sum(TouristReport.foreign_daytour_visitors).label('foreign_daytour'),
            func.sum(TouristReport.foreign_overnight_visitors).label('foreign_overnight')
        ).filter(
            extract('year', TouristReport.report_date) == current_year
        ).first()

        if visitor_data:
            dashboard_stats.update({
                'daytour_visitors': visitor_data.daytour or 0,
                'overnight_visitors': visitor_data.overnight or 0,
                'total_visitors': (visitor_data.daytour or 0) + (visitor_data.overnight or 0),
                'foreign_visitors': (visitor_data.foreign_daytour or 0) + (visitor_data.foreign_overnight or 0),
                'local_visitors': ((visitor_data.daytour or 0) + (visitor_data.overnight or 0)) -
                                  ((visitor_data.foreign_daytour or 0) + (visitor_data.foreign_overnight or 0))
            })

        # 3. Get municipal summary from TouristReport
        municipal_summary = []
        municipalities = db.session.query(Property.municipality).distinct().all()

        for mun in municipalities:
            mun_data = db.session.query(
                func.count(Property.property_id).label('total_properties'),
                func.sum(TouristReport.total_daytour_guests).label('daytour'),
                func.sum(TouristReport.total_overnight_guests).label('overnight'),
                func.sum(TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors).label(
                    'foreign')
            ).join(
                TouristReport, TouristReport.property_id == Property.property_id
            ).filter(
                Property.municipality == mun.municipality,
                extract('year', TouristReport.report_date) == current_year
            ).first()

            if mun_data:
                total_visitors = (mun_data.daytour or 0) + (mun_data.overnight or 0)
                foreign_visitors = mun_data.foreign or 0
                local_visitors = total_visitors - foreign_visitors

                municipal_summary.append({
                    'municipality': mun.municipality,
                    'total_properties': mun_data.total_properties or 0,
                    'daytour_visitors': mun_data.daytour or 0,
                    'overnight_visitors': mun_data.overnight or 0,
                    'foreign_visitors': foreign_visitors,
                    'local_visitors': local_visitors,
                    'total_visitors': total_visitors,
                    'last_update': datetime.now().date()
                })

        # 4. Get monthly trend data
        monthly_data = [0] * 12
        trends = db.session.query(
            extract('month', TouristReport.report_date).label('month'),
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors')
        ).filter(
            extract('year', TouristReport.report_date) == current_year
        ).group_by('month').order_by('month').all()

        for trend in trends:
            monthly_data[int(trend.month) - 1] = int(trend.total_visitors or 0)

        # 5. Get top destinations
        top_destinations = db.session.query(
            Property.property_name,
            Property.municipality,
            Property.barangay,
            Property.accommodation_type.label('type'),
            Property.status,
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors')
        ).join(
            TouristReport, TouristReport.property_id == Property.property_id
        ).filter(
            extract('year', TouristReport.report_date) == current_year
        ).group_by(
            Property.property_id
        ).order_by(
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).desc()
        ).limit(10).all()

        return render_template(
            'PTCAO_Dashboard.html',
            dashboard_stats=dashboard_stats,
            municipal_summary=municipal_summary,
            top_destinations=top_destinations,
            current_year=current_year,
            current_date=datetime.now().strftime('%B %d, %Y'),
            monthly_data=monthly_data
        )

    except Exception as e:
        current_app.logger.error(f"Error loading PTCAO dashboard: {str(e)}")
        flash('Failed to load dashboard data', 'error')
        return redirect(url_for('login'))

def get_municipal_summary(current_year):
    """Get summary data for all municipalities"""
    return db.session.query(
        Property.municipality,
        func.count(Property.property_id).label('total_properties'),
        func.sum(case((PropertyReport.dot_accredited == True, 1), else_=0)).label('dot_accredited'),
        func.sum(case((PropertyReport.ptcao_registered == True, 1), else_=0)).label('ptcao_registered'),
        func.sum(TouristReport.total_daytour_guests).label('daytour_visitors'),
        func.sum(TouristReport.total_overnight_guests).label('overnight_visitors'),
        func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors'),
        func.sum(TouristReport.total_revenue).label('total_revenue'),
        func.max(TouristReport.report_date).label('last_update')
    ).join(
        PropertyReport, Property.property_id == PropertyReport.property_id
    ).join(
        TouristReport, Property.property_id == TouristReport.property_id
    ).filter(
        extract('year', TouristReport.report_date) == current_year
    ).group_by(
        Property.municipality
    ).order_by(
        Property.municipality
    ).all()


def get_monthly_trend(current_year):
    """Get monthly visitor trend data for the current year"""
    monthly_data = [0] * 12
    trends = db.session.query(
        extract('month', TouristReport.report_date).label('month'),
        func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors')
    ).filter(
        extract('year', TouristReport.report_date) == current_year
    ).group_by('month').order_by('month').all()

    for trend in trends:
        monthly_data[int(trend.month) - 1] = int(trend.total_visitors or 0)

    return monthly_data


def get_top_destinations(current_year, limit=10):
    """Get top destinations by visitor count"""
    return db.session.query(
        Property.property_name,
        Property.municipality,
        Property.barangay,
        Property.accommodation_type.label('type'),
        Property.status,
        func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors')
    ).join(
        TouristReport, Property.property_id == TouristReport.property_id
    ).filter(
        extract('year', TouristReport.report_date) == current_year
    ).group_by(
        Property.property_id
    ).order_by(
        func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).desc()
    ).limit(limit).all()


@ptcao_dashboard_bp.route('/api/ptcao/summary', methods=['GET'])
@jwt_required()
def get_ptcao_summary():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or getattr(user, 'account_type', None) != 'ptcao':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        # Get filter parameters
        municipality = request.args.get('municipality')
        year = int(request.args.get('year', datetime.now().year))
        month = request.args.get('month')

        # Base queries
        property_query = db.session.query(
            func.count(Property.property_id),
            func.sum(PropertyReport.total_rooms),
            func.sum(case((PropertyReport.dot_accredited == True, 1), else_=0)),
            func.sum(case((PropertyReport.ptcao_registered == True, 1), else_=0))
        ).join(PropertyReport, Property.property_id == PropertyReport.property_id)

        tourist_query = db.session.query(
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests),
            func.sum(TouristReport.total_revenue)
        ).join(Property, Property.property_id == TouristReport.property_id)

        # Apply filters
        if municipality:
            property_query = property_query.filter(Property.municipality == municipality)
            tourist_query = tourist_query.filter(Property.municipality == municipality)

        if month:
            tourist_query = tourist_query.filter(
                extract('year', TouristReport.report_date) == year,
                extract('month', TouristReport.report_date) == month
            )
        else:
            tourist_query = tourist_query.filter(
                extract('year', TouristReport.report_date) == year
            )

        # Execute queries
        prop_stats = property_query.first()
        tour_stats = tourist_query.first()

        return jsonify({
            'success': True,
            'data': {
                'total_properties': prop_stats[0] or 0,
                'total_rooms': prop_stats[1] or 0,
                'dot_accredited': prop_stats[2] or 0,
                'ptcao_registered': prop_stats[3] or 0,
                'total_visitors': tour_stats[0] or 0,
                'total_revenue': float(tour_stats[1]) if tour_stats[1] else 0
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@ptcao_dashboard_bp.route('/api/ptcao/municipalities', methods=['GET'])
@jwt_required()
def get_municipalities_data():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or getattr(user, 'account_type', None) != 'ptcao':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        # Get filter parameters
        year = int(request.args.get('year', datetime.now().year))
        month = request.args.get('month')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '')

        # Base query
        query = db.session.query(
            Property.municipality,
            func.count(Property.property_id).label('total_properties'),
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors'),
            func.sum(TouristReport.total_revenue).label('total_revenue'),
            func.max(TouristReport.report_date).label('last_update')
        ).join(
            TouristReport, Property.property_id == TouristReport.property_id
        )

        # Apply filters
        if month:
            query = query.filter(
                extract('year', TouristReport.report_date) == year,
                extract('month', TouristReport.report_date) == month
            )
        else:
            query = query.filter(
                extract('year', TouristReport.report_date) == year
            )

        if search:
            query = query.filter(
                Property.municipality.ilike(f'%{search}%')
            )

        # Group and paginate
        query = query.group_by(Property.municipality)
        paginated = query.paginate(page=page, per_page=per_page)

        return jsonify({
            'success': True,
            'data': {
                'municipalities': [{
                    'municipality': item.municipality,
                    'total_properties': item.total_properties or 0,
                    'total_visitors': item.total_visitors or 0,
                    'total_revenue': float(item.total_revenue) if item.total_revenue else 0,
                    'last_update': item.last_update.strftime('%Y-%m-%d') if item.last_update else None
                } for item in paginated.items],
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@ptcao_dashboard_bp.route('/api/ptcao/properties', methods=['GET'])
@jwt_required()
def get_properties_data():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user or getattr(user, 'account_type', None) != 'ptcao':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403

        # Get filter parameters
        municipality = request.args.get('municipality')
        year = int(request.args.get('year', datetime.now().year))
        month = request.args.get('month')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '')

        # Base query
        query = db.session.query(
            Property.property_id,
            Property.property_name,
            Property.municipality,
            Property.barangay,
            Property.accommodation_type,
            Property.status,
            func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors'),
            func.sum(TouristReport.total_revenue).label('total_revenue')
        ).join(
            TouristReport, Property.property_id == TouristReport.property_id
        )

        # Apply filters
        if municipality:
            query = query.filter(Property.municipality == municipality)

        if month:
            query = query.filter(
                extract('year', TouristReport.report_date) == year,
                extract('month', TouristReport.report_date) == month
            )
        else:
            query = query.filter(
                extract('year', TouristReport.report_date) == year
            )

        if search:
            query = query.filter(
                or_(
                    Property.property_name.ilike(f'%{search}%'),
                    Property.barangay.ilike(f'%{search}%')
                )
            )

        # Group and paginate
        query = query.group_by(Property.property_id)
        paginated = query.paginate(page=page, per_page=per_page)

        return jsonify({
            'success': True,
            'data': {
                'properties': [{
                    'property_id': item.property_id,
                    'property_name': item.property_name,
                    'municipality': item.municipality,
                    'barangay': item.barangay,
                    'type': item.accommodation_type,
                    'status': item.status,
                    'total_visitors': item.total_visitors or 0,
                    'total_revenue': float(item.total_revenue) if item.total_revenue else 0
                } for item in paginated.items],
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500