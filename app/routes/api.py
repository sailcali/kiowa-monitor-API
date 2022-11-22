
from flask import Blueprint, jsonify, make_response, request, redirect, url_for
import sqlalchemy
from app import db
from app.models import EnphaseProduction, LightingStatus, VenstarTemp, Food, Bedtime
from datetime import datetime, date
import requests
from dotenv import load_dotenv
import os
from smartthings import SMARTTHINGS_DEVICES
import configparser

load_dotenv()
SMARTTHINGS_TOKEN = os.environ.get("SMARTTHINGS_TOKEN")
IP = os.environ.get("VENSTAR_IP")
PI_ZERO_IP = os.environ.get("PI_ZERO_IP")
DIRECTORY = os.environ.get("DIRECTORY")
VENSTAR_INFO_URL = 'http://' + IP + '/query/info'
VENSTAR_SENSOR_URL = 'http://' + IP + '/query/sensors'
VENSTAR_RUNTIMES_URL = 'http://' + IP + '/query/runtimes'
VENSTAR_CONTROL_URL = 'http://' + IP + '/control'
GARAGE_PI_STATUS_URL = 'http://' + PI_ZERO_IP + '/get-status'
SMARTTHINGS_DEVICES_URL = 'https://api.smartthings.com/v1/devices'
GARAGE_PICO_URL = 'http://192.168.86.33'
WEATHER_APP_ID = os.environ.get("WEATHER_APP_ID")

api_bp = Blueprint('api_bp', __name__, url_prefix='/api')

@api_bp.route("", methods=['GET'])
def return_api_docs():
    return jsonify({'/temps': 'Returns the temperature data from today as JSON', 
                    '/current_temps': 'Returns current temperatures as JSON',
                    '/garage-status': 'Returns garage PICO status (temperature and lighting) as JSON',
                    '/record-landscape-change': "Records landscape lighting changes in database (requires boolean 'state_change')",
                    '/food': 'Records new food item in database for food tracker',
                    '/smartthings/status': 'Returns SmartThings devices states as JSON',
                    '/solar-production/lifetime': 'Returns all known production data from database as JSON.',
                    '/solar-production/period-sum': "Returns solar production data as a sum during a specified period. Requires 'start_date' and 'end_date' as YYYY-MM-DD.",
                    '/solar-production/period/data': "Returns all known production data over a period from database as JSON. Requires 'start_date' and 'end_date' as YYYY-MM-DD."})


