from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import (
    User,
    VisitorStatistics,
    Property
)

visitors_bp = Blueprint('visitors', __name__)


def init_visitors_routes(app):
    app.register_blueprint(visitors_bp)


@visitors_bp.route('/mto/visitors')
@jwt_required()
def mto_visitors():
    """Render the MTO Visitors page"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    return render_template(
        'MTO_Visitors.html',
        municipality=user.municipality
    )


@visitors_bp.route('/api/visitors', methods=['GET'])
@jwt_required()
def get_visitors():
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
        query = VisitorStatistics.query.join(
            Property,
            Property.property_id == VisitorStatistics.property_id
        ).filter(
            Property.municipality == user.municipality
        )

        # Apply date filter
        query = query.filter(
            VisitorStatistics.report_date.between(start_date, end_date)
        )

        # Apply barangay filter
        if barangay != 'all':
            query = query.filter(
                Property.barangay == barangay
            )

        # Apply visitor type filter
        if visitor_type != 'all':
            query = query.filter(
                VisitorStatistics.visitor_type == visitor_type
            )

        # Apply stay type filter
        if stay_type != 'all':
            query = query.filter(
                VisitorStatistics.stay_type == stay_type
            )

        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Property.property_name.ilike(f'%{search}%'),
                    Property.barangay.ilike(f'%{search}%')
                )
            )

        # Paginate results
        paginated = query.order_by(
            VisitorStatistics.report_date.desc()
        ).paginate(page=page, per_page=per_page)

        # Format results
        visitors = []
        for stat in paginated.items:
            visitors.append({
                'id': f"VS-{stat.stat_id}",
                'date': stat.report_date.strftime('%b %d, %Y'),
                'visitor_type': stat.visitor_type,
                'barangay': stat.property.barangay,
                'stay_type': stat.stay_type,
                'adults': stat.adults,
                'children': stat.children,
                'revenue': float(stat.revenue) if stat.revenue else 0.0,
                'property_name': stat.property.property_name
            })

        return jsonify({
            'success': True,
            'data': {
                'visitors': visitors,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page
            },
            'filters': {
                'date_range': date_range,
                'barangay': barangay,
                'visitor_type': visitor_type,
                'stay_type': stay_type
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@visitors_bp.route('/api/visitors/barangays', methods=['GET'])
@jwt_required()
def get_barangays():
    """Get list of barangays for the MTO's municipality"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        barangays = db.session.query(
            Property.barangay
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