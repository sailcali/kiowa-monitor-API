
from flask import Blueprint, abort, render_template
from app.models import VenstarTemp
from datetime import datetime, timedelta, date

temps_bp = Blueprint('temps_bp', __name__, url_prefix='/temps')

@temps_bp.route("/<requested_date>", methods=["GET"])
def display_temps_by_date(requested_date):
    """Renders a table of temperatures from a given date"""
    try:
        start_date = datetime.strptime(requested_date, '%Y-%m-%d')
    except ValueError:
        try:
            start_date = datetime.strptime(requested_date, '%Y-%b-%d')
        except ValueError:
            abort(404)
    end_time = start_date + timedelta(days=1)
    temps = VenstarTemp.query.filter(VenstarTemp.time>start_date, VenstarTemp.time<end_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    if start_date < datetime.strptime('2021-12-05', '%Y-%m-%d'):
        for i in range(len(temps)):
        
            data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                        'local_temp': temps[i].local_temp,
                        'pi_temp': temps[i].pi_temp,
                        'remote_temp': temps[i].remote_temp,
                        'humidity': temps[i].humidity})
    else:
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

@temps_bp.route("/today", methods=["GET"])
def display_temps_from_today():
    """Renders a table of today's temperature data"""
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    for i in range(len(temps)):
        data['data'].append({'time': datetime.strftime(temps[i].time, '%Y-%b-%d %H:%M'),
                     'local_temp': temps[i].local_temp,
                     'pi_temp': temps[i].pi_temp,
                     'remote_temp': temps[i].remote_temp,
                     'humidity': temps[i].humidity,
                     'heat_time': temps[i].heat_runtime,
                     'cool_time': temps[i].cool_runtime})
    return render_template('index.html', data=data)
