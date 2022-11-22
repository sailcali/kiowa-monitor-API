#!/var/www/kiowa-monitor-API/venv/bin/python3

from astral.sun import sun
from datetime import date
import os
import pytz
from astral.geocoder import database, lookup
from datetime import datetime, timedelta
import requests
# import configparser

DIRECTORY = os.environ.get("DIRECTORY")

def change_landscape(on_off=3, delay_request=False):
    """Algorithm for deciding state of landscape lighting.
    on_off = 0 : turn off
    on_off = 1 : turn on
    on_off = 3 : no argument given, default to check programming
    delay_request = {datetime} : gets logged in config file and used as delay param
    delay_request = false : config file is used as delay param"""
    
    # Setup logger and config file
    # config = configparser.ConfigParser()
    # config.read_file(open(f'{DIRECTORY}/delay_time.conf'))
    
    # Set the config file to the new delay request if given
    # Then set the current delay datetime
    # if delay_request:
    #     config.set('DelayDatetime', 'value', datetime.strftime(delay_request, '%Y-%m-%d %H:%M:%S'))
    #     with open(f'{DIRECTORY}/delay_time.conf', 'w') as configfile:
    #         config.write(configfile)
    # value = config.get('DelayDatetime', 'value')
    # delay_datetime = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    
    # This will track if the lights are actually changed or not
    state_change = None

    # Get time of sunrise and sunset
    city = lookup("San Diego", database())
    s = sun(city.observer, date=date.today())
    sunset = s["sunset"] + timedelta(minutes=15)
    sunset = sunset.astimezone(tz=pytz.timezone("US/Pacific"))

    # Get the current settings from PICO
    response = requests.get('http://192.168.86.33/get-status')
    if response.status_code != 404:
        current_status = int(response.json()['current_status']['landscape'])
        
        # If a delay to the programming is requested (on/off == 1 or 2)
        # Send code to PICO to adjust landscape
        # Add state to data
        if on_off == 0 and current_status == 1:
            response = requests.get('http://192.168.86.33/lights/off')
            if response.json()['current_status']['landscape'] == 0:
                state_change = False
        elif on_off == 1 and current_status == 0:
            response = requests.get('http://192.168.86.33/lights/on')
            if response.json()['current_status']['landscape'] == 1:
                state_change = True

        # If sunset has occurred and lights are off, turn it on
        if current_status == 0 and sunset.time() > datetime.now().time():
            response = requests.get('http://192.168.86.33/lights/on')
            if response.json()['current_status']['landscape'] == 1:
                state_change = True
        # If its midnight turn the landscape lights off
        if datetime.now().hour == 0 and current_status == 1:
            response = requests.get('http://192.168.86.33/lights/off')
            if response.json()['current_status']['landscape'] == 0:
                state_change = False
            
        # Update database with new state
        if state_change is not None:
            try:
                r = requests.post('http://localhost/api/record-landscape-change', json={'state_change': state_change})
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                r = requests.post('http://localhost:5000/api/record-landscape-change', json={'state_change': state_change})
    return state_change
    
if __name__ == '__main__':
    change_landscape()
