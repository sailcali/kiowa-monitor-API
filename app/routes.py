import re
from flask import Blueprint, jsonify, make_response, request, abort, render_template, redirect, url_for
from flask.signals import request_finished
import sqlalchemy
from app import db
from app.models import EnphaseProduction, LightingStatus, VenstarTemp, FoodPlanner, MealListing, Food
from datetime import datetime, timedelta, date
import requests
from dotenv import load_dotenv
import os
from smartthings import SMARTTHINGS_DEVICES
from app.landscape import landscape
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

temps_bp = Blueprint('temps_bp', __name__, url_prefix='/temps')
venstar_bp = Blueprint('venstar_bp', __name__, url_prefix='/venstar')
usage_bp = Blueprint('usage_bp', __name__, url_prefix='/usage')
login_bp = Blueprint('login_bp', __name__, url_prefix='/')
landscape_bp = Blueprint('landscape_bp', __name__, url_prefix='/landscape')
api_bp = Blueprint('api_bp', __name__, url_prefix='/api')
food_bp = Blueprint('food_bp', __name__, url_prefix='/food')

@login_bp.route("", methods=['GET'])
def login():
    return redirect(url_for('venstar_bp.kiowa_dashboard'))

@api_bp.route("", methods=['GET'])
def return_api_docs():
    return jsonify({'temps': 'Returns temperatures from today', 
                    '/current_temps': 'Returns current temperatures monitored by server'})

@venstar_bp.route("", methods=['GET'])
def kiowa_dashboard():
    """Main dashboard for Kiowa. Gathers data from the VENSTAR thermostat, database for humidity and lighting and renders the page"""
    authorized_ip = os.environ.get("IP_ALLOWED")
    if request.remote_addr not in authorized_ip:
        return make_response(f'Sorry, {request.remote_addr} your computer is not permitted to view this resource.', 401)

    # Gather all necessary data
    info_response = requests.get(VENSTAR_INFO_URL)
    info = info_response.json()
    sensor_response = requests.get(VENSTAR_SENSOR_URL)
    sensors = sensor_response.json()
    runtime_response = requests.get(VENSTAR_RUNTIMES_URL)
    runtimes = runtime_response.json()
    recent_data = VenstarTemp.query.order_by(VenstarTemp.time.desc()).first()
    landscape_state = LightingStatus.query.order_by(LightingStatus.time.desc()).first()

    # Gather the outdoor temp
    remote_temp = 'N/A' # set to N/A in case its not found!
    for sensor in sensors['sensors']:
        if sensor['name'] == 'Remote':
            remote_temp = sensor['temp']
    # Change lighting bool to ON or OFF
    lighting_bool = {1: 'ON', 0: 'OFF'}
    # Change mode data (0,1,2,3) to understandable strings
    venstar_modes = {0: 'OFF', 1: 'HEAT', 2: 'COOL', 3: 'AUTO'}
    # Change fan state to ON or AUTO
    fan_states = {0: 'AUTO', 1: 'ON'}

    data = {'current_temp': int(info['spacetemp']), 'outside_temp': int(remote_temp), 
            'heat_temp': int(info['heattemp']), 'cool_temp': int(info['cooltemp']),
            'mode': venstar_modes[info['mode']], 'fan_setting': fan_states[info['fan']], 'humidity': recent_data.humidity, 
            'living_room_temp': int(recent_data.pi_temp), 'heat_time': runtimes['runtimes'][-1]['heat1'], 
            'cool_time': runtimes['runtimes'][-1]['cool1'], 'landscape_state': lighting_bool[landscape_state.setting], 
            'last_landscape_change': landscape_state.time}
    
    return render_template('dashboard.html', data=data)

@venstar_bp.route("", methods=['POST'])
def venstar_changes():
    """Middle-man for changing VENSTAR status. POST request made from dashboard, 
    makes post request to VENSTAR control, and re-renders dashboard"""
    params = {
        'mode': request.form.get('mode'),
        'fan': request.form.get('fan'),
        'heattemp': request.form.get('heat_temp'),
        'cooltemp': request.form.get('cool_temp')
    }
    requests.post(VENSTAR_CONTROL_URL, params=params)
    return redirect(url_for('venstar_bp.kiowa_dashboard'))

@temps_bp.route("/<requested_date>", methods=["GET"])
def display_temps_by_date(requested_date):
    """Renders a table of temperatures from a given date"""
    try:
        start_date = datetime.strptime(requested_date, '%Y-%m-%d')
    except ValueError:
        try:
            start_date = datetime.strptime(requested_date, '%Y-%b-%d')
        except ValueError:
            abort(404)
    end_time = start_date + timedelta(days=1)
    temps = VenstarTemp.query.filter(VenstarTemp.time>start_date, VenstarTemp.time<end_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    if start_date < datetime.strptime('2021-12-05', '%Y-%m-%d'):
        for i in range(len(temps)):
        
            data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                        'local_temp': temps[i].local_temp,
                        'pi_temp': temps[i].pi_temp,
                        'remote_temp': temps[i].remote_temp,
                        'humidity': temps[i].humidity})
    else:
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
    return render_template('index.html', data=data)

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
    return jsonify({'thermostat_temp': venstar_info['spacetemp'], 'living_room_temp': living_room, 'humidity': hum}), 200

