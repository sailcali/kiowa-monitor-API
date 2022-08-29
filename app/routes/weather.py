from flask import Blueprint, render_template


weather_bp = Blueprint('weather_bp', __name__, url_prefix='/weather')

@weather_bp.route("/", methods=["GET"])
def render_weather_page():
    return render_template('weather_forecast.html')