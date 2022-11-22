from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

db = SQLAlchemy()
migrate = Migrate()
load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
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
    from .routes.temps import temps_bp
    from .routes.api import api_bp
    from.routes.venstar import venstar_bp
    from .login_route import login_bp
    from .routes.usage import usage_bp
    from .routes.landscape import landscape_bp
    from .routes.api import api_bp
    from .routes.food import food_bp
    from .routes.weather import weather_bp

    app.register_blueprint(temps_bp)
    app.register_blueprint(venstar_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(usage_bp)
    app.register_blueprint(landscape_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(food_bp)
    app.register_blueprint(weather_bp)
    
    return app


