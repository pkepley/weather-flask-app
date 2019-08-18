import os, sys
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Basic set-up
if len(sys.argv) > 1:
    data_input_root = sys.argv[1]
    db_dir = sys.argv[2]    
    fcst_dt = sys.argv[3]
else:
    data_input_root = '/home/ubuntu/flaskapp/data/'
    db_dir  = '/home/ubuntu/flaskapp/db/'    
    fcst_dt  = '2019-08-13'

# Airport list
df_airport   = pd.read_csv(os.path.join(data_input_root, 'airports.csv'))
airport_list = df_airport['icao_designation'].to_list()

# Set up the database for
sqlite_file = os.path.join(db_dir, 'weather.sqlite')
conn    = sqlite3.connect(sqlite_file)
cur     = conn.cursor()

columns = ['airport_name', 'pull_date', 'forecast_time_stamps', 'temperature_dew_point',
           'temperature_heat_index', 'wind_speed_sustained', 'cloud_amount_total',
           'probability_of_precipitation_floating', 'humidity_relative', 'direction_wind',
           'temperature_hourly', 'wind_speed_gust', 'hourly_qpf_floating']

# Load data for each airport
for airport in airport_list:    
    # Expected location for the airport's forecast
    airport_fcst_path = os.path.join(
        data_input_root,
        airport,
        'nws_fcst_{0}.csv'.format(fcst_dt)
    )

    # Check to see if the weather forecast table exists
    cur.execute('''
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
        AND name='weather_fcst'
    ''')
    table_query_result = cur.fetchone()

    # If the table exists, see if the data has been loaded
    if table_query_result is not None:
        query_params = (airport, fcst_dt)
        cur.execute(
            '''
            SELECT * 
            FROM weather_fcst 
            WHERE airport_name = ?
            AND pull_date = ?
            ''',
            query_params
        )
        query_result = cur.fetchall()
    else:
        query_result = None

    # Data exists and nothing found on the table so far
    if os.path.exists(airport_fcst_path) and (query_result is None or len(query_result) == 0):
        df_airport = pd.read_csv(airport_fcst_path)
        df_airport['airport_name'] = airport
        for c in columns:
            if c not in df_airport.columns:
                df_airport[c] = np.nan
                
        df_airport = df_airport[columns]
        df_airport.to_sql('weather_fcst', index=False, con = conn, if_exists='append')

    # Either the data did not exist, or the data has already been loaded
    else:
        # No data to load
        if not os.path.exists(airport_fcst_path):
            print('No CSV data for {0} on {1}.'.format(airport, fcst_dt))
            
        # Data already loaded
        if query_result is not None:
            print('Found {0} records for {1} on {2} in the database.'.format(
                len(query_result), airport, fcst_dt)
            )
