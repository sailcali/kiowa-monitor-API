from flask import Blueprint, jsonify, render_template, make_response
import requests
import os

WEATHER_APP_ID = os.environ.get("WEATHER_APP_ID")

weather_bp = Blueprint('weather_bp', __name__, url_prefix='/weather')

@weather_bp.route("/", methods=["GET"])
def render_weather_page():
    return render_template('weather_forecast.html')

@weather_bp.route("/current", methods={"GET"})
def return_current_local_weather():
    params = {"lat": 32.782, "lon": -117.04, "units": "imperial", "appid": WEATHER_APP_ID}
    response = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    j = response.json()
    return j

