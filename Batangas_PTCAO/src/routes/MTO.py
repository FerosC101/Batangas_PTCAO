from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import User, Property, VisitorStatistics, VisitorDataUpload, PropertyStatus, \
    PropertyReport, TouristReport

mto_bp = Blueprint('mto', __name__, url_prefix='/mto')

def init_mto_routes(app):
    app.register_blueprint(mto_bp)

@mto_bp.route('/dashboard')
@jwt_required()
def dashboard():
    if 'account_id' not in session or session.get('account_type') != 'mto':
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))

    municipality = user.municipality
    today = datetime.now().date()
    last_30_days = today - timedelta(days=30)

    # Initialize dashboard stats
    dashboard_stats = {
        'active_properties': 0,
        'local_visitors': 0,
        'foreign_visitors': 0,
        'total_visitors': 0
    }

    try:
        # 1. Get active properties count from Property
        dashboard_stats['active_properties'] = Property.query.filter_by(
            status=PropertyStatus.ACTIVE,
            municipality=municipality
        ).count()

        # 2. Get visitor statistics from TouristReport
        visitor_data = db.session.query(
            db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total'),
            db.func.sum(TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors).label('foreign'),
            db.func.sum(
                (TouristReport.total_daytour_guests + TouristReport.total_overnight_guests) -
                (TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors)
            ).label('local')
        ).join(
            Property,
            Property.property_id == TouristReport.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(last_30_days, today)
        ).first()

        if visitor_data:
            dashboard_stats.update({
                'total_visitors': visitor_data.total or 0,
                'local_visitors': visitor_data.local or 0,
                'foreign_visitors': visitor_data.foreign or 0
            })

        # 3. Get top destinations with all required fields
        top_destinations = db.session.query(
            Property.property_id,
            Property.property_name,
            Property.barangay,
            Property.accommodation_type.label('type'),
            Property.status,
            db.func.sum(TouristReport.total_daytour_guests + TouristReport.total_overnight_guests).label('total_visitors'),
            db.func.sum(
                (TouristReport.total_daytour_guests + TouristReport.total_overnight_guests) -
                (TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors)
            ).label('local_visitors'),
            db.func.sum(TouristReport.foreign_daytour_visitors + TouristReport.foreign_overnight_visitors).label('foreign_visitors'),
            db.func.sum(TouristReport.total_daytour_guests).label('daytour_visitors'),
            db.func.sum(TouristReport.total_overnight_guests).label('overnight_visitors')
        ).join(
            TouristReport,
            TouristReport.property_id == Property.property_id
        ).filter(
            Property.municipality == municipality,
            TouristReport.report_date.between(last_30_days, today)
        ).group_by(
            Property.property_id,
            Property.property_name,
            Property.barangay,
            Property.accommodation_type,
            Property.status
        ).order_by(
            db.desc('total_visitors')
        ).limit(5).all()

        # 4. Get recent uploads
        recent_uploads = VisitorDataUpload.query.filter_by(
            municipality=municipality
        ).order_by(
            VisitorDataUpload.upload_date.desc()
        ).limit(5).all()

    except Exception as e:
        current_app.logger.error(f"Error loading dashboard data: {str(e)}")
        flash('Error loading dashboard data', 'error')
        top_destinations = []
        recent_uploads = []

    return render_template(
        'MTO_Dashboard.html',
        dashboard_stats=dashboard_stats,
        top_destinations=top_destinations,
        recent_uploads=recent_uploads,
        municipality=municipality,
        current_date=today.strftime('%B %d, %Y')
    )

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
    # Start building the query
    query = db.session.query(
        Property.property_id,
        Property.property_name,
        Property.barangay,
        Property.accommodation_type,
        Property.status,
        db.func.sum(VisitorStatistics.count).label('total_visitors'),
        db.func.sum(
            db.case(
                (VisitorStatistics.visitor_type == 'Local', VisitorStatistics.count),
                else_=0
            )
        ).label('local_visitors'),
        db.func.sum(
            db.case(
                (VisitorStatistics.visitor_type == 'Foreign', VisitorStatistics.count),
                else_=0
            )
        ).label('foreign_visitors'),
        db.func.sum(
            db.case(
                (VisitorStatistics.stay_type == 'Day Tour', VisitorStatistics.count),
                else_=0
            )
        ).label('day_tour_visitors'),
        db.func.sum(
            db.case(
                (VisitorStatistics.stay_type == 'Overnight', VisitorStatistics.count),
                else_=0
            )
        ).label('overnight_visitors')
    ).join(
        VisitorStatistics,
        VisitorStatistics.property_id == Property.property_id
    )

    # Apply municipality filter first if provided
    if municipality:
        query = query.filter(Property.municipality == municipality)

    # Then apply grouping, ordering and limiting
    query = query.group_by(
        Property.property_id,
        Property.property_name,
        Property.barangay,
        Property.accommodation_type,
        Property.status
    ).order_by(
        db.desc('total_visitors')
    ).limit(limit)

    return query.all()

@mto_bp.route('/register', methods=['GET', 'POST'])
def mto_registration():
    if request.method == 'POST':
        try:
            # Get and validate form data
            required_fields = [
                'full-name', 'municipality', 'id-number', 'designation',
                'email', 'gender', 'birthday', 'username',
                'password', 'password-confirmation'
            ]

            form_data = {field: request.form.get(field, '').strip() for field in required_fields}

            # Check for empty fields
            if not all(form_data.values()):
                flash('All fields are required', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Validate password match
            if form_data['password'] != form_data['password-confirmation']:
                flash('Passwords do not match', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Check for existing username
            if User.query.filter_by(username=form_data['username']).first():
                flash('Username already exists. Please choose another one.', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Check for existing email
            if User.query.filter_by(email=form_data['email'].lower()).first():
                flash('Email already registered', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Check for existing ID number
            if User.query.filter_by(id_number=form_data['id-number']).first():
                flash('ID number already registered', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Parse birthday
            try:
                birthday = datetime.strptime(form_data['birthday'], '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format for birthday', 'error')
                return redirect(url_for('mto.mto_registration'))

            # Create new user
            new_user = User(
                full_name=form_data['full-name'],
                municipality=form_data['municipality'],
                id_number=form_data['id-number'],
                designation=form_data['designation'],
                email=form_data['email'].lower(),
                gender=form_data['gender'],
                birthday=birthday,
                username=form_data['username'],
                is_active=False,  # Requires admin approval
                is_archived=False
            )

            # Set password using bcrypt
            new_user.set_password(form_data['password'])

            # Save to database
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! Your account will be activated after review.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'error')
            return redirect(url_for('mto.mto_registration'))

    return render_template('Register.html')
