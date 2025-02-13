import os
from flask import Flask
from flask_jwt_extended import JWTManager
from extension import db
from config import Config
from datetime import timedelta

from routes.auth import init_auth_routes
from routes.business import init_business_routes
from routes.services import init_services_routes
from routes.main import init_main_routes

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')

    # Initialize extensions
    jwt = JWTManager(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Initialize routes
    init_auth_routes(app)
    init_business_routes(app)
    init_services_routes(app)
    init_main_routes(app)

    return app

# Application instantiation
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)