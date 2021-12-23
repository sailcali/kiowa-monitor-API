from flask import Blueprint, jsonify, make_response, request, abort, render_template, redirect, url_for
from flask.signals import request_finished
from app import db
from app.models import VenstarTemp
from datetime import datetime, timedelta, date
import requests
from dotenv import load_dotenv
import os

load_dotenv()
IP = os.environ.get("VENSTAR_IP")
VENSTAR_INFO_URL = 'http://' + IP + '/query/info'
VENSTAR_SENSOR_URL = 'http://' + IP + '/query/sensors'
VENSTAR_CONTROL_URL = 'http://' + IP + '/control'

temps_bp = Blueprint('temps_bp', __name__, url_prefix='/temps')
venstar_bp = Blueprint('venstar_bp', __name__, url_prefix='/venstar')
usage_bp = Blueprint('usage_bp', __name__, url_prefix='/usage')
login_bp = Blueprint('login_bp', __name__, url_prefix='/')

@login_bp.route("", methods=['GET'])
def login():
    return redirect(url_for('venstar_bp.venstar_dashboard'))

@venstar_bp.route("", methods=['GET'])
def venstar_dashboard():
    """Main dashboard for VENSTAR thermostat. Gathers data from the unit (and database for humidity) and renders the page"""
    authorized_ip = os.environ.get("IP_ALLOWED")
    if request.remote_addr not in authorized_ip:
        return make_response('Sorry, your computer is not permitted to view this resource.', 401)

    # Gather all necessary data
    info_response = requests.get(VENSTAR_INFO_URL)
    info = info_response.json()
    sensor_response = requests.get(VENSTAR_SENSOR_URL)
    sensors = sensor_response.json()
    recent_data = VenstarTemp.query.order_by(VenstarTemp.time.desc()).first()

    # Gather the outdoor temp
    remote_temp = 'N/A' # set to N/A in case its not found!
    for sensor in sensors['sensors']:
        if sensor['name'] == 'Remote':
            remote_temp = sensor['temp']
    
    # Change mode data (0,1,2,3) to understandable strings
    if info['mode'] == 0:
        thermostat_mode = 'OFF'
    elif info['mode'] == 1:
        thermostat_mode = 'HEAT'
    elif info['mode'] == 2:
        thermostat_mode = 'COOL'
    else:
        thermostat_mode = 'AUTO'
    if info['fan'] == 0:
        fan_setting = 'AUTO'
    else:
        fan_setting = 'ON'
    data = {'current_temp': info['spacetemp'], 'outside_temp': remote_temp, 
            'heat_temp': info['heattemp'], 'cool_temp': info['cooltemp'],
            'mode': thermostat_mode, 'fan_setting': fan_setting, 'humidity': recent_data.humidity}
    return render_template('venstar_dashboard.html', data=data)

@venstar_bp.route("", methods=['POST'])
def venstar_changes():
    params = {
        'mode': request.form.get('mode'),
        'fan': request.form.get('fan'),
        'heattemp': request.form.get('heat_temp'),
        'cooltemp': request.form.get('cool_temp')
    }
    requests.post(VENSTAR_CONTROL_URL, params=params)
    return redirect(url_for('venstar_bp.venstar_dashboard'))

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

@usage_bp.route("/today", methods=["GET"])
def display_usage_from_today():
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    for i in range(len(temps)):
        if i != len(temps):
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
