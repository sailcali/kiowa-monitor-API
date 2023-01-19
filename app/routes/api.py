
from flask import Blueprint, jsonify, make_response, request, redirect, url_for
import sqlalchemy
from app import db
from app.models import EnphaseProduction, LightingStatus, VenstarTemp, Food, Bedtime
from datetime import datetime, date, timedelta
import requests
from dotenv import load_dotenv
import os
from smartthings import SMARTTHINGS_DEVICES, SMARTTHINGS_NAMES, LIGHTS_FE_TO_BE_CONVERSION, BEDTIME_LIGHTS
from .landscape import landscape
import platform
from discordwebhook import Discord

if platform.system() == 'Linux':
    from adafruit_bme280 import basic as adafruit_bme280
    from board import D4
    import board

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
LIGHTING_STATES = {'on': True, 'off': False}
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

@api_bp.route("/venstar-status", methods=["GET", "POST"])
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

@api_bp.route("/temps/<requested_date>", methods=["GET"])
def display_temps_by_date(requested_date):
    """Returns a JSON of temperatures from a given date"""
    # Check format of requested date (YYYY-MM-DD) OR (YYYY-MMM-DD)
    try:
        start_date = datetime.strptime(requested_date, '%Y-%m-%d')
    except ValueError:
        try:
            start_date = datetime.strptime(requested_date, '%Y-%b-%d')
        except ValueError:
            return make_response({"Error": "Date format must be YYYY-MM-DD"}, 404)
    # end time is 0001 next day
    end_time = start_date + timedelta(days=1)
    # Retrieve data from database
    temps = VenstarTemp.query.filter(VenstarTemp.time>start_date, VenstarTemp.time<end_time).order_by(VenstarTemp.time.desc()).all()
    # Instatiate empty dictionary
    data = {'data': []}
    # DEPRICATE Ensure the user is not looking for data prior to the heat/cool data collection start date
    if start_date < datetime.strptime('2021-12-05', '%Y-%m-%d'):
        for i in range(len(temps)):
        
            data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                        'local_temp': temps[i].local_temp,
                        'pi_temp': temps[i].pi_temp,
                        'remote_temp': temps[i].remote_temp,
                        'humidity': temps[i].humidity})
    else:
        # Looping through each 15 minute temperature record
        for i in range(len(temps)):
            # Record the last time each time (after the first) for subtracting from the current 
            # ultimately to get the time used during that 15 min cycle
            if i > 0:
                last_heat_time = temps[i-1].heat_runtime
                last_cool_time = temps[i-1].cool_runtime
            else:
                last_heat_time = 0
                last_cool_time = 0
            # Gather each 15 min record into the data dictionary
            data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                        'local_temp': temps[i].local_temp,
                        'pi_temp': temps[i].pi_temp,
                        'remote_temp': temps[i].remote_temp,
                        'humidity': temps[i].humidity,
                        'heat_time': temps[i].heat_runtime - last_heat_time,
                        'cool_time': temps[i].cool_runtime - last_cool_time})
    return make_response(data, 200)

@api_bp.route("/temps", methods=["GET"])
def return_temps_for_api():
    """API call for today's temps"""
    
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    
    for i in range(len(temps)):
        # Record the last time each time (after the first) for subtracting from the current 
        # ultimately to get the time used during that 15 min cycle
        if i > 0:
            last_heat_time = temps[i-1].heat_runtime
            last_cool_time = temps[i-1].cool_runtime
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
    response = make_response(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@api_bp.route("/current_temps", methods=["GET"])
def return_current_temps_for_api():
    """Returns a JSON of the current temperatures onboard the server"""
    
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
        pressure = last_temps.pressure
    
    # Get the current venstar thermostat temperature and the outdoor temp.
    venstar_response = requests.get(VENSTAR_SENSOR_URL)
    venstar_info = venstar_response.json()
    response = requests.get(GARAGE_PICO_URL)
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

@api_bp.route('/venstar-usage', methods=['GET'])
def return_usage_from_today():
    """Returns dataset of today's venstar usage data"""
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
        # Gather each 15 min record into the data dictionary
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime - last_heat_time,
                     'cool_time': temps[i].cool_runtime - last_cool_time})
    return make_response(data, 200)

@api_bp.route('/venstar-usage/<requested_date>', methods=['GET'])
def return_usage_from_date(requested_date):
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
        # Gather each 15 min record into the data dictionary
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime - last_heat_time,
                     'cool_time': temps[i].cool_runtime - last_cool_time})
    return make_response(data, 200)

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

