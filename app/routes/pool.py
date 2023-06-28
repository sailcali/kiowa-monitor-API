from flask import Blueprint, request, jsonify
import requests
import os
from app.models import PoolData
from app import db
import pytz
from datetime import datetime, timedelta
from app.pool_utils.pool import Pool
from discordwebhook import Discord

POOL_URL = os.environ.get("POOL_URL")

pool_bp = Blueprint('pool_bp', __name__, url_prefix='/pool')
POOL = Pool()
DISCORD_POOL_URL = os.environ.get("DISCORD_POOL_URL")
DISCORD = Discord(url=DISCORD_POOL_URL)

@pool_bp.route('/temp/set-temp', methods=['POST'])
def set_pool_temp():
    """Changes the set temperature on the solar valve controller"""
    body = request.get_json()
    params = {"setting": body["setting"]}
    response = requests.post(POOL_URL + "temp", params=params)
    if response.status_code == 200:
        return jsonify({"status": f"New set temp {body['setting']} deg"}), 201
    else:
        return jsonify({"status": "connectionError"}), 400
    
@pool_bp.route('/status', methods=['GET', 'POST'])
def get_set_pool_status():
    """Get or set the current pool controller values"""
    if request.method == 'GET':
        response = requests.get(POOL_URL + "status")
        pool_json =  response.json()

        return jsonify(pool_json), 200
    elif request.method == 'POST':
        body = request.get_json()['data']
        # Get pool temp for x minutes ago and evaluate whether or not to turn off the solar
        start_datetime = datetime.now(tz=pytz.UTC) - timedelta(minutes=10)
        temps = PoolData.query.filter(PoolData.datetime>start_datetime).first()
        if temps and POOL.valve:
            POOL.evaluate_pool_temp(body['water_temp'], temps.water_temp)
        last_status = PoolData.query.order_by(PoolData.datetime.desc()).first()
        if last_status.valve != body['valve']:
            if body['valve'] == 1:
                DISCORD.post(content="Pool valve is open")
                POOL.valve = True
            else:
                DISCORD.post(content="Pool valve is closed")
                POOL.valve = False
                POOL.decline_hits = 0
        new_pool_data = PoolData(datetime=datetime.now(tz=pytz.UTC),
                                    roof_temp=body['roof_temp'],
                                    water_temp=body['water_temp'],
                                    valve=body['valve'],
                                    temp_range=body['temp_range'],
                                    decline_hits=POOL.decline_hits,
                                    max_hit_delay=body['max_hit_delay'])
        db.session.add(new_pool_data)
        db.session.commit()

        return jsonify({"Status": "Created"}), 201
    
@pool_bp.route('/valve/open', methods=['POST'])
def open_pool_valve():
    """Try to open the valve and return a status"""
    body = request.get_json()
    params = {"valve": 1}

    try:
        params["delay"] = body['delay']
    except (TypeError, KeyError):
        params["delay"] = 60
    
    result = POOL.close_valve(params)
    
    if result == 200:
        return jsonify({'status': 'opening'}), 201
    elif result == 400:
        return jsonify({'status': 'open'})
    else:
        return jsonify({'status': "connectionError"})

@pool_bp.route('/valve/close', methods=['POST'])
def close_pool_valve():
    """Try to close the valve and return a status"""
    body = request.get_json()
    params = {"valve": 0}

    try:
        params["delay"] = body['delay']
    except (TypeError, KeyError):
        params["delay"] = 60
    
    result = POOL.close_valve(params)
    
    if result == 200:
        return jsonify({'status': 'closing'}), 201
    elif result == 400:
        return jsonify({'status': 'closed'})
    else:
        return jsonify({'status': "connectionError"})

@pool_bp.route('/config', methods=['POST'])
def change_pool_config():
    config = request.get_json()
    if "MAX_DECLINE_HITS" in config:
        POOL.max_decline_hits = config['MAX_DECLINE_HITS']
    print(POOL.max_decline_hits)
    return jsonify({"status":"changed"}), 201