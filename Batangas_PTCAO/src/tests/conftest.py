import pytest
from flask import Flask
from Batangas_PTCAO.src.extension import db
from Batangas_PTCAO.src.config import Config
from flask_jwt_extended import JWTManager


@pytest.fixture(scope='session')
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        yield db
        db.session.rollback()