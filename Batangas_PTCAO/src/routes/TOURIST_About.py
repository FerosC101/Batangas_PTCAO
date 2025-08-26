from flask import Blueprint, render_template
from app import app
tourist_about_bp = Blueprint('tourist_about', __name__, url_prefix='/tourist')


def init_tourist_about_routes(app):
    app.register_blueprint(tourist_about_bp)


@tourist_about_bp.route('/about')
def tourist_about():

    try:

        return render_template('TOURIST_About.html')

    except Exception as e:
        # Log error and render template anyway
        app.logger.error(f"Error loading about page: {str(e)}")
        return render_template('TOURIST_About.html'), 500

@tourist_about_bp.route('/home')
def tourist_home():
    return render_template("TOURIST_Home.html")

@tourist_about_bp.route('/destinations')
def tourist_destinations():
    return render_template('TOURIST_Destination.html')

@tourist_about_bp.route('/map')
def tourist_map():
    return render_template('TOURIST_Map.html')

@tourist_about_bp.route('/events')
def tourist_events():
    return render_template('TOURIST_Event.html')
