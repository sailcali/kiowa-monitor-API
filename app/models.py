
from app import db

class VenstarTemp(db.Model):
    __tablename__ = 'temp_history'
    time = db.Column(db.DateTime, primary_key=True)
    local_temp = db.Column(db.SmallInteger)
    remote_temp = db.Column(db.SmallInteger, nullable=True)
    humidity = db.Column(db.SmallInteger, nullable=True)
    pi_temp = db.Column(db.SmallInteger, nullable=True)
    heat_runtime = db.Column(db.SmallInteger)
    cool_runtime = db.Column(db.SmallInteger)
    pressure = db.Column(db.Float)

class EnphaseProduction(db.Model):
    __tablename__ = 'enphase_production'
    time = db.Column(db.DateTime, primary_key=True)
    production = db.Column(db.SmallInteger)

class LightingStatus(db.Model):
    __tablename__ = 'lighting_status'
    time = db.Column(db.DateTime, primary_key=True)
    device = db.Column(db.Text)
    setting = db.Column(db.Boolean)
    time_on = db.Column(db.SmallInteger, nullable=True)

class FoodPlanner(db.Model):
    __tablename__ = 'food_planner'
    id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    date = db.Column(db.Date)
    meal_id = db.Column(db.SmallInteger, db.ForeignKey('meal_listing.id'), nullable=True)
    food_id = db.Column(db.SmallInteger, db.ForeignKey('common_food.id'), nullable=True)
    source = db.Column(db.Text)

class Food(db.Model):
    __tablename__ = 'common_food'
    id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    food = db.Column(db.Text)
    meals = db.relationship("FoodPlanner", backref="food")

class MealListing(db.Model):
    __tablename__ = 'meal_listing'
    id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    meal = db.Column(db.Text)
    meals = db.relationship("FoodPlanner", backref="meal_list")

class Bedtime(db.Model):
    __tablename__ = 'bedtime'
    id = db.Column(db.SmallInteger, primary_key=True, autoincrement=True)
    time = db.Column(db.DateTime)