@api_bp.route("/temps", methods=["GET"])
def return_temps_for_api():
    """API call for today's temps"""
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    for i in range(len(temps)):
        if i > 0:
            last_heat_time = temps[i-1].heat_runtime
            last_cool_time = temps[i-1].cool_runtime
        else:
            last_heat_time = 0
            last_cool_time = 0
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime - last_heat_time,
                     'cool_time': temps[i].cool_runtime - last_cool_time})
    response = make_response(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@api_bp.route("/current_temps", methods=["GET"])
def return_current_temps_for_api():
    """Returns a JSON of the current temperatures onboard the server"""
    temps = VenstarTemp.query.order_by(VenstarTemp.time.desc()).first()
    living_room = temps.pi_temp
    venstar_response = requests.get(VENSTAR_INFO_URL)
    venstar_info = venstar_response.json()
    hum = temps.humidity
    return jsonify({'thermostat_temp': venstar_info['spacetemp'], 'living_room_temp': living_room, 'humidity': hum, 'remote_temp': temps.remote_temp}), 200

@api_bp.route('/garage-status', methods=['GET'])
def get_garage_status():
    response = requests.get(GARAGE_PICO_URL)
    if response.status_code != 200:
        return make_response({'Status': 'No connection to Garage PICO'}, 401)
    response = response.json()
    # last_entry = LightingStatus.query.order_by(LightingStatus.time.desc()).first()
    # config = configparser.ConfigParser()
    # config.read_file(open(f'{DIRECTORY}/delay_time.conf'))
    # delay = config.get('DelayDatetime', 'value')
    return make_response({'temperature': response['temp'], 
    'humidity': response['humidity'], 'lighting_state': response['current_status']['landscape'],}, 201)

@api_bp.route('/record-landscape-change', methods=['POST'])
def record_landscape_change():
    """Makes new entry in the database to update the lighting status
    Note: Requires a state_change boolean"""
    body = request.get_json()
    strtime = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')
    last_entry = LightingStatus.query.order_by(LightingStatus.time.desc()).first()
    new_entry = LightingStatus(time=datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S'), device='landscape', setting=body['state_change'])
    if not body['state_change']:
        time_on = new_entry.time - last_entry.time
        new_entry.time_on = time_on.total_seconds()/60
    db.session.add(new_entry)
    db.session.commit()
    return jsonify([]), 201

@api_bp.route("/food", methods=["POST"])
def food_tables():
    new_food = Food(food=request.form.get('new_food'))
    db.session.add(new_food)
    db.session.commit()
    return redirect(url_for('food_bp.get_food_schedule'))

@api_bp.route('/smartthings/status', methods=['GET', 'POST'])
def interact_smartthings():
    headers = {"Authorization": "Bearer " + SMARTTHINGS_TOKEN}
    if request.method == 'GET':
        states = {"devices": []}
        for device, id in SMARTTHINGS_DEVICES.items():
            status_response = requests.get(f'{SMARTTHINGS_DEVICES_URL}/{id}/status', headers=headers)
            if status_response.status_code == 400:
                states['devices'].append({"name": device, 'state': 'OFFLINE'})
                continue

            health_response = requests.get(f'{SMARTTHINGS_DEVICES_URL}/{id}/health', headers=headers)
            device_state = status_response.json()
            device_health = health_response.json()
            if device_health['state'] == 'OFFLINE':
                states['devices'].append({"name": device, 'state': 'OFFLINE'})
            else:
                states['devices'].append({"name": device, 'state': device_state['components']['main']['switch']['switch']['value']})
        return jsonify(states)
    if request.method == 'POST':
        data = request.get_json()
        new_state = ''
        device = ''
        if data['light'] == 'pineappleSwitch':
            device = 'Pineapple'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'diningroomSwitch':
            device = 'Dining Room'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'garageSwitch':
            device = 'Garage'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'bedroomSwitch':
            device = 'Bedroom'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'lanternSwitch':
            device = 'Lantern'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'stringlightsSwitch':
            device = 'String Lights'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'frontdoorSwitch':
            device = 'Front Door'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        params = {'commands': [{"component": 'main',
                                "capability": 'switch',
                                "command": new_state}]}
        requests.post(f"{SMARTTHINGS_DEVICES_URL}/{SMARTTHINGS_DEVICES[device]}/commands", headers=headers, json=params)
        
        return jsonify([])

@api_bp.route('/bedtime', methods=['GET'])
def set_bedtime():
    headers = {"Authorization": "Bearer " + SMARTTHINGS_TOKEN}
    params = {'commands': [{"component": 'main',
                                "capability": 'switch',
                                "command": 'off'}]}
    requests.post(f"{SMARTTHINGS_DEVICES_URL}/{SMARTTHINGS_DEVICES['Bedroom']}/commands", headers=headers, json=params)
    requests.post(f"{SMARTTHINGS_DEVICES_URL}/{SMARTTHINGS_DEVICES['Pineapple']}/commands", headers=headers, json=params)
    new_bedtime = Bedtime(time=datetime.now())
    db.session.add(new_bedtime)
    db.session.commit()
    return redirect(url_for('venstar_bp.kiowa_dashboard'))

@api_bp.route('/solar-production/lifetime', methods=['GET'])
def get_all_solar_production():
    all_production = db.session.query(sqlalchemy.func.sum(EnphaseProduction.production)).first()
    return make_response({"total_production": all_production[0]}, 200)

@api_bp.route('/solar-production/period-sum', methods=['GET'])
def get_period_solar_production_sum():
    request_body = request.get_json()
    all_production = db.session.query(sqlalchemy.func.sum(EnphaseProduction.production)) \
        .filter(sqlalchemy.and_(sqlalchemy.func.date(EnphaseProduction.time) >= request_body['start_date']), \
        sqlalchemy.func.date(EnphaseProduction.time) <= request_body['end_date']).first()
    return make_response({"period_production": all_production[0], "start_date": request_body['start_date'], "end_date": request_body['end_date']}, 200)

@api_bp.route('/solar-production/period-data', methods=['GET'])
def get_period_solar_production_data():
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