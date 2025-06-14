from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
from extension import db
from model import (
    User,
    Property,
    VisitorRecord,
    VisitorType,
    StayType
)

visitor_records_bp = Blueprint('visitor_records', __name__, template_folder='../../templates')


def init_visitor_records_routes(app):
    app.register_blueprint(visitor_records_bp)


@visitor_records_bp.route('/mto/visitors')
@jwt_required()
def mto_visitors():
    """Render the MTO Visitors page"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    return render_template('MTO_Visitors.html', municipality=user.municipality)


@visitor_records_bp.route('/api/visitors', methods=['GET'])
@jwt_required()
def get_visitor_records():
    """Get visitor records for the MTO's municipality with filtering"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Get filter parameters
        date_range = request.args.get('date_range', 'this_month')
        barangay = request.args.get('barangay', 'all')
        visitor_type = request.args.get('visitor_type', 'all')
        stay_type = request.args.get('stay_type', 'all')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '')

        # Calculate date range
        today = datetime.now().date()
        start_date, end_date = get_date_range(date_range, today)

        # Base query
        query = db.session.query(
            VisitorRecord,
            Property.property_name
        ).join(
            Property,
            Property.property_id == VisitorRecord.property_id
        ).filter(
            Property.municipality == user.municipality,
            VisitorRecord.date.between(start_date, end_date)
        )

        # Apply barangay filter
        if barangay != 'all':
            query = query.filter(VisitorRecord.barangay == barangay)

        # Apply visitor type filter
        if visitor_type != 'all':
            query = query.filter(VisitorRecord.visitor_type == visitor_type)

        # Apply stay type filter
        if stay_type != 'all':
            query = query.filter(VisitorRecord.stay_type == stay_type)

        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Property.property_name.ilike(f'%{search}%'),
                    VisitorRecord.barangay.ilike(f'%{search}%'),
                    VisitorRecord.record_id.ilike(f'%{search}%')
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        paginated = query.order_by(
            VisitorRecord.date.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()

        # Format results
        visitors = []
        for record, property_name in paginated:
            visitors.append({
                'id': record.record_id,
                'date': record.date.strftime('%b %d, %Y'),
                'visitor_type': record.visitor_type.value,
                'barangay': record.barangay,
                'stay_type': record.stay_type.value,
                'adults': record.adults,
                'children': record.children,
                'revenue': float(record.revenue) if record.revenue else 0.0,
                'property_name': property_name
            })

        return jsonify({
            'success': True,
            'data': {
                'visitors': visitors,
                'total': total,
                'pages': (total + per_page - 1) // per_page,
                'current_page': page
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@visitor_records_bp.route('/api/visitors/barangays', methods=['GET'])
@jwt_required()
def get_barangays():
    """Get list of barangays for the MTO's municipality"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        barangays = db.session.query(
            VisitorRecord.barangay
        ).join(
            Property,
            Property.property_id == VisitorRecord.property_id
        ).filter(
            Property.municipality == user.municipality
        ).distinct().all()

        barangay_list = [b[0] for b in barangays if b[0]]
        barangay_list.sort()

        return jsonify({
            'success': True,
            'data': barangay_list
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def get_date_range(date_range, today):
    """Helper function to calculate date ranges"""
    if date_range == 'last_7_days':
        start_date = today - timedelta(days=7)
    elif date_range == 'last_30_days':
        start_date = today - timedelta(days=30)
    elif date_range == 'last_month':
        # Get first day of last month
        start_date = today.replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    elif date_range == 'custom':
        # In a real implementation, you'd get these from request args
        start_date = request.args.get('start_date', today)
        end_date = request.args.get('end_date', today)
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:  # 'this_month'
        start_date = today.replace(day=1)
        end_date = today

    if date_range != 'last_month' and date_range != 'custom':
        end_date = today

    return start_date, end_date