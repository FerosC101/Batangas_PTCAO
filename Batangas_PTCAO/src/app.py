import os
from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.config import Config
from datetime import timedelta

# Correct import paths
from Batangas_PTCAO.src.routes.auth import init_auth_routes
from Batangas_PTCAO.src.routes.MTO import init_mto_routes  # Ensure correct case


def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    app.config.from_object(Config)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')

    # Initialize extensions
    jwt = JWTManager(app)
    db.init_app(app)

    # Create a proper application context
    with app.app_context():
        from Batangas_PTCAO.src.model import User  # Ensure all models are imported before creating tables
        db.create_all()

    # Initialize routes
    init_auth_routes(app)
    init_mto_routes(app)

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


# Application instantiation
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
