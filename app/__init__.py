from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from flask_cors import CORS
from discordwebhook import Discord
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()

load_dotenv()

DISCORD_URL = os.environ.get("DISCORD_GENERAL_URL")
DISCORD = Discord(url=DISCORD_URL)

def create_app(test_config=None):
    app = Flask(__name__, static_folder='build', static_url_path='/')
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    CORS(app)
    
    # if test_config is None:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "SQLALCHEMY_DATABASE_URI")
    # else:
    #     app.config["TESTING"] = True
    #     app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    #         "SQLALCHEMY_TEST_DATABASE_URI")
    
    # Import models here for Alembic setup
    from app.models import VenstarTemp, LightingStatus, EnphaseProduction, FoodPlanner, Food, AllowedConnections
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register Blueprints here
    from .routes.api import api_bp
    from.routes.climate import climate_bp
    from .login_route import login_bp
    from .routes.landscape import landscape_bp
    from .routes.food import food_bp
    from .routes.weather import weather_bp
    from .routes.lights import lights_bp
    from .routes.solar import solar_bp
    from .routes.pool import pool_bp

    app.register_blueprint(climate_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(landscape_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(food_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(lights_bp)
    app.register_blueprint(solar_bp)
    app.register_blueprint(pool_bp)

    @app.before_request
    def check_user():
        """Run for each and every request - check user IP against database. If not in database - send IP to discord"""
        
        ip = None

        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            ip = request.environ['REMOTE_ADDR']
        else:
            ip = request.environ['HTTP_X_FORWARDED_FOR']

        row = AllowedConnections.query.filter(AllowedConnections.address==ip).first()
        if not row:
            DISCORD.post(content=f"New access from IP Address: {ip}")
            conn = AllowedConnections(address=ip, timestamp=int(datetime.now().timestamp()))
            db.session.add(conn)
            db.session.commit()

    return app


