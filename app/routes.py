from flask import Blueprint, jsonify, make_response, abort, render_template
from flask.signals import request_finished
from app import db
from app.models import VenstarTemp
from datetime import datetime, timedelta, date

venstar_bp = Blueprint('venstar_bp', __name__, url_prefix='/temps')
login_bp = Blueprint('login_bp', __name__, url_prefix='/')

@login_bp.route("", methods=['GET'])
def login():
    return jsonify(['/temps', 'temps/<requested_date>', '/temps/today', '/temps/today_api'])

@venstar_bp.route("", methods=['GET'])
def display_recent_temps():
    start_time = datetime.now() - timedelta(days=1)
    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).all()
    data = {}
    for temp in temps:
        data[datetime.strftime(temp.time, '%Y-%b-%d %H:%M')] = [temp.local_temp, temp.pi_temp, temp.remote_temp, temp.humidity]
    return make_response(data)

@venstar_bp.route("/<requested_date>", methods=["GET"])
def display_temps_by_date(requested_date):
    try:
        start_date = datetime.strptime(requested_date, '%Y-%m-%d')
    except ValueError:
        try:
            start_date = datetime.strptime(requested_date, '%Y-%b-%d')
        except ValueError:
            abort(404)
    end_time = start_date + timedelta(days=1)
    temps = VenstarTemp.query.filter(VenstarTemp.time>start_date, VenstarTemp.time<end_time).all()
    data = {}
    for temp in temps:
        data[datetime.strftime(temp.time, '%Y-%b-%d %H:%M')] = [temp.local_temp, temp.pi_temp, temp.remote_temp, temp.humidity]
    return make_response(data)

@venstar_bp.route("/today_api", methods=["GET"])
def return_temps_for_api():
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).all()
    data = {'data': []}
    for i in range(len(temps)):
        if i > 0:
            last_heat_time = temps[i-1].heat_runtime
            last_cool_time = temps[i-1].cool_runtime
        else:
            last_heat_time = 0
            last_cool_time = 0
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime - last_heat_time,
                     'cool_time': temps[i].cool_runtime - last_cool_time})
    response = make_response(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@venstar_bp.route("/today", methods=["GET"])
def display_temps_from_today():
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).all()
    data = {'data': []}
    for i in range(len(temps)):
        if i > 0:
            last_heat_time = temps[i-1].heat_runtime
            last_cool_time = temps[i-1].cool_runtime
        else:
            last_heat_time = 0
            last_cool_time = 0
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime - last_heat_time,
                     'cool_time': temps[i].cool_runtime - last_cool_time})
    return render_template('index.html', data=data)
