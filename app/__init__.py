from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
load_dotenv()


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
    from app.models import VenstarTemp, LightingStatus, EnphaseProduction, FoodPlanner, Food
    
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

    app.register_blueprint(climate_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(landscape_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(food_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(lights_bp)
    
    return app


