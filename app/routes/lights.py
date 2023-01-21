
from flask import Blueprint, jsonify, request
from app import db
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from discordwebhook import Discord
import random

from app.models import Bedtime
from .landscape import landscape
from smartthings import SMARTTHINGS_DEVICES, SMARTTHINGS_NAMES, LIGHTS_FE_TO_BE_CONVERSION, BEDTIME_LIGHTS

lights_bp = Blueprint('lights_bp', __name__, url_prefix='/lighting')

load_dotenv()

SMARTTHINGS_TOKEN = os.environ.get("SMARTTHINGS_TOKEN")
GARAGE_IP = os.environ.get("GARAGE_PI_IP")
GARAGE_PI_STATUS_URL = 'http://' + GARAGE_IP + '/get-status'
SMARTTHINGS_DEVICES_URL = 'https://api.smartthings.com/v1/devices'
LIGHTING_STATES = {'on': True, 'off': False}
DISCORD_URL = os.environ.get("DISCORD_GENERAL_URL")
DISCORD = Discord(url=DISCORD_URL)
BED_SAYINGS = os.environ.get("BED_SAYINGS")

@lights_bp.route('/status', methods=['GET', 'POST'])
def interact_smartthings():
    """GET and SET lighting status in SmartThings"""
    
    # Header needed for GET and SET
    headers = {"Authorization": "Bearer " + SMARTTHINGS_TOKEN}
    
    if request.method == 'GET':
        states = {"devices": {}}

        # First, the landscape light status from the garage PICO
        result = requests.get(GARAGE_PI_STATUS_URL)
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

@lights_bp.route('/bedtime', methods=['GET', "POST"])
def get_set_bedtime():
    """Returns the recent bedtime data. POST will also set bedtime"""
    
    # constants and instants
    last_bedtime_time = "No Data"
    today_bedtime_time = "No Data"
    yesterday = datetime.now() - timedelta(hours=36)
    recent = datetime.now() - timedelta(hours=8)

    # Gather current data from the database back to yesterday, sorted by most recent
    bedtime = Bedtime.query.filter(Bedtime.time>=yesterday).order_by(Bedtime.time.desc()).all()

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
        if datetime.now() - timedelta(hours=24) < bedtime[0].time:
            DISCORD.post(content=random.choice(BED_SAYINGS))

    # Loop through all the bedtime datapoints since yesterday (should only be 0-2) most recent first
    for row in bedtime:
        # If the datapoint is within todays timeframe and todays timeframe has not yet been set
        if row.time > recent and today_bedtime_time == "No Data":
            today_bedtime_time = datetime.strftime(row.time, "%Y-%m-%d %I:%M %p")
        # If the datapoint is outside of today, and yesterday has not been set
        elif row.time < recent and last_bedtime_time == "No Data":
            last_bedtime_time = datetime.strftime(row.time, "%Y-%m-%d %I:%M %p")
    return jsonify({"today_bedtime": today_bedtime_time, "last_bedtime": last_bedtime_time})
