from flask import Blueprint, render_template

tourist_bp = Blueprint('tourist', __name__)

def init_tourist_routes(app):
    app.register_blueprint(tourist_bp)

@tourist_bp.route('/home')
def tourist_home():
    return render_template('TOURIST_Home.html')