from flask import Blueprint, request, make_response
from datetime import timedelta, datetime
from app.landscape import landscape

landscape_bp = Blueprint('landscape_bp', __name__, url_prefix='/landscape')

@landscape_bp.route('/change-state', methods=['POST'])
def change_landscape_state():
    body = request.get_json()
    delay_time = datetime.today() + timedelta(minutes=int(body["delay_time"]))
    new = landscape.change_landscape(body['state'], delay_time)
    return make_response({'new_status': new, 'new_delay': delay_time}, 201)