@temps_bp.route("/today", methods=["GET"])
def display_temps_from_today():
    """Renders a table of today's temperature data"""
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    for i in range(len(temps)):
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime,
                     'cool_time': temps[i].cool_runtime})
    return render_template('index.html', data=data)

@usage_bp.route("/today", methods=["GET"])
def display_usage_from_today():
    """Renders a table of today's usage data"""
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    for i in range(len(temps)):
        if i != len(temps)-1:
            last_heat_time = temps[i+1].heat_runtime
            last_cool_time = temps[i+1].cool_runtime
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
    return render_template('hvac-index.html', data=data)

@api_bp.route('/garage-status', methods=['GET'])
def get_garage_status():
    response = requests.get(GARAGE_PICO_URL)
    response = response.json()
    # last_entry = LightingStatus.query.order_by(LightingStatus.time.desc()).first()
    config = configparser.ConfigParser()
    config.read_file(open(f'{DIRECTORY}/delay_time.conf'))
    delay = config.get('DelayDatetime', 'value')
    return make_response({'temperature': response['temp'], 'current_delay': delay, 
    'humidity': response['humidity'], 'lighting_state': response['current_status']['landscape'],}, 201)

@api_bp.route('/record-landscape-change', methods=['POST'])
def record_landscape_change():
    body = request.get_json()
    strtime = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')
    last_entry = LightingStatus.query.order_by(LightingStatus.time.desc()).first()
    new_entry = LightingStatus(time=datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S'), device='landscape', setting=body['state_change'])
    if not body['state_change']:
        time_on = new_entry.time - last_entry.time
        new_entry.time_on = time_on.total_seconds()/60
    db.session.add(new_entry)
    db.session.commit()


@landscape_bp.route('/change-state', methods=['POST'])
def change_landscape_state():
    body = request.get_json()
    delay_time = datetime.today() + timedelta(minutes=int(body["delay_time"]))
    new = landscape.change_landscape(body['state'], delay_time)
    return make_response({'new_status': new, 'new_delay': delay_time}, 201)

@api_bp.route("/food", methods=["POST"])
def food_tables():
    new_food = Food(food=request.form.get('new_food'))
    db.session.add(new_food)
    db.session.commit()
    return redirect(url_for('food_bp.get_food_schedule'))
    
@food_bp.route("/schedule", methods=['GET', 'POST'])
def get_food_schedule():
    if request.method == "GET": 
        food_list = Food.query.all()
        meal_names = []
        for food in food_list:
            meal_names.append(food.food)
        schedule = FoodPlanner.query.filter(FoodPlanner.date>=date.today()).all()
        meals = {}
        for meal in schedule:
            meal_date = datetime.strftime(meal.date, '%Y-%m-%d')
            try:
                meals[meal_date]
            except KeyError:
                meals[meal_date] = []
            meals[meal_date].append({'meal': meal.meal_list.meal, "food": meal.food.food, "source": meal.source})
        return render_template('weekly_food.html', data=meals, meals=meal_names)
    elif request.method == "POST":
        meal_of_day = MealListing.query.filter(MealListing.meal == request.form.get('meal')).first()
        food = Food.query.filter(Food.food == request.form.get('food_items')).first()
        current_meal = FoodPlanner.query.filter(FoodPlanner.date == request.form.get('date'), FoodPlanner.meal_id == meal_of_day.id).first()
        new_meal = FoodPlanner(date=request.form.get('date'),
                                    meal_id=meal_of_day.id,
                                    food_id=food.id,
                                    source=request.form.get('ingredients'))
        
        if current_meal:
            db.session.delete(current_meal)

        db.session.add(new_meal)
        db.session.commit()
        return redirect(url_for('food_bp.get_food_schedule'))

@api_bp.route('/smartthings/status', methods=['GET', 'POST'])
def interact_smartthings():
    headers = {"Authorization": "Bearer " + SMARTTHINGS_TOKEN}
    if request.method == 'GET':
        states = {"devices": []}
        for device, id in SMARTTHINGS_DEVICES.items():
            response = requests.get(f'{SMARTTHINGS_DEVICES_URL}/{id}/status', headers=headers)
            device_state = response.json()
            states['devices'].append({"name": device, 'state': device_state['components']['main']['switch']['switch']['value']})
        return jsonify(states)
    if request.method == 'POST':
        data = request.get_json()
        new_state = ''
        device = ''
        if data['light'] == 'pineappleLightSwitch':
            device = 'Pineapple'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'diningLightSwitch':
            device = 'Dining Room Table'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'garageLightSwitch':
            device = 'Garage Light'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'bedroomLightSwitch':
            device = 'Bedroom Light'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'lanternLightSwitch':
            device = 'Drinking Lamp'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        elif data['light'] == 'stringLightSwitch':
            device = 'String Lights'
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
        params = {'commands': [{"component": 'main',
                                "capability": 'switch',
                                "command": new_state}]}
        requests.post(f"{SMARTTHINGS_DEVICES_URL}/{SMARTTHINGS_DEVICES[device]}/commands", headers=headers, json=params)
        
        return jsonify([])

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
