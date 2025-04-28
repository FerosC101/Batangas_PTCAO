import os
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.config import Config
from datetime import timedelta

from Batangas_PTCAO.src.routes.auth import init_auth_routes
from Batangas_PTCAO.src.routes.MTO import init_mto_routes
from Batangas_PTCAO.src.routes.MTO_Property import init_property_routes, properties_bp
from Batangas_PTCAO.src.routes.MTO_Dashboard import init_dashboard_routes
from Batangas_PTCAO.src.routes.MTO_Events import init_events_routes
from Batangas_PTCAO.src.routes.MTO_Analytics import init_analytics_routes
from Batangas_PTCAO.src.routes.MTO_Visitors import init_visitors_routes

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    app.config.from_object(Config)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False  # HTTPS only
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Enable CSRF protection
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static/uploads/properties')

    # Initialize extensions
    jwt = JWTManager(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Initialize routes
    init_auth_routes(app)
    init_mto_routes(app)
    init_property_routes(app)
    init_dashboard_routes(app)
    init_events_routes(app)
    init_analytics_routes(app)
    init_visitors_routes()

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
