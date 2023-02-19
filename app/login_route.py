
from flask import Blueprint, redirect, url_for, current_app

login_bp = Blueprint('login_bp', __name__, url_prefix='/')

@login_bp.route("", methods=['GET'])
def login():
    return current_app.send_static_file('index.html')
