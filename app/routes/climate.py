
from flask import Blueprint, make_response, request, jsonify
from app import db
from app.models import VenstarTemp
from datetime import datetime, timedelta, date
import requests
from dotenv import load_dotenv
import os
import platform
from discordwebhook import Discord

if platform.system() == 'Linux':
    from adafruit_bme280 import basic as adafruit_bme280
    from board import D4
    import board

climate_bp = Blueprint('climate_bp', __name__, url_prefix='/climate')

load_dotenv()
SMARTTHINGS_TOKEN = os.environ.get("SMARTTHINGS_TOKEN")
VENSTAR_IP = os.environ.get("VENSTAR_IP")
GARAGE_IP = os.environ.get("GARAGE_PI_IP")
DIRECTORY = os.environ.get("DIRECTORY")
VENSTAR_INFO_URL = 'http://' + VENSTAR_IP + '/query/info'
VENSTAR_SENSOR_URL = 'http://' + VENSTAR_IP + '/query/sensors'
VENSTAR_RUNTIMES_URL = 'http://' + VENSTAR_IP + '/query/runtimes'
VENSTAR_CONTROL_URL = 'http://' + VENSTAR_IP + '/control'
GARAGE_PI_STATUS_URL = 'http://' + GARAGE_IP + '/get-status'
SMARTTHINGS_DEVICES_URL = 'https://api.smartthings.com/v1/devices'

DISCORD_URL = os.environ.get("DISCORD_GENERAL_URL")
DISCORD = Discord(url=DISCORD_URL)

@climate_bp.route("/venstar-status", methods=["GET", "POST"])
def interact_with_venstar():
    """Get the current status of venstar ecosystem, Change the current status of venstar ecosystem"""
    if request.method == 'GET':
        # Transfer Values
        # Change mode data (0,1,2,3) to understandable strings
        venstar_modes = {0: 'OFF', 1: 'HEAT', 2: 'COOL', 3: 'AUTO'}
        # Change fan state to ON or AUTO
        fan_states = {0: 'AUTO', 1: 'ON'}
        
        # First try to get VENSTAR data
        try:
            info_response = requests.get(VENSTAR_INFO_URL)
            info = info_response.json()
            sensor_response = requests.get(VENSTAR_SENSOR_URL)
            sensors = sensor_response.json()
            runtime_response = requests.get(VENSTAR_RUNTIMES_URL)
            runtimes = runtime_response.json()
        except requests.exceptions.RequestException as e:
            # Error in getting VENSTAR data, send error to DISCORD
            DISCORD.post(content=f"Problem with Venstar. Error: {e}")
        else:
            # No errors: Set remote temperature (outdoor)
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
                    'mode': venstar_mode, 'fan_setting': fan_setting, 'heat_time': heat_time, 
                    'cool_time': cool_time}
        return jsonify(data)
    else:
        # POST METHOD: CHANGE VENSTAR STATUS
        # Change mode data (0,1,2,3) to understandable strings
        venstar_modes = {'OFF': 0, 'HEAT': 1, 'COOL': 2, 'AUTO': 3}
        # Change fan state to ON or AUTO
        fan_states = {'AUTO': 0, 'ON': 1}
        data = request.get_json()
        params = {
            'mode': venstar_modes[data["mode"]],
            'fan': fan_states[data['fan_setting']],
            'heattemp': data['heat_temp'],
            'cooltemp': data['cool_temp']
        }
        requests.post(VENSTAR_CONTROL_URL, params=params)
        return jsonify([]), 201


