from flask import Blueprint, request, jsonify
import requests
from dotenv import load_dotenv
import os

load_dotenv()

POOL_URL = os.environ.get("POOL_URL")

pool_bp = Blueprint('pool_bp', __name__, url_prefix='/pool')

@pool_bp.route('/temp/set-temp', methods=['POST'])
def set_pool_temp():
    body = request.get_json()

    params = {"setting": body["setting"]}
    response = requests.post(POOL_URL + "temp", params=params)
    if response.status_code == 200:
        return jsonify({"status": f"New set temp {body['setting']} deg"}), 201
    else:
        return jsonify({"status": "connectionError"}), 400
    
@pool_bp.route('/', methods=['GET'])
def get_pool_details():
    """Simple connector to return the same details from the pool valve controller"""
    response = requests.get(POOL_URL)
    pool_json =  response.json()

    return jsonify(pool_json), 200

@pool_bp.route('/valve/open', methods=['POST'])
def open_pool_valve():
    """Try to open the valve and return a status"""
    body = request.get_json()
    params = {"valve": 1}

    try:
        params["delay"] = body['delay']
    except (TypeError, KeyError):
        pass
    
    response = requests.post(POOL_URL + "valve", params=params)
    
    if response.status_code == 200:
        return jsonify({'status': 'opening'}), 201
    elif response.status_code == 400:
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
        pass

    response = requests.post(POOL_URL + "valve", params=params)

    if response.status_code == 200:
        return jsonify({'status': 'closing'}), 201
    elif response.status_code == 400:
        return jsonify({'status': 'closed'})
    else:
        return jsonify({'status': "connectionError"})

