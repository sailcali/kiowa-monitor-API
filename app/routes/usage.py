from flask import Blueprint, render_template
from app.models import VenstarTemp
from datetime import datetime, date

usage_bp = Blueprint('usage_bp', __name__, url_prefix='/usage')

@usage_bp.route("/today", methods=["GET"])
def display_usage_from_today():
    """Renders a table of today's usage data"""
    start_date = date.today()
    start_time = datetime.combine(start_date, datetime.min.time())

    temps = VenstarTemp.query.filter(VenstarTemp.time>start_time).order_by(VenstarTemp.time.desc()).all()
    data = {'data': []}
    for i in range(len(temps)):
        if i != len(temps)-1:
            last_heat_time = temps[i+1].heat_runtime
            last_cool_time = temps[i+1].cool_runtime
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
    return render_template('hvac-index.html', data=data)
