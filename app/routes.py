from flask import Blueprint, jsonify, make_response, request, abort, render_template, redirect, url_for
from flask.signals import request_finished
from app import db
from app.models import LightingStatus, VenstarTemp
from datetime import datetime, timedelta, date
import requests
from dotenv import load_dotenv
import os

load_dotenv()
IP = os.environ.get("VENSTAR_IP")
PI_ZERO_IP = os.environ.get("PI_ZERO_IP")
VENSTAR_INFO_URL = 'http://' + IP + '/query/info'
VENSTAR_SENSOR_URL = 'http://' + IP + '/query/sensors'
VENSTAR_RUNTIMES_URL = 'http://' + IP + '/query/runtimes'
VENSTAR_CONTROL_URL = 'http://' + IP + '/control'
GARAGE_PI_STATUS_URL = 'http://' + PI_ZERO_IP + '/get-status'

temps_bp = Blueprint('temps_bp', __name__, url_prefix='/temps')
venstar_bp = Blueprint('venstar_bp', __name__, url_prefix='/venstar')
usage_bp = Blueprint('usage_bp', __name__, url_prefix='/usage')
login_bp = Blueprint('login_bp', __name__, url_prefix='/')
landscape_bp = Blueprint('landscape_bp', __name__, url_prefix='/landscape')

@login_bp.route("", methods=['GET'])
def login():
    return redirect(url_for('venstar_bp.kiowa_dashboard'))

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
    garage_response = requests.get(GARAGE_PI_STATUS_URL)
    garage_status = garage_response.json()

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
    # Account for garage temp being null...
    if garage_status['temperature']:
        garage_temp = int(garage_status['temperature'])
    else: 
        garage_temp = 'UNK'
    data = {'current_temp': int(info['spacetemp']), 'outside_temp': int(remote_temp), 
            'heat_temp': int(info['heattemp']), 'cool_temp': int(info['cooltemp']),
            'mode': venstar_modes[info['mode']], 'fan_setting': fan_states[info['fan']], 'humidity': recent_data.humidity, 
            'living_room_temp': int(recent_data.pi_temp), 'heat_time': runtimes['runtimes'][-1]['heat1'], 
            'cool_time': runtimes['runtimes'][-1]['cool1'], 'landscape_state': lighting_bool[garage_status['lighting_state']], 
            'last_landscape_change': landscape_state.time, 'garage_temp': garage_temp, 
            'current_landscape_delay': garage_status['current_delay']}
    
    return render_template('dashboard.html', data=data)

@venstar_bp.route("", methods=['POST'])
def venstar_changes():
    params = {
        'mode': request.form.get('mode'),
        'fan': request.form.get('fan'),
        'heattemp': request.form.get('heat_temp'),
        'cooltemp': request.form.get('cool_temp')
    }
    requests.post(VENSTAR_CONTROL_URL, params=params)
    return redirect(url_for('venstar_bp.kiowa_dashboard'))

@temps_bp.route("", methods=['GET'])
def display_recent_temps():
    start_time = datetime.now() - timedelta(days=1)
    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).all()
    data = {}
    for temp in temps:
        data[datetime.strftime(temp.time, '%Y-%b-%d %H:%M')] = [temp.local_temp, temp.pi_temp, temp.remote_temp, temp.humidity]
    return make_response(data)

@temps_bp.route("/<requested_date>", methods=["GET"])
def display_temps_by_date(requested_date):
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

@temps_bp.route("/today_api", methods=["GET"])
def return_temps_for_api():
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

@temps_bp.route("/today", methods=["GET"])
def display_temps_from_today():
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

@landscape_bp.route("/update-state", methods=['POST'])
def change_landscape_state():
    request_body = request.get_json()
    last_entry = LightingStatus.query.order_by(LightingStatus.time.desc()).first()
    new_entry = LightingStatus(time=request_body['time'], device='landscape', setting=request_body['state'])
    if not request_body['state']:
        time_on = datetime.strptime(new_entry.time, '%Y-%m-%d %H:%M:%S') - last_entry.time
        new_entry.time_on = time_on.total_seconds()/60
    db.session.add(new_entry)
    db.session.commit()
    return jsonify(new_entry.time_on), 201