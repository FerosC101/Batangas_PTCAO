from flask import Blueprint, render_template, jsonify, request
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.model import Event
from datetime import datetime, date
from sqlalchemy import or_, and_


def init_tourist_events_routes(app):
    @app.route('/events')
    def events_page():
        return render_template('TOURIST_Event.html')

    @app.route('/api/events')
    def get_events():
        try:
            category = request.args.get('category', 'all')
            search = request.args.get('search', '').strip()
            municipality = request.args.get('municipality', '')
            upcoming_only = request.args.get('upcoming_only', 'false').lower() == 'true'
            featured_only = request.args.get('featured_only', 'false').lower() == 'true'

            query = Event.query

            if category and category != 'all':
                query = query.filter(Event.category.ilike(f'%{category}%'))

            if municipality:
                query = query.filter(Event.municipality.ilike(f'%{municipality}%'))

            if upcoming_only:
                today = date.today()
                query = query.filter(Event.end_date >= today)

            if search:
                search_filter = or_(
                    Event.event_title.ilike(f'%{search}%'),
                    Event.description.ilike(f'%{search}%'),
                    Event.location.ilike(f'%{search}%'),
                    Event.municipality.ilike(f'%{search}%'),
                    Event.category.ilike(f'%{search}%')
                )
                query = query.filter(search_filter)

            query = query.order_by(Event.start_date.asc())

            events = query.all()

            events_data = []
            for event in events:
                today = date.today()
                is_ongoing = event.start_date <= today <= event.end_date
                is_upcoming = event.start_date > today
                is_past = event.end_date < today

                start_date_str = event.start_date.strftime('%B %d, %Y')
                end_date_str = event.end_date.strftime('%B %d, %Y')

                if event.start_date == event.end_date:
                    date_display = start_date_str
                else:
                    if event.start_date.year == event.end_date.year and event.start_date.month == event.end_date.month:
                        date_display = f"{event.start_date.strftime('%B %d')}-{event.end_date.strftime('%d, %Y')}"
                    else:
                        date_display = f"{start_date_str} - {end_date_str}"

                status = 'past'
                if is_ongoing:
                    status = 'ongoing'
                elif is_upcoming:
                    status = 'upcoming'

                image_url = event.event_image or '/static/images/default-event.jpg'

                is_featured = (category == 'festival' and 'festival' in (event.category or '').lower()) or featured_only

                event_data = {
                    'event_id': event.event_id,
                    'title': event.event_title,
                    'description': event.description or 'No description available',
                    'start_date': event.start_date.isoformat(),
                    'end_date': event.end_date.isoformat(),
                    'date_display': date_display,
                    'municipality': event.municipality or 'Batangas',
                    'location': event.location or 'To be announced',
                    'category': event.category or 'general',
                    'image_url': image_url,
                    'status': status,
                    'is_featured': is_featured,
                    'is_ongoing': is_ongoing,
                    'is_upcoming': is_upcoming,
                    'is_past': is_past
                }

                events_data.append(event_data)

            if featured_only:
                events_data = [event for event in events_data if event['is_featured']]

            return jsonify({
                'success': True,
                'events': events_data,
                'total_count': len(events_data),
                'filters_applied': {
                    'category': category,
                    'search': search,
                    'municipality': municipality,
                    'upcoming_only': upcoming_only,
                    'featured_only': featured_only
                }
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'events': []
            }), 500

    @app.route('/api/events/<int:event_id>')
    def get_event_detail(event_id):
        """Get detailed information about a specific event"""
        try:
            event = Event.query.get_or_404(event_id)

            today = date.today()
            is_ongoing = event.start_date <= today <= event.end_date
            is_upcoming = event.start_date > today
            is_past = event.end_date < today

            status = 'past'
            if is_ongoing:
                status = 'ongoing'
            elif is_upcoming:
                status = 'upcoming'

            start_date_str = event.start_date.strftime('%B %d, %Y')
            end_date_str = event.end_date.strftime('%B %d, %Y')

            if event.start_date == event.end_date:
                date_display = start_date_str
            else:
                date_display = f"{start_date_str} - {end_date_str}"

            event_data = {
                'event_id': event.event_id,
                'title': event.event_title,
                'description': event.description or 'No description available',
                'start_date': event.start_date.isoformat(),
                'end_date': event.end_date.isoformat(),
                'date_display': date_display,
                'municipality': event.municipality or 'Batangas',
                'location': event.location or 'To be announced',
                'category': event.category or 'general',
                'image_url': event.event_image or '/static/images/default-event.jpg',
                'status': status,
                'is_ongoing': is_ongoing,
                'is_upcoming': is_upcoming,
                'is_past': is_past
            }

            return jsonify({
                'success': True,
                'event': event_data
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/events/categories')
    def get_event_categories():
        try:
            categories = db.session.query(Event.category).distinct().filter(Event.category.isnot(None)).all()
            category_list = [cat[0] for cat in categories if cat[0]]

            return jsonify({
                'success': True,
                'categories': category_list
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'categories': []
            }), 500

    @app.route('/api/events/municipalities')
    def get_event_municipalities():
        try:
            municipalities = db.session.query(Event.municipality).distinct().filter(
                Event.municipality.isnot(None)).all()
            municipality_list = [muni[0] for muni in municipalities if muni[0]]

            return jsonify({
                'success': True,
                'municipalities': municipality_list
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'municipalities': []
            }), 500

    @app.route('/api/events/featured')
    def get_featured_event():
        """Get a featured event for the hero section"""
        try:
            # Get the most upcoming festival event or the latest event
            featured_event = Event.query.filter(
                and_(
                    Event.end_date >= date.today(),
                    Event.category.ilike('%festival%')
                )
            ).order_by(Event.start_date.asc()).first()

            # If no festival event, get any upcoming event
            if not featured_event:
                featured_event = Event.query.filter(
                    Event.end_date >= date.today()
                ).order_by(Event.start_date.asc()).first()

            # If no upcoming events, get the latest event
            if not featured_event:
                featured_event = Event.query.order_by(Event.start_date.desc()).first()

            if not featured_event:
                return jsonify({
                    'success': False,
                    'message': 'No events found'
                }), 404

            # Format dates
            start_date_str = featured_event.start_date.strftime('%B %d, %Y')
            end_date_str = featured_event.end_date.strftime('%B %d, %Y')

            if featured_event.start_date == featured_event.end_date:
                date_display = start_date_str
            else:
                date_display = f"{start_date_str} - {end_date_str}"

            event_data = {
                'event_id': featured_event.event_id,
                'title': featured_event.event_title,
                'description': featured_event.description or 'Join this exciting event in Batangas!',
                'date_display': date_display,
                'municipality': featured_event.municipality or 'Batangas',
                'location': featured_event.location or 'Various Locations',
                'category': featured_event.category or 'festival',
                'image_url': featured_event.event_image or 'https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
            }

            return jsonify({
                'success': True,
                'featured_event': event_data
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500