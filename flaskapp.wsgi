import sys 
import os
from dotenv import load_dotenv
sys.path.insert(0, '/var/www/kiowa-monitor-API')
load_dotenv(dotenv_path="/var/www/kiowa-monitor-API/.env")
from app import create_app
application = create_app()

