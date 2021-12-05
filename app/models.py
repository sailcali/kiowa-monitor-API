
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

class EnphaseProduction(db.Model):
    __tablename__ = 'enphase_production'
    time = db.Column(db.DateTime, primary_key=True)
    production = db.Column(db.SmallInteger)