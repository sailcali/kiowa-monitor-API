# kiowa-monitor-API

All-encompassing smart home monitor website designed for personal LAN use only. 
WARNING: NO SECURITY PROTOCOLS HAVE BEEN ADDED YET. THIS IS DESIGNED AT THIS POINT FOR LOCAL LAN USE ONLY.

FLASK Endpoints:
GET /api
* Returns JSON of available API calls (not updated)

GET /api/temps
* returns the temperature data from today as JSON

GET /api/current_temps
* Returns current temperatures as JSON

GET /api/garage-status
* Returns garage PICO status (temperature and lighting) as JSON

POST /api/record-landscape-change
* Records landscape lighting changes in database (requires boolean 'state_change")

POST /api/food
* Records new food item in database for food tracker

GET /api/smartthings/status
* Returns SmartThings devices states as JSON

POST /api/smartthings/status
* Changes lighting status. Requires 'light' with name of the light.

GET /api/solar-production/lifetime
* Returns all known production data from database as JSON.

GET /api/solar-production/period-sum
* Returns solar production data as a sum during a specified period. Requires 'start_date' and 'end_date' as YYYY-MM-DD.

GET /api/solar-production/period/data
* Returns all known production data over a period from database as JSON. Requires 'start_date' and 'end_date' as YYYY-MM-DD.

GET /venstar
* Renders the main dashboard

POST /venstar
* Updates the VENSTAR status from dashboard entries and re-renders site

GET /temps/<YYYY-MM-DD>
* Renders a table of temperatures from a given date

GET /temps/today
* Renders a table of todays temperatures

GET /usage/today
* Renders a table of todays HVAC usage

POST /landscape/change-state
* Turns on/off landscape lighting (requires 'delay_time as minutes and 'state' as 0 or 1)

GET /food/schedule
* Renders food schedule site

POST /food/schedule
* Records new food item in the schedule (or updates if one is currently in the slot) and re-renders
