from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from flask_apscheduler import APScheduler
# from app.landscape import landscape


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

    scheduler = APScheduler()
    
    # Import models here for Alembic setup
    from app.models import VenstarTemp, LightingStatus, EnphaseProduction, FoodPlanner, Food
    
    db.init_app(app)
    migrate.init_app(app, db)
    scheduler.api_enabled = True
    scheduler.init_app(app)

    from app.landscape import landscape
    scheduler.add_job(id = 'Scheduled Task', func=landscape.change_landscape, trigger="interval", seconds=60)
    scheduler.start()
    
    
    # Register Blueprints here
    from .routes import temps_bp, venstar_bp, login_bp, usage_bp, landscape_bp, api_bp, food_bp
    app.register_blueprint(temps_bp)
    app.register_blueprint(venstar_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(usage_bp)
    app.register_blueprint(landscape_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(food_bp)
    


    return app


