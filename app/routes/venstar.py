
from flask import Blueprint, make_response, request, render_template, redirect, url_for
from app import db
from app.models import LightingStatus, VenstarTemp, Bedtime
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import os

venstar_bp = Blueprint('venstar_bp', __name__, url_prefix='/venstar')

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

@venstar_bp.route("", methods=['GET'])
def kiowa_dashboard():
    """Main dashboard for Kiowa. Gathers data from the VENSTAR thermostat, database for humidity and lighting and renders the page"""
    authorized_ip = os.environ.get("IP_ALLOWED")
    if request.remote_addr not in authorized_ip:
        return make_response(f'Sorry, {request.remote_addr} your computer is not permitted to view this resource.', 401)
    
    # Transfer Values
    # Change lighting bool to ON or OFF
    lighting_bool = {1: 'ON', 0: 'OFF'}
    # Change mode data (0,1,2,3) to understandable strings
    venstar_modes = {0: 'OFF', 1: 'HEAT', 2: 'COOL', 3: 'AUTO'}
    # Change fan state to ON or AUTO
    fan_states = {0: 'AUTO', 1: 'ON'}

    yesterday = datetime.now() - timedelta(hours=36)
    recent = datetime.now() - timedelta(hours=8)
    
    # Set Default Values
    remote_temp = 'N/A' # set to N/A in case its not found!
    heat_time = 'N/A'
    cool_time = 'N/A'
    fan_setting = 'AUTO'
    venstar_mode = 'OFF'
    heat_setting = 0
    cool_setting = 0
    therm_temp = None
    last_bedtime_time = "No Data"
    today_bedtime_time = "No Data"
    recent_data = VenstarTemp.query.order_by(VenstarTemp.time.desc()).first()
    landscape_state = LightingStatus.query.order_by(LightingStatus.time.desc()).first()
    bedtime = Bedtime.query.filter(Bedtime.time>=yesterday).order_by(Bedtime.time.desc()).all()
    for row in bedtime:
        if row.time > recent and today_bedtime_time == "No Data":
            today_bedtime_time = datetime.strftime(row.time, "%Y-%m-%d %I:%M %p")
        elif row.time < recent and last_bedtime_time == "No Data":
            last_bedtime_time = datetime.strftime(row.time, "%Y-%m-%d %I:%M %p")
    
    # Gather all necessary real-time data
    try:
        info_response = requests.get(VENSTAR_INFO_URL)
        info = info_response.json()
        sensor_response = requests.get(VENSTAR_SENSOR_URL)
        sensors = sensor_response.json()
        runtime_response = requests.get(VENSTAR_RUNTIMES_URL)
        runtimes = runtime_response.json()
    except requests.exceptions.RequestException as e:
        print(e)
    else:
        # Set remote temperature (outdoor)
        for sensor in sensors['sensors']:
            if sensor['name'] == 'Remote':
                remote_temp = int(sensor['temp'])

        # Collect and transpose real-time data
        heat_time = runtimes['runtimes'][-1]['heat1']
        cool_time = runtimes['runtimes'][-1]['cool1']
        fan_setting = fan_states[info['fan']]
        venstar_mode = venstar_modes[info['mode']]
        heat_setting = int(info['heattemp'])
        cool_setting = int(info['cooltemp'])
        therm_temp = int(info['spacetemp'])
        
    finally:
        # Collect final into dictionary for transfer
        data = {'current_temp': therm_temp, 'outside_temp': remote_temp, 
                'heat_temp': heat_setting, 'cool_temp': cool_setting,
                'mode': venstar_mode, 'fan_setting': fan_setting, 'humidity': recent_data.humidity, 
                'living_room_temp': int(recent_data.pi_temp), 'heat_time': heat_time, 
                'cool_time': cool_time, 'landscape_state': lighting_bool[landscape_state.setting], 
                'last_landscape_change': landscape_state.time, 'last_bedtime': last_bedtime_time, 
                'today_bedtime': today_bedtime_time}
        
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