@api_bp.route('/lighting/status', methods=['GET', 'POST'])
def interact_smartthings():
    """GET and SET lighting status in SmartThings"""
    
    # Header needed for GET and SET
    headers = {"Authorization": "Bearer " + SMARTTHINGS_TOKEN}
    
    if request.method == 'GET':
        states = {"devices": {}}

        # First, the landscape light status from the garage PICO
        result = requests.get(GARAGE_PICO_URL)
        garage_response = result.json()

        # Next, loop through each SmartThings light device and put its status into a dictionary (if available)
        for device, id in SMARTTHINGS_DEVICES.items():
            # First check the health of the device
            health_response = requests.get(f'{SMARTTHINGS_DEVICES_URL}/{id}/health', headers=headers)
            device_health = health_response.json()
            
            if device_health['state'] == 'OFFLINE':
                states['devices'][SMARTTHINGS_NAMES[device]] = None
            else:
                # Get the device status
                status_response = requests.get(f'{SMARTTHINGS_DEVICES_URL}/{id}/status', headers=headers)
                device_state = status_response.json()
                # If the device is not found, report as None
                if status_response.status_code == 400:
                    states['devices'][SMARTTHINGS_NAMES[device]] = None
                else:
                    # Otherwise, report the status (true or false)
                    states['devices'][SMARTTHINGS_NAMES[device]] = LIGHTING_STATES[device_state['components']['main']['switch']['switch']['value']]
        # Based on response from the garage, set the landscape lighting status
        if garage_response['current_status']['landscape'] == 1:
            states['devices']["landscape"] = True
        else:
            states['devices']["landscape"] = False
        return jsonify(states)

    if request.method == 'POST':
        
        data = request.get_json()
        new_state = ''
        device = ''
        
        # If its the landscape light we are changing, run the util
        if data['light'] == 'landscape':
            if data['state']:
                landscape.change_landscape(1)
            else:
                landscape.change_landscape(0)
        else:
            # If its a SMARTTHINGS device, convert the device name from Front End language to local language
            device = LIGHTS_FE_TO_BE_CONVERSION[data['light']]
            # Set the new requested state (to SmartThings language on/off)
            if data['state']:
                new_state = 'on'
            else:
                new_state = 'off'
            # Make the request to SMARTTHINGS
            params = {'commands': [{"component": 'main',
                                    "capability": 'switch',
                                    "command": new_state}]}
            requests.post(f"{SMARTTHINGS_DEVICES_URL}/{SMARTTHINGS_DEVICES[device]}/commands", headers=headers, json=params)
        
        return jsonify([])

@api_bp.route('/bedtime', methods=['GET', "POST"])
def get_set_bedtime():
    """Returns the recent bedtime data. POST will also set bedtime"""
    # If its a post request, we want to set the new bedtime FIRST
    if request.method == "POST":
        headers = {"Authorization": "Bearer " + SMARTTHINGS_TOKEN}
        params = {'commands': [{"component": 'main',
                                    "capability": 'switch',
                                    "command": 'off'}]}
        
        # run through each device and turn it off
        for light in BEDTIME_LIGHTS:
            requests.post(f"{SMARTTHINGS_DEVICES_URL}/{SMARTTHINGS_DEVICES[light]}/commands", headers=headers, json=params)

        # Set new bedtime and commit to database
        new_bedtime = Bedtime(time=datetime.now())
        db.session.add(new_bedtime)
        db.session.commit()
        DISCORD.post(content=f"Good night!")
    
    # Go into database and get the last bedtime times in the last 36 hrs
    last_bedtime_time = "No Data"
    today_bedtime_time = "No Data"
    yesterday = datetime.now() - timedelta(hours=36)
    recent = datetime.now() - timedelta(hours=8)
    # Get all data back to yesterday
    bedtime = Bedtime.query.filter(Bedtime.time>=yesterday).order_by(Bedtime.time.desc()).all()
    # Loop through all the bedtime datapoints since yesterday (should only be 0-2) most recent first
    for row in bedtime:
        # If the datapoint is within todays timeframe and todays timeframe has not yet been set
        if row.time > recent and today_bedtime_time == "No Data":
            today_bedtime_time = datetime.strftime(row.time, "%Y-%m-%d %I:%M %p")
        # If the datapoint is outside of today, and yesterday has not been set
        elif row.time < recent and last_bedtime_time == "No Data":
            last_bedtime_time = datetime.strftime(row.time, "%Y-%m-%d %I:%M %p")
    return jsonify({"today_bedtime": today_bedtime_time, "last_bedtime": last_bedtime_time})

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