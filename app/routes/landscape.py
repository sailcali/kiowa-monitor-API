from flask import Blueprint, request, make_response
from app.landscape import landscape

landscape_bp = Blueprint('landscape_bp', __name__, url_prefix='/landscape')

@landscape_bp.route('/change-state', methods=['POST'])
def change_landscape_state():
    """Turns on/off landscape lighting based on state boolean in body
    This will call the change_landscape function, which will change the state
    and then call the api/record-landscape-change"""
    body = request.get_json()
    # delay_time = datetime.today() + timedelta(minutes=int(body["delay_time"]))
    new = landscape.change_landscape(body['state'])
    return make_response({'new_status': new}, 201)
