from flask import Blueprint, jsonify, request, url_for, render_template, flash, redirect, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from extension import db
from model import (
    User,
    Property,
    VisitorStatistics,
    BarangayMonthlyStatistics,
    PropertyMonthlyStatistics,
    VisitorRecord,
    VisitorDataUpload,
    PropertyReport,
    TouristReport
)
import pandas as pd
import os
from werkzeug.utils import secure_filename
from io import BytesIO

dashboard_bp = Blueprint('dashboard', __name__)


def init_dashboard_routes(app):
    app.register_blueprint(dashboard_bp)
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls', 'csv'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_property_stats(municipality):
    """Get aggregated property statistics for the dashboard"""
    try:
        stats = db.session.query(
            db.func.count(Property.property_id).label('total_properties'),
            db.func.sum(PropertyReport.total_rooms).label('total_rooms'),
            db.func.sum(PropertyReport.daytour_capacity).label('daytour_capacity'),
            db.func.sum(PropertyReport.overnight_capacity).label('overnight_capacity')
        ).outerjoin(
            PropertyReport,
            PropertyReport.property_id == Property.property_id
        ).filter(
            Property.municipality == municipality,
            Property.status == 'ACTIVE'
        ).first()

        return {
            'total_properties': stats.total_properties or 0,
            'total_rooms': stats.total_rooms or 0,
            'daytour_capacity': stats.daytour_capacity or 0,
            'overnight_capacity': stats.overnight_capacity or 0
        }
    except Exception as e:
        current_app.logger.error(f"Error in get_property_stats: {str(e)}")
        return {
            'total_properties': 0,
            'total_rooms': 0,
            'daytour_capacity': 0,
            'overnight_capacity': 0
        }


