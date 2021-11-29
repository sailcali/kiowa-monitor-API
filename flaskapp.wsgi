import sys 
sys.path.insert(0, '/var/www/kiowa-monitor-API')
from app import create_app
application = create_app()

