import os, sys
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from db_setup import *

# Basic set-up
if len(sys.argv) > 1:
    actl_dt = sys.argv[1]
    tomm_dt = actl_dt

else:
    #data_input_root = '/home/ubuntu/flaskapp/data/'
    #db_dir  = '/home/ubuntu/flaskapp/db/'
    actl_dt  = '2019-11-01'
    tomm_dt  = '2019-11-02'

# Airport list
df_airport   = pd.read_csv(airport_list_loc)
airport_list = df_airport['icao_designation'].to_list()

# Set up the database for
sqlite_file = weather_db_loc
conn    = sqlite3.connect(sqlite_file)
cur     = conn.cursor()

columns = ['datetime', 'date', 'time', 'wind_raw', 'wind_dir', 'wind_speed',
           'gust_speed', 'visibility', 'weather', 'sky_conditions', 'air_temp',
           'dew_point', 'temp_6_hour_max', 'temp_6_hour_min', 'relative_humidity',
           'wind_chill', 'heat_index', 'pressure', 'pressure_mb', 'precip_1_hour',
           'precip_3_hour', 'precip_6_hour', 'airport_name']
    

# Load data for each airport
for airport in airport_list:    
    # Expected location for the airport's forecast
    airport_actl_path = os.path.join(
        data_input_root,
        airport,
        'nws_actual_{0}.csv'.format(tomm_dt)
    )

    # May have gzipped it
    if not os.path.exists(airport_actl_path):
        airport_actl_path = airport_actl_path + '.gz'

    # Check to see if the weather forecast table exists
    cur.execute('''
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
        AND name='weather_actl'
    ''')
    table_query_result = cur.fetchone()

    # If the table exists, see if the data has been loaded
    if table_query_result is not None:
        query_params = (airport, actl_dt, tomm_dt)
        cur.execute(
            '''
            SELECT * 
            FROM weather_actl 
            WHERE airport_name = ?
            AND datetime >= ?
            AND datetime <= ?
            ''',
            query_params
        )
        query_result = cur.fetchall()
    else:
        query_result = None

    # Data exists and nothing found on the table so far
    if os.path.exists(airport_actl_path) and (query_result is None or len(query_result) == 0):
        df_airport = pd.read_csv(airport_actl_path)
        df_airport['airport_name'] = airport

        for c in columns:
            if c not in df_airport.columns:
                df_airport[c] = np.nan
                
        df_airport = df_airport[columns]
        df_airport.to_sql('weather_actl', index=False, con = conn, if_exists='append')

    # Either the data did not exist, or the data has already been loaded
    else:
        # No data to load
        if not os.path.exists(airport_actl_path):
            print('No CSV data for {0} on {1}.'.format(airport, actl_dt))
            
        # Data already loaded
        if query_result is not None:
            print('Found {0} records for {1} on {2} in the database.'.format(
                len(query_result), airport, actl_dt)
            )
