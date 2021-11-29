from flask import Blueprint, jsonify, make_response, request, abort
from flask.signals import request_finished
from app import db
from app.models import VenstarTemp
from datetime import datetime, timedelta

venstar_bp = Blueprint('venstar_bp', __name__, url_prefix='/temps')
login_bp = Blueprint('login_bp', __name__, url_prefix='/')

@login_bp.route("", methods=['GET'])
def login():
    return jsonify([])

@venstar_bp.route("", methods=['GET'])
def display_recent_temps():
    start_time = datetime.now() - timedelta(days=1)
    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).all()
    data = {}
    for temp in temps:
        data[datetime.strftime(temp.time, '%Y-%b-%d %H:%M')] = [temp.local_temp, temp.remote_temp]
    return make_response(data)