@climate_bp.route("/current_temps", methods=["GET", "POST"])
def return_current_temps_for_api():
    """Returns a JSON of the current temperatures onboard the server"""
    if request.method == "GET":
        # Gather the last known temp data from database
        last_temps = VenstarTemp.query.order_by(VenstarTemp.time.desc()).first()
        
        # Sensors wont work unless in PROD
        if platform.system() == 'Linux':
            i2c = board.I2C()
            BME280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)
            farenheight = BME280.temperature * (9 / 5) + 32
            humidity = BME280.humidity
            pressure = round(BME280.pressure,1)
        else:
            # Not in PROD: use the last updated data
            farenheight = last_temps.pi_temp
            humidity = last_temps.humidity
            pressure = round(last_temps.pressure,1)
        
        # Get the current venstar thermostat temperature and the outdoor temp.
        venstar_response = requests.get(VENSTAR_SENSOR_URL)
        venstar_info = venstar_response.json()
        response = requests.get(GARAGE_PI_STATUS_URL)
        garage_response = response.json()
        try:
            # Look for the Remote (outdoor) and Space Temp (thermostat) sensor temps
            for sensor in venstar_info['sensors']:
                if sensor['name'] == "Space Temp":
                    thermostat_temp = sensor["temp"]
                if sensor['name'] == "Remote":
                    outdoor_temp = sensor['temp']
        except KeyError:
            # If VENSTAR request came back 404, use the last temps for the sensors
            thermostat_temp = last_temps.local_temp
            outdoor_temp = last_temps.remote_temp

        return jsonify({'pressure': pressure, 'thermostat': thermostat_temp, 'living_room': int(farenheight), 'living_room_humidity': int(humidity), 
                        'outside': outdoor_temp, "garage": int(garage_response["temp"])}), 200
    elif request.method == "POST":
        # For a post of the current temps, we create a new object based on the param data, add, and commit it to the database
        data = request.get_json()['data']
        new_temps = VenstarTemp(time=data['time'],
                                local_temp=data['local_temp'],
                                remote_temp=data['remote_temp'],
                                pi_temp=data['pi_temp'],
                                humidity=data['humidity'],
                                pressure=data['pressure'],
                                heat_runtime=data['heat_runtime'],
                                cool_runtime=data['cool_runtime'])
        db.session.add(new_temps)
        db.session.commit()
        return make_response({"Status": "Created"}, 201)


@climate_bp.route('/today', methods=['GET'])
def return_climate_data_from_today():
    """Returns dataset of today's climate data"""
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    for i in range(len(temps)):
        # Record the last time each time (after the first) for subtracting from the current 
        # ultimately to get the time used during that 15 min cycle
        if i != len(temps)-1:
            last_heat_time = temps[i+1].heat_runtime
            last_cool_time = temps[i+1].cool_runtime
        else:
            last_heat_time = 0
            last_cool_time = 0
        # If the current record has a pressure, include. Otherwise, N/A
        if temps[i].pressure:
            pressure = round(temps[i].pressure,1)
        else:
            pressure = "N/A"
        # Gather each 15 min record into the data dictionary
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime - last_heat_time,
                     'cool_time': temps[i].cool_runtime - last_cool_time,
                     'pressure': pressure})
    return make_response(data, 200)

@climate_bp.route('/<requested_date>', methods=['GET'])
def return_climate_data_from_date(requested_date):
    """Returns dataset of requested days venstar usage data"""
    # Check format of requested date (YYYY-MM-DD) OR (YYYY-MMM-DD)
    try:
        start_date = datetime.strptime(requested_date, '%Y-%m-%d')
    except ValueError:
        try:
            start_date = datetime.strptime(requested_date, '%Y-%b-%d')
        except ValueError:
            return make_response({}, 404)
    end_time = start_date + timedelta(days=1)

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_date, VenstarTemp.time<end_time).order_by(VenstarTemp.time.desc()).all()

    data = {'data': []}
    for i in range(len(temps)):
        # Record the last time each time (after the first) for subtracting from the current 
        # ultimately to get the time used during that 15 min cycle
        if i != len(temps)-1:
            last_heat_time = temps[i+1].heat_runtime
            last_cool_time = temps[i+1].cool_runtime
        else:
            last_heat_time = 0
            last_cool_time = 0
        # If the current record has a pressure, include. Otherwise, N/A
        if temps[i].pressure:
            pressure = round(temps[i].pressure,1)
        else:
            pressure = "N/A"
        # Gather each 15 min record into the data dictionary
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime - last_heat_time,
                     'cool_time': temps[i].cool_runtime - last_cool_time,
                     "pressure": pressure})
    return make_response(data, 200)


# DEPRECATED -----------------------------------------------------------------
# @venstar_bp.route("/V1", methods=['GET'])
# def kiowa_dashboard():
#     """Main dashboard for Kiowa. Gathers data from the VENSTAR thermostat, database for humidity and lighting and renders the page"""
#     authorized_ip = os.environ.get("IP_ALLOWED")
#     if request.remote_addr not in authorized_ip:
#         return make_response(f'Sorry, {request.remote_addr} your computer is not permitted to view this resource.', 401)
    
