from flask import Blueprint, jsonify, request, url_for, render_template, flash, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import (
    User,
    Property,
    VisitorStatistics,
    BarangayMonthlyStatistics,
    PropertyMonthlyStatistics,
    VisitorRecord,
    VisitorDataUpload
)
import pandas as pd
import os
from werkzeug.utils import secure_filename
from io import BytesIO

dashboard_bp = Blueprint('dashboard', __name__)


def init_dashboard_routes(app):
    app.register_blueprint(dashboard_bp)
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@dashboard_bp.route('/mto/dashboard')
@jwt_required()
def mto_dashboard():
    """Render the MTO Dashboard with all necessary statistics and data"""
    try:
        # Get current user identity
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        municipality = user.municipality

        # Calculate date ranges
        today = datetime.now().date()
        last_30_days = today - timedelta(days=30)
        last_7_days = today - timedelta(days=7)

        # 1. Get summary statistics filtered by municipality
        summary_stats = {
            'total_properties': Property.query.filter_by(
                status='Active',
                municipality=municipality
            ).count(),
            'total_visitors': get_visitor_count(last_30_days, today, municipality=municipality),
            'local_visitors': get_visitor_count(last_30_days, today, 'Local', municipality),
            'foreign_visitors': get_visitor_count(last_30_days, today, 'Foreign', municipality),
            'new_properties': Property.query.filter(
                Property.registration_date >= last_30_days,
                Property.municipality == municipality
            ).count()
        }

        # 2. Get top 5 destinations in the municipality
        top_destinations = get_top_destinations(municipality=municipality, limit=5)

        # 3. Get recent visitor trends (weekly) for the municipality
        visitor_trends = get_visitor_trends(last_7_days, today, municipality)

        # 4. Get property status distribution for the municipality
        status_distribution = {
            'Active': Property.query.filter_by(
                status='Active',
                municipality=municipality
            ).count(),
            'Maintenance': Property.query.filter_by(
                status='Maintenance',
                municipality=municipality
            ).count()
        }

        # Get recent uploads
        recent_uploads = VisitorDataUpload.query.filter_by(
            municipality=municipality
        ).order_by(
            VisitorDataUpload.upload_date.desc()
        ).limit(5).all()

        return render_template(
            'MTO_Dashboard.html',
            current_date=today.strftime('%B %d, %Y'),
            summary=summary_stats,
            top_destinations=top_destinations,
            visitor_trends=visitor_trends,
            status_distribution=status_distribution,
            recent_uploads=recent_uploads,
            user_id=current_user_id,
            municipality=municipality
        )

    except Exception as e:
        app.logger.error(f"Error loading MTO dashboard: {str(e)}")
        flash('Failed to load dashboard data', 'error')
        return redirect(url_for('login')

                        @ dashboard_bp.route('/mto/dashboard/upload', methods=['POST'])
                        @ jwt_required()


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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
                        app.logger.error(f"Error processing row {_}: {str(e)}")
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
                app.logger.error(f"Error processing file: {str(e)}")
            finally:
                # Clean up - remove the uploaded file
                try:
                    os.remove(filepath)
                except Exception as e:
                    app.logger.error(f"Error removing file: {str(e)}")

        else:
            flash('Allowed file types are .xlsx, .xls, .csv', 'error')

    except Exception as e:
        flash('An error occurred during file upload', 'error')
        app.logger.error(f"Upload error: {str(e)}")

    return redirect(url_for('dashboard.mto_dashboard'))


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls', 'csv'}


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
    query = db.session.query(
        Property.property_id,
        Property.property_name,
        Property.barangay,
        db.func.sum(VisitorStatistics.count).label('total_visitors')
    ).join(
        VisitorStatistics,
        VisitorStatistics.property_id == Property.property_id
    ).group_by(
        Property.property_id,
        Property.property_name,
        Property.barangay
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
        # Get time period parameter
        period = request.args.get('period', 'month')  # month, week, year

        # Determine date range based on period
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
            db.func.sum(PropertyMonthlyStatistics.total_visitors).label('total_visitors'),
            db.func.sum(PropertyMonthlyStatistics.local_visitors).label('local_visitors'),
            db.func.sum(PropertyMonthlyStatistics.foreign_visitors).label('foreign_visitors')
        ).join(
            PropertyMonthlyStatistics,
            PropertyMonthlyStatistics.property_id == Property.property_id
        ).filter(
            PropertyMonthlyStatistics.year == start_date.year,
            PropertyMonthlyStatistics.month == start_date.month,
            Property.municipality == municipality
        ).group_by(
            Property.barangay
        ).order_by(
            db.desc('total_visitors')
        ).limit(5).all()

        result = []
        for dest in top_destinations:
            local_percent = round((dest.local_visitors / dest.total_visitors) * 100) if dest.total_visitors else 0
            foreign_percent = 100 - local_percent

            result.append({
                'barangay': dest.barangay,
                'total_visitors': dest.total_visitors,
                'local_visitors': dest.local_visitors,
                'foreign_visitors': dest.foreign_visitors,
                'local_percent': local_percent,
                'foreign_percent': foreign_percent
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