def get_visitor_stats(municipality, days=30):
    """Get visitor statistics for the dashboard"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Initialize default values
        result = {
            'total_visitors': 0,
            'local_visitors': 0,
            'foreign_visitors': 0,
            'daytour_visitors': 0,
            'overnight_visitors': 0,
            'revenue': 0
        }

        # From TouristReport
        tourist_stats = db.session.query(
            db.func.sum(TouristReport.total_daytour_guests).label('daytour'),
            db.func.sum(TouristReport.total_overnight_guests).label('overnight'),
            db.func.sum(TouristReport.total_revenue).label('revenue')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(start_date, end_date)
        ).first()

        if tourist_stats:
            result.update({
                'daytour_visitors': tourist_stats.daytour or 0,
                'overnight_visitors': tourist_stats.overnight or 0,
                'revenue': float(tourist_stats.revenue) if tourist_stats.revenue else 0
            })

        # From VisitorStatistics
        visitor_stats = db.session.query(
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
            VisitorStatistics.report_date.between(start_date, end_date)
        ).first()

        if visitor_stats:
            result.update({
                'total_visitors': visitor_stats.total or 0,
                'local_visitors': visitor_stats.local or 0,
                'foreign_visitors': visitor_stats.foreign or 0
            })

        return result

    except Exception as e:
        current_app.logger.error(f"Error in get_visitor_stats: {str(e)}")
        return {
            'total_visitors': 0,
            'local_visitors': 0,
            'foreign_visitors': 0,
            'daytour_visitors': 0,
            'overnight_visitors': 0,
            'revenue': 0
        }

@dashboard_bp.route('/mto/dashboard')
@jwt_required()
def mto_dashboard():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth.login'))

        municipality = user.municipality

        # Initialize default values
        property_stats = {
            'total_properties': 0,
            'total_rooms': 0,
            'daytour_capacity': 0,
            'overnight_capacity': 0
        }

        visitor_stats = {
            'total_visitors': 0,
            'local_visitors': 0,
            'foreign_visitors': 0,
            'daytour_visitors': 0,
            'overnight_visitors': 0,
            'revenue': 0
        }

        # Get property statistics if available
        try:
            property_stats = get_property_stats(municipality)
        except Exception as e:
            current_app.logger.error(f"Error getting property stats: {str(e)}")

        # Get visitor statistics if available (last 30 days)
        try:
            visitor_stats = get_visitor_stats(municipality)
        except Exception as e:
            current_app.logger.error(f"Error getting visitor stats: {str(e)}")

        # Get top 5 destinations
        top_destinations = []
        try:
            top_destinations = db.session.query(
                Property.property_name,
                Property.barangay,
                db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label(
                    'total_visitors')
            ).join(
                TouristReport,
                TouristReport.property_id == Property.property_id
            ).filter(
                Property.municipality == municipality,
                TouristReport.report_date >= datetime.now().date() - timedelta(days=30)
            ).group_by(
                Property.property_id,
                Property.property_name,
                Property.barangay
            ).order_by(
                db.desc('total_visitors')
            ).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"Error getting top destinations: {str(e)}")

        # Get recent uploads
        recent_uploads = []
        try:
            recent_uploads = VisitorDataUpload.query.filter_by(
                municipality=municipality
            ).order_by(
                VisitorDataUpload.upload_date.desc()
            ).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"Error getting recent uploads: {str(e)}")

        return render_template(
            'MTO_Dashboard.html',
            current_date=datetime.now().strftime('%B %d, %Y'),
            property_stats=property_stats,
            visitor_stats=visitor_stats,
            top_destinations=top_destinations,
            recent_uploads=recent_uploads,
            municipality=municipality
        )

    except Exception as e:
        current_app.logger.error(f"Error loading MTO dashboard: {str(e)}")
        flash('Failed to load dashboard data', 'error')
        return redirect(url_for('auth.login'))

@dashboard_bp.route('/mto/dashboard/upload', methods=['POST'])
@jwt_required()
def upload_visitor_data():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('dashboard.mto_dashboard'))

        file = request.files['file']

        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('dashboard.mto_dashboard'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process the Excel file
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)

                records_processed = 0

                # Process each row and save to database
                for _, row in df.iterrows():
                    # Validate and process the row
                    try:
                        # Example processing - adjust based on your Excel format
                        visitor_record = VisitorRecord(
                            date=pd.to_datetime(row['date']).date(),
                            property_id=row['property_id'],
                            visitor_type=row['visitor_type'],
                            stay_type=row['stay_type'],
                            municipality=municipality,
                            barangay=row['barangay'],
                            adults=row['adults'],
                            children=row['children'],
                            revenue=row['revenue']
                        )
                        db.session.add(visitor_record)
                        records_processed += 1
                    except Exception as e:
                        current_app.logger.error(f"Error processing row {_}: {str(e)}")
                        continue

                # Create upload record
                upload_record = VisitorDataUpload(
                    user_id=current_user_id,
                    municipality=municipality,
                    filename=filename,
                    records_processed=records_processed
                )
                db.session.add(upload_record)
                db.session.commit()

                flash(f'Successfully processed {records_processed} records', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing file: {str(e)}', 'error')
                current_app.logger.error(f"Error processing file: {str(e)}")
            finally:
                # Clean up - remove the uploaded file
                try:
                    os.remove(filepath)
                except Exception as e:
                    current_app.logger.error(f"Error removing file: {str(e)}")

        else:
            flash('Allowed file types are .xlsx, .xls, .csv', 'error')

    except Exception as e:
        flash('An error occurred during file upload', 'error')
        current_app.logger.error(f"Upload error: {str(e)}")

    return redirect(url_for('dashboard.mto_dashboard'))


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


def get_top_destinations(municipality=None, limit=5):
    # Calculate date range for the last 30 days
    today = datetime.now().date()
    last_30_days = today - timedelta(days=30)

    query = db.session.query(
        Property.property_id,
        Property.property_name,
        Property.barangay,
        Property.accommodation_type,
        Property.status,
        db.func.sum(VisitorStatistics.count).label('total_visitors'),
        db.func.sum(db.case(
            [(VisitorStatistics.visitor_type == 'Local', VisitorStatistics.count)],
            else_=0
        )).label('local_visitors'),
        db.func.sum(db.case(
            [(VisitorStatistics.visitor_type == 'Foreign', VisitorStatistics.count)],
            else_=0
        )).label('foreign_visitors'),
        db.func.sum(db.case(
            [(VisitorStatistics.stay_type == 'Day Tour', VisitorStatistics.count)],
            else_=0
        )).label('day_tour_visitors'),
        db.func.sum(db.case(
            [(VisitorStatistics.stay_type == 'Overnight', VisitorStatistics.count)],
            else_=0
        )).label('overnight_visitors')
    ).join(
        VisitorStatistics,
        VisitorStatistics.property_id == Property.property_id
    ).filter(
        VisitorStatistics.report_date.between(last_30_days, today)
    ).group_by(
        Property.property_id,
        Property.property_name,
        Property.barangay,
        Property.accommodation_type,
        Property.status
    ).order_by(
        db.desc('total_visitors')
    ).limit(limit)

    if municipality:
        query = query.filter(Property.municipality == municipality)

    return query.all()

def get_visitor_trends(start_date, end_date, municipality=None):
    query = db.session.query(
        VisitorStatistics.report_date,
        db.func.sum(VisitorStatistics.count).label('total_visitors')
    ).join(
        Property,
        Property.property_id == VisitorStatistics.property_id
    ).filter(
        VisitorStatistics.report_date.between(start_date, end_date)
    ).group_by(
        VisitorStatistics.report_date
    ).order_by(
        VisitorStatistics.report_date
    )

    if municipality:
        query = query.filter(Property.municipality == municipality)

    return query.all()


@dashboard_bp.route('/api/dashboard/summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    municipality = user.municipality

    # Calculate date ranges
    today = datetime.now().date()
    last_month = today - timedelta(days=30)

    try:
        # Get total properties
        total_properties = Property.query.filter_by(
            status='Active',
            municipality=municipality
        ).count()

        # Get visitor statistics
        total_visitors = get_visitor_count(last_month, today, municipality=municipality)
        local_visitors = get_visitor_count(last_month, today, 'Local', municipality)
        foreign_visitors = get_visitor_count(last_month, today, 'Foreign', municipality)

        # Calculate percentage changes (simplified - in real app you'd compare with previous period)
        properties_change = 8  # Example value
        visitors_change = 9  # Example value

        return jsonify({
            'success': True,
            'data': {
                'total_properties': total_properties,
                'local_visitors': local_visitors,
                'foreign_visitors': foreign_visitors,
                'total_visitors': total_visitors,
                'properties_change': properties_change,
                'visitors_change': visitors_change
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dashboard_bp.route('/api/dashboard/destinations', methods=['GET'])
@jwt_required()
def get_destinations_list():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    municipality = user.municipality

    try:
        # Get filter parameters
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Base query
        query = Property.query.filter_by(municipality=municipality)

        # Apply search filter
        if search:
            query = query.filter(
                db.or_(
                    Property.property_name.ilike(f'%{search}%'),
                    Property.barangay.ilike(f'%{search}%')
                )
            )

        # Pagination
        paginated = query.paginate(page=page, per_page=per_page)

        # Get statistics for each property
        properties = []
        current_month = datetime.now().month
        current_year = datetime.now().year

        for prop in paginated.items:
            stats = PropertyMonthlyStatistics.query.filter_by(
                property_id=prop.property_id,
                year=current_year,
                month=current_month
            ).first()

            properties.append({
                'property_id': prop.property_id,
                'property_name': prop.property_name,
                'barangay': prop.barangay,
                'type': prop.accommodation_type,
                'status': prop.status,
                'local_visitors': stats.local_visitors if stats else 0,
                'foreign_visitors': stats.foreign_visitors if stats else 0,
                'day_tour_visitors': stats.day_tour_visitors if stats else 0,
                'overnight_visitors': stats.overnight_visitors if stats else 0
            })

        return jsonify({
            'success': True,
            'data': {
                'properties': properties,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@dashboard_bp.route('/api/dashboard/top-destinations', methods=['GET'])
@jwt_required()
def get_top_destinations_api():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    municipality = user.municipality

    try:
        period = request.args.get('period', 'month')
        today = datetime.now().date()

        if period == 'week':
            start_date = today - timedelta(days=7)
        elif period == 'year':
            start_date = today - timedelta(days=365)
        else:  # month
            start_date = today - timedelta(days=30)

        # Get top destinations by barangay
        top_destinations = db.session.query(
            Property.barangay,
            Property.property_name,
            db.func.sum(PropertyMonthlyStatistics.total_visitors).label('total_visitors'),
            db.func.sum(PropertyMonthlyStatistics.local_visitors).label('local_visitors'),
            db.func.sum(PropertyMonthlyStatistics.foreign_visitors).label('foreign_visitors'),
            db.func.sum(PropertyMonthlyStatistics.day_tour_visitors).label('day_tour_visitors'),
            db.func.sum(PropertyMonthlyStatistics.overnight_visitors).label('overnight_visitors')
        ).join(
            PropertyMonthlyStatistics,
            PropertyMonthlyStatistics.property_id == Property.property_id
        ).filter(
            Property.municipality == municipality,
            PropertyMonthlyStatistics.year == today.year,
            PropertyMonthlyStatistics.month == today.month
        ).group_by(
            Property.barangay,
            Property.property_name
        ).order_by(
            db.desc('total_visitors')
        ).limit(5).all()

        result = []
        for dest in top_destinations:
            result.append({
                'barangay': dest.barangay,
                'property_name': dest.property_name,
                'total_visitors': dest.total_visitors or 0,
                'local_visitors': dest.local_visitors or 0,
                'foreign_visitors': dest.foreign_visitors or 0,
                'day_tour_visitors': dest.day_tour_visitors or 0,
                'overnight_visitors': dest.overnight_visitors or 0
            })

        return jsonify({
            'success': True,
            'data': result,
            'period': period
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@dashboard_bp.route('/api/dashboard/visitor-trends', methods=['GET'])
@jwt_required()
def get_visitor_trends_api():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    municipality = user.municipality

    try:
        # Get period parameter (default: 6months)
        period = request.args.get('period', '6months')  # 3months, 6months, year

        # Determine number of months to include
        if period == '3months':
            months = 3
        elif period == 'year':
            months = 12
        else:  # 6months
            months = 6

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30 * months)

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