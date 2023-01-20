
from flask import Blueprint, jsonify, make_response, request, redirect, url_for
import sqlalchemy
from app import db
from app.models import EnphaseProduction, LightingStatus, Food
from datetime import datetime
import requests
from dotenv import load_dotenv
import os
from discordwebhook import Discord

load_dotenv()

GARAGE_PICO_URL = os.environ.get("GARAGE_PI_IP")
WEATHER_APP_ID = os.environ.get("WEATHER_APP_ID")
DISCORD_URL = os.environ.get("DISCORD_GENERAL_URL")
DISCORD = Discord(url=DISCORD_URL)

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

@api_bp.route("", methods=['GET'])
def return_api_docs():
    return jsonify({'venstar-status': 'Get and Set the current status of venstar ecosystem',
                    '/temps': 'Returns the temperature data from today as JSON', 
                    '/temps/<requested_date>': 'Returns the temperature data from a date as JSON',
                    '/current_temps': 'Returns current temperatures as JSON',
                    '/venstar-usage': 'Returns the temps and venstar usage data from today',
                    '/venstar-usage/<requested_date>': 'Returns the temps and venstar usage data from a date',
                    '/garage-status': 'Returns garage PICO status (temperature and lighting) as JSON',
                    '/record-landscape-change': "Records landscape lighting changes in database (requires boolean 'state_change')",
                    '/food': 'Records new food item in database for food tracker',
                    '/lighting/status': 'Returns SmartThings and Garage devices states as JSON',
                    '/bedtime': 'Get and Set bedtime lights and time',
                    '/solar-production/lifetime': 'Returns all known production data from database as JSON.',
                    '/solar-production/period-sum': "Returns solar production data as a sum during a specified period. Requires 'start_date' and 'end_date' as YYYY-MM-DD.",
                    '/solar-production/period/data': "Returns all known production data over a period from database as JSON. Requires 'start_date' and 'end_date' as YYYY-MM-DD.",
                    '/weather/outlook': 'Returns JSON of weather data for 5 days'})

@api_bp.route('/garage-status', methods=['GET'])
def get_garage_status():
    """Return JSON of garage temp, humidity, and landscape status"""
    response = requests.get(GARAGE_PICO_URL)
    if response.status_code != 200:
        return make_response({'Status': 'No connection to Garage PICO'}, 401)
    response = response.json()
    return make_response({'temperature': response['temp'], 
    'humidity': response['humidity'], 'lighting_state': response['current_status']['landscape'],}, 200)

@api_bp.route('/record-landscape-change', methods=['POST'])
def record_landscape_change():
    """Makes new entry in the database to update the lighting status
    Note: Requires a state_change boolean"""
    body = request.get_json()
    # Current time in string format
    strtime = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')
    # Get the last entry
    last_entry = LightingStatus.query.order_by(LightingStatus.time.desc()).first()
    # Create the new entry
    new_entry = LightingStatus(time=datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S'), device='landscape', setting=body['state_change'])
    
    # if the light is going off
    if not body['state_change']:
        # Calculate time that the light was on
        time_on = new_entry.time - last_entry.time
        # Insert the that time spent on into the corresponding field
        new_entry.time_on = time_on.total_seconds()/60
    
    # Commit the new entry
    db.session.add(new_entry)
    db.session.commit()
    return jsonify([]), 201

@api_bp.route("/food", methods=["POST"])
def food_tables():
    """Post a new commonly used food item"""
    new_food = Food(food=request.form.get('new_food'))
    db.session.add(new_food)
    db.session.commit()
    return redirect(url_for('food_bp.get_food_schedule'))

@api_bp.route('/solar-production/lifetime', methods=['GET'])
def get_all_solar_production():
    """Returns the total lifetime production value (sum) of the enphase system"""
    all_production = db.session.query(sqlalchemy.func.sum(EnphaseProduction.production)).first()
    return make_response({"total_production": all_production[0]}, 200)

@api_bp.route('/solar-production/period-sum', methods=['GET'])
def get_period_solar_production_sum():
    """Returns the production sum for a period of time sent in the request body"""
    request_body = request.get_json()
    all_production = db.session.query(sqlalchemy.func.sum(EnphaseProduction.production)) \
        .filter(sqlalchemy.and_(sqlalchemy.func.date(EnphaseProduction.time) >= request_body['start_date']), \
        sqlalchemy.func.date(EnphaseProduction.time) <= request_body['end_date']).first()
    return make_response({"period_production": all_production[0], "start_date": request_body['start_date'], "end_date": request_body['end_date']}, 200)

@api_bp.route('/solar-production/period-data', methods=['GET'])
def get_period_solar_production_data():
    """Returns all production data for a period of time sent in the request body"""
    request_body = request.get_json()
    all_production = EnphaseProduction.query \
        .filter(sqlalchemy.and_(sqlalchemy.func.date(EnphaseProduction.time) >= request_body['start_date']), \
        sqlalchemy.func.date(EnphaseProduction.time) <= request_body['end_date']).all()
    response_data = []
    for row in all_production:
        response_data.append({'time': row.time, 'production': row.production})
    return make_response({'Results': response_data}, 200)

@api_bp.route('/weather/outlook', methods=["GET"])
def get_weather_outlook():
    params = {"lat": 32.782, "lon": -117.04, "units": "imperial", "appid": WEATHER_APP_ID}
    response = requests.get("https://api.openweathermap.org/data/2.5/forecast", params=params)
    j = response.json()
    return make_response(j, 200)