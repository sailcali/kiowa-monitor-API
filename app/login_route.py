
from flask import Blueprint, redirect, url_for

login_bp = Blueprint('login_bp', __name__, url_prefix='/')

@login_bp.route("", methods=['GET'])
def login():
    return redirect(url_for('venstar_bp.kiowa_dashboard'))
