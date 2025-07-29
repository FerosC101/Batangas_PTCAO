import os
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from sqlalchemy import values

from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.config import Config
from datetime import timedelta

from Batangas_PTCAO.src.routes.MTO_Announcement import init_mto_announcement_routes
from Batangas_PTCAO.src.routes.PTCAO_Dashboard import init_ptcao_dashboard_routes
from Batangas_PTCAO.src.routes.PTCAO_Destinations import init_ptcao_destinations_routes
from Batangas_PTCAO.src.routes.PTCAO_Property import init_ptcao_property_routes
# Import route initializers
from Batangas_PTCAO.src.routes.auth import init_auth_routes
from Batangas_PTCAO.src.routes.MTO import init_mto_routes
from Batangas_PTCAO.src.routes.MTO_Property import init_property_routes
from Batangas_PTCAO.src.routes.MTO_Dashboard import init_dashboard_routes
from Batangas_PTCAO.src.routes.MTO_Events import init_events_routes
from Batangas_PTCAO.src.routes.MTO_Analytics import init_analytics_routes
from Batangas_PTCAO.src.routes.MTO_VisitorsRecords import init_visitor_records_routes
from Batangas_PTCAO.src.routes.MTO_Destinations import init_destinations_routes
from Batangas_PTCAO.src.routes.MTO_Reports import init_reports_routes
from Batangas_PTCAO.src.routes.ADMIN_users import init_admin_users_routes  # New import
from Batangas_PTCAO.src.routes.ADMIN_dashboard import init_admin_dashboard_routes
from Batangas_PTCAO.src.routes.ADMIN_reports import init_admin_reports_routes

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    @app.template_filter('number_format')
    def number_format(value):
        try:
            return "{:,}".format(int(value))
        except (ValueError, TypeError):
            return values

    # Configurations
    app.config.from_object(Config)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static/uploads/properties')

    # Initialize extensions
    jwt = JWTManager(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Initialize all routes
    init_auth_routes(app)
    init_mto_routes(app)
    init_property_routes(app)
    init_dashboard_routes(app)
    init_events_routes(app)
    init_analytics_routes(app)
    init_visitor_records_routes(app)
    init_destinations_routes(app)
    init_reports_routes(app)
    init_mto_announcement_routes(app)
    init_admin_users_routes(app)
    init_admin_dashboard_routes(app)
    init_admin_reports_routes(app)
    init_ptcao_dashboard_routes(app)
    init_ptcao_destinations_routes(app)
    init_ptcao_property_routes(app)

    # Static file serving route
    @app.route('/static/<path:filename>')
    def serve_static_file(filename):
        if allowed_file(filename):
            return send_from_directory(os.path.join(app.root_path, 'static'), filename)
        return 'File type not allowed', 400

    return app


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)