#     # Transfer Values
#     # Change lighting bool to ON or OFF
#     lighting_bool = {1: 'ON', 0: 'OFF'}
#     # Change mode data (0,1,2,3) to understandable strings
#     venstar_modes = {0: 'OFF', 1: 'HEAT', 2: 'COOL', 3: 'AUTO'}
#     # Change fan state to ON or AUTO
#     fan_states = {0: 'AUTO', 1: 'ON'}

#     yesterday = datetime.now() - timedelta(hours=36)
#     recent = datetime.now() - timedelta(hours=8)
    
#     # Set Default Values
#     remote_temp = 'N/A' # set to N/A in case its not found!
#     heat_time = 'N/A'
#     cool_time = 'N/A'
#     fan_setting = 'AUTO'
#     venstar_mode = 'OFF'
#     heat_setting = 0
#     cool_setting = 0
#     therm_temp = None
#     last_bedtime_time = "No Data"
#     today_bedtime_time = "No Data"
#     recent_data = VenstarTemp.query.order_by(VenstarTemp.time.desc()).first()
#     landscape_state = LightingStatus.query.order_by(LightingStatus.time.desc()).first()
#     bedtime = Bedtime.query.filter(Bedtime.time>=yesterday).order_by(Bedtime.time.desc()).all()
#     for row in bedtime:
#         if row.time > recent and today_bedtime_time == "No Data":
#             today_bedtime_time = datetime.strftime(row.time, "%Y-%m-%d %I:%M %p")
#         elif row.time < recent and last_bedtime_time == "No Data":
#             last_bedtime_time = datetime.strftime(row.time, "%Y-%m-%d %I:%M %p")
    
#     # Gather all necessary real-time data
#     try:
#         info_response = requests.get(VENSTAR_INFO_URL)
#         info = info_response.json()
#         sensor_response = requests.get(VENSTAR_SENSOR_URL)
#         sensors = sensor_response.json()
#         runtime_response = requests.get(VENSTAR_RUNTIMES_URL)
#         runtimes = runtime_response.json()
#     except requests.exceptions.RequestException as e:
#         print(e)
#     else:
#         # Set remote temperature (outdoor)
#         for sensor in sensors['sensors']:
#             if sensor['name'] == 'Remote':
#                 remote_temp = int(sensor['temp'])

#         # Collect and transpose real-time data
#         heat_time = runtimes['runtimes'][-1]['heat1']
#         cool_time = runtimes['runtimes'][-1]['cool1']
#         fan_setting = fan_states[info['fan']]
#         venstar_mode = venstar_modes[info['mode']]
#         heat_setting = int(info['heattemp'])
#         cool_setting = int(info['cooltemp'])
#         therm_temp = int(info['spacetemp'])
        
#     finally:
#         # Collect final into dictionary for transfer
#         data = {'current_temp': therm_temp, 'outside_temp': remote_temp, 
#                 'heat_temp': heat_setting, 'cool_temp': cool_setting,
#                 'mode': venstar_mode, 'fan_setting': fan_setting, 'humidity': recent_data.humidity, 
#                 'living_room_temp': int(recent_data.pi_temp), 'heat_time': heat_time, 
#                 'cool_time': cool_time, 'landscape_state': lighting_bool[landscape_state.setting], 
#                 'last_landscape_change': landscape_state.time, 'last_bedtime': last_bedtime_time, 
#                 'today_bedtime': today_bedtime_time}
        
#         return render_template('dashboard.html', data=data)

# @venstar_bp.route("", methods=['POST'])
# def venstar_changes():
#     """Middle-man for changing VENSTAR status. POST request made from dashboard, 
#     makes post request to VENSTAR control, and re-renders dashboard"""
#     params = {
#         'mode': request.form.get('mode'),
#         'fan': request.form.get('fan'),
#         'heattemp': request.form.get('heat_temp'),
#         'cooltemp': request.form.get('cool_temp')
#     }
#     requests.post(VENSTAR_CONTROL_URL, params=params)
#     return redirect(url_for('venstar_bp.kiowa_dashboard'))
