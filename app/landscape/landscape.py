#!/usr/bin/env python3

import re
from astral.sun import sun
from datetime import date
import os
import pytz
from astral.geocoder import database, lookup
from datetime import datetime, timedelta
import requests
import configparser
# import logging
from app import db
from app.models import LightingStatus

DIRECTORY = os.environ.get("DIRECTORY")

def change_landscape(on_off=3, delay_request=False):
    """Algorithm for deciding state of landscape lighting.
    on_off = 0 : turn off
    on_off = 1 : turn on
    on_off = 3 : no argument given, default to check programming
    delay_request = {datetime} : gets logged in config file and used as delay param
    delay_request = false : config file is used as delay param"""
    
    # Setup logger and config file
    # logging.basicConfig(level=logging.DEBUG, filename='main.log', filemode='w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    print('checking landscape')
    config = configparser.ConfigParser()
    config.read_file(open(f'{DIRECTORY}/delay_time.conf'))
    
    # Set the config file to the new delay request if given
    # Then set the current delay datetime
    if delay_request:
        config.set('DelayDatetime', 'value', datetime.strftime(delay_request, '%Y-%m-%d %H:%M:%S'))
        with open(f'{DIRECTORY}/delay_time.conf', 'w') as configfile:
            config.write(configfile)
    value = config.get('DelayDatetime', 'value')
    delay_datetime = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

    # logging.info('config opened')
    
    # This will track if the lights are actually changed or not
    state_change = None

    # Get time of sunrise and sunset
    city = lookup("San Diego", database())
    s = sun(city.observer, date=date.today())
    sunrise = s["sunrise"]
    sunrise = sunrise.astimezone(tz=pytz.timezone("US/Pacific"))
    sunset = s["sunset"] + timedelta(minutes=15)
    
    sunset = sunset.astimezone(tz=pytz.timezone("US/Pacific"))
    
    # Get the current settings from PICO
    response = requests.get('http://192.168.86.33/get-status')
    current_status = int(response.json()['current_status']['landscape'])
    # logging.info(current_status)
    # If a delay to the programming is requested (on/off == 1 or 2)
    # Send code to PICO to adjust landscape
    # Add state to data
    if on_off == 0 and current_status == 1:
        response = requests.get('http://192.168.86.33/lights/off')
        if response.json()['current_status']['landscape'] == 0:
            state_change = False
    elif on_off == 1 and current_status == 0:
        # logging.info('turning on')
        response = requests.get('http://192.168.86.33/lights/on')
        if response.json()['current_status']['landscape'] == 1:
            state_change = True

    # If the current delay time is not beyond the current time
    # Run the programming
    if delay_datetime < datetime.today():
        # logging.info('delay_datetime OK')

        # If sunset has occurred, make sure its on
        if sunset.time() < datetime.now().time():
            if current_status == 0:
                response = requests.get('http://192.168.86.33/lights/on')
                if response.json()['current_status']['landscape'] == 1:
                    state_change = True
        else: # If sunset has not occurred, make sure its off
            if current_status == 1:
                response = requests.get('http://192.168.86.33/lights/off')
                if response.json()['current_status']['landscape'] == 0:
                    state_change = False
    
    # logging.info(state_change)

    # Update database with new state
    if state_change is not None:
        requests.post('api/record-landscape-change', data={'state_change': state_change})
    
    return state_change

if __name__ == '__main__':
    change_landscape()