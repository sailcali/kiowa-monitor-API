# kiowa-monitor-API

All-encompassing smart home monitor website designed for personal LAN use only. 

WARNING: NO SECURITY PROTOCOLS HAVE BEEN ADDED YET. THIS IS DESIGNED AT THIS POINT FOR LOCAL LAN USE ONLY.

FLASK Endpoints:

GET /climate/venstar-status
* Returns JSON of current VENSTAR settings and temps

POST /climate/venstar-status
* Changes VENSTAR thermostat state. Returns empty list

GET /climate/current_temps
* Returns JSON of current temps, pressure, humidity

POST /climate/current_temps
* Periodic posting of climate data to database (15 minutes)

GET /climate/today
* Returns todays climate data in JSON format data:list

GET /climate/<YYYY-MM-DD>
* Returns climate data in JSON format data:list for a specific date

GET /api
* Returns JSON of available API calls (not updated)

GET /api/garage-status
* Returns garage PICO status (temperature and lighting) as JSON

POST /api/record-landscape-change
* Records landscape lighting changes in database (requires boolean 'state_change")

POST /api/food
* Records new food item in database for food tracker

GET /api/weather/outlook
* Returns API data from openweathermap

GET /lighting/status
* Returns JSON of lighting states from SMARTTHINGS and Garage PI

POST /lighting/status
* Change the state of lighting, return empty list

GET /lighting/bedtime
* Returns most recent bedtime data

POST /lighting/bedtime
* Turns off select lights and records time in database

GET /solar/production/<YYYY-MM-DD>
* Returns production data for a given date

POST /solar/production/<YYYY-MM-DD>
* Posts daily production data to database, returns the same

GET /solar/access
* Gets API keys for enphase access based on a user code. Requires API key.

POST /solar/access
* Sets API keys for enphase access into database. Requires API key.

GET /solar/production/last-update
* Returns the date of the last production update

GET /solar/production/lifetime
* Returns all known production data from database as JSON.

GET solar/production/period-sum
* Returns solar production data as a sum during a specified period. Requires 'start_date' and 'end_date' as YYYY-MM-DD.

GET /solar/production/period/data
* Returns all known production data over a period from database as JSON. Requires 'start_date' and 'end_date' as YYYY-MM-DD.

POST /landscape/change-state
* Turns on/off landscape lighting (requires 'state' as 0 or 1)

GET /food/schedule
* Renders food schedule site (not yet react)

POST /food/schedule
* Records new food item in the schedule (or updates if one is currently in the slot) and re-renders (not yet react)

GET /pool
* Simple connector to return the same details from the pool valve controller

POST /pool/valve/open
* Try to open the valve and return a status (allowed - delay: seconds{int} (default 60))

POST /pool/valve/close
* Try to close the valve and return a status (allowed - delay: seconds{int} (default 60))

POST /pool/set-temp
* Changes the set temperature on the solar valve controller (requires- setting: temp{int})