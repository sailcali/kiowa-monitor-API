from flask import Blueprint, make_response, request
import sqlalchemy
from app import db
from app.models import EnphaseProduction, SDAccess
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

API_PASSWORD = os.environ.get("API_PASSWORD")

solar_bp = Blueprint('solar_bp', __name__, url_prefix='/solar')

@solar_bp.route('/production/<requested_date>', methods=['GET', 'POST'])
def get_set_daily_solar_production(requested_date):
    """Sets daily production values if POST, returns daily production values"""
    
    if request.method == "POST":
        # Get data from client
        data = request.get_json()
        # Update the database and commit
        db.session.bulk_insert_mappings(EnphaseProduction, data['days_production'])
        db.session.commit()

    # Whether GET or SET, we will return the subject day's data
    # Requested date is start date (midnight is assumed)
    start_date = datetime.strptime(requested_date, '%Y-%m-%d')
    # End date is just tomorrow
    end_date = start_date + timedelta(days=1)
    
    # Get all production figures starting today, and prior to tomorrow
    all_production = EnphaseProduction.query \
        .filter(sqlalchemy.and_(sqlalchemy.func.date(EnphaseProduction.time) >= start_date), \
        sqlalchemy.func.date(EnphaseProduction.time) < end_date).all()
    
    # Cleanse and populate data into a list of dictionaries
    response_data = []
    for row in all_production:
        response_data.append({'time': datetime.strftime(row.time,'%Y-%m-%d %H:%M'), 'production': row.production})
    return make_response({"days_production": response_data}, 200)

@solar_bp.route("/access", methods=['GET', "POST"])
def get_set_solar_keys():
    """GET and SET API keys for Enphase. Requires own API password"""
    # Correct password is required in the header to ensure the request is coming from the backend!
    client_password = request.headers.get("password")
    if client_password == API_PASSWORD:
        # We need the request data either way
        keys = request.get_json()
        
        if request.method == "POST":
            # Check to see if the user code exists already
            current_access = SDAccess.query.filter(SDAccess.user == keys["user"]).first()
            if current_access:
                # If so, we will adjust the existing tokens and commit
                current_access.acdate = keys["date"]
                current_access.rfdate = keys["date"]
                current_access.at = keys["at"]
                current_access.rt = keys["rt"]
                db.session.commit()
            else:
                # If it does not exist, we will create a new record for the user code
                new_access = SDAccess(user=keys["user"], 
                                      acdate=keys["date"], 
                                      rfdate=keys["date"],
                                      at=keys["at"],
                                      rt=keys["rt"])
                db.session.add(new_access)
                db.session.commit()
            # For the POST method, return OK, created
            return make_response({"Result": "OK"}, 201)
        elif request.method == "GET":
            # For GET we will simply get the tokens for the specified user code and return it formatted
            current_access = SDAccess.query.filter(SDAccess.user == keys["user"]).first()
            data = {"rt":current_access.rt, "at": current_access.at, "date": current_access.rfdate}
            return make_response({'keys': data}, 200)

@solar_bp.route('/production/last-update', methods=['GET'])
def get_last_solar_production():
    """Returns the date of the last production update"""
    last_record = EnphaseProduction.query.order_by(EnphaseProduction.time.desc()).first()
    return make_response({"last_entry": last_record.time}, 200)

@solar_bp.route('/production/lifetime', methods=['GET'])
def get_all_solar_production():
    """Returns the total lifetime production value (sum) of the enphase system"""
    all_production = db.session.query(sqlalchemy.func.sum(EnphaseProduction.production)).first()
    return make_response({"total_production": all_production[0]}, 200)

@solar_bp.route('/production/period-sum', methods=['GET'])
def get_period_solar_production_sum():
    """Returns the production sum for a period of time sent in the request body"""
    request_body = request.get_json()
    all_production = db.session.query(sqlalchemy.func.sum(EnphaseProduction.production)) \
        .filter(sqlalchemy.and_(sqlalchemy.func.date(EnphaseProduction.time) >= request_body['start_date']), \
        sqlalchemy.func.date(EnphaseProduction.time) <= request_body['end_date']).first()
    return make_response({"period_production": all_production[0], "start_date": request_body['start_date'], "end_date": request_body['end_date']}, 200)

@solar_bp.route('/production/period-data', methods=['GET'])
def get_period_solar_production_data():
    """Returns all production data for a period of time sent in the request body"""
    request_body = request.get_json()
    all_production = EnphaseProduction.query \
        .filter(sqlalchemy.and_(sqlalchemy.func.date(EnphaseProduction.time) >= request_body['start_date']), \
        sqlalchemy.func.date(EnphaseProduction.time) <= request_body['end_date']).all()
    response_data = []
    for row in all_production:
        response_data.append({'time': row.time, 'production': row.production})
    return make_response({'Results': response_data}, 200)