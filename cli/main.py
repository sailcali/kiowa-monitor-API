from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import pandas as pd

load_dotenv()
def migrate_venstar_data(par_to_ras=False):
    parsec_db_string = os.environ.get("SQLALCHEMY_DATABASE_URI")
    ras_db_string = os.environ.get("SQLALCHEMY_REMOTE_DATABASE_URI")
    
    # Establish database connnections
    parsec_db = create_engine(parsec_db_string)
    ras_db = create_engine(ras_db_string)
    if not par_to_ras:
        start_data = pd.read_sql_table('temp_history', ras_db, index_col=['time'])
        start_data.to_sql('temp_history', parsec_db, if_exists='append')
    else:
        start_data = pd.read_sql_table('temp_history', parsec_db, index_col=['time'])
        start_data.to_sql('temp_history', ras_db, if_exists='append')
    print('Sucessfully Migrated!')


migrate_venstar_data()