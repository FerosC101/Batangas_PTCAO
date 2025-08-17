from flask import Blueprint, render_template

tourist_contact_bp = Blueprint('tourist_contact_bp', __name__, url_prefix='/tourist')

def init_tourist_contact_routes(app):
    app.register_blueprint(tourist_contact_bp)

@tourist_contact_bp.route('/contact')
def tourist_contact():
    return render_template('TOURIST_Contact.html')

@tourist_contact_bp.route('/home')
def tourist_home():
    return render_template('TOURIST_Home.html')

@tourist_contact_bp.route('/destination')
def tourist_destination():
    return render_template('TOURIST_Destination.html')

@tourist_contact_bp.route('/map')
def tourist_map():
    return render_template('TOURIST_Map.html')

@tourist_contact_bp.route('/events')
def tourist_events():
    return render_template('TOPURIST_Event.html')
