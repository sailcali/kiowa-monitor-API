from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import pandas as pd

load_dotenv()
def migrate_venstar_data():
    ras_db_string = os.environ.get("SQLALCHEMY_DATABASE_URI")
    other_db_string = os.environ.get("SQLALCHEMY_OTHER_DATABASE_URI")
    
    # Establish database connnections
    other_db = create_engine(other_db_string)
    ras_db = create_engine(ras_db_string)
    start_data = pd.read_sql_table('temp_history', other_db, index_col=['time'])
    start_data.to_sql('temp_history', ras_db, if_exists='append')
    print('Sucessfully Migrated!')


migrate_venstar_data()