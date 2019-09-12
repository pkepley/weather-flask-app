import os, sys
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from time import sleep

from db_setup import weather_db_loc, airport_list_loc
from forecast_tools import get_avf_compare, get_fcst, get_actl

# Basic set-up
if len(sys.argv) > 1:
    date_str = sys.argv[1]
else:
    date_str = '2019-08-13'

# Airport list
df_airport   = pd.read_csv(airport_list_loc)
airport_list = df_airport['icao_designation'].to_list()

# Set up the database for
sqlite_file = weather_db_loc
conn    = sqlite3.connect(sqlite_file)
cur     = conn.cursor()

columns = ['airport_name', 'pull_date', 'datetime', 'interp_seconds',
           'interp_day', 'interp_hour', 'fcst_temperature', 'fcst_wind_speed',
           'fcst_precip_prob', 'air_temp', 'wind_speed',
           'precip_1_hour', 'temp_delta', 'wind_speed_delta']

# Load data for each airport
for airport in airport_list:

    # Check to see if the weather forecast table exists
    cur.execute('''
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
        AND name='weather_avf_compare'
    ''')
    table_query_result = cur.fetchone()

    # If the table exists, see if the data has been loaded
    if table_query_result is not None:
        # date range to pull
        date_time = datetime.strptime(date_str, '%Y-%m-%d')
        first_pull_dt = (date_time + timedelta(days = 0)).strftime('%Y-%m-%d')
        last_pull_dt =  (date_time + timedelta(days = 1)).strftime('%Y-%m-%d')
        
        query_params = (airport, first_pull_dt, last_pull_dt)
        cur.execute(
            '''
            SELECT * 
            FROM weather_avf_compare 
            WHERE airport_name = ?
            AND datetime >= ?
            AND datetime <  ?
            ''',
            query_params
        )
        query_result = cur.fetchall()
    else:
        query_result = None

    try:
        na, _ = get_actl(airport, date_str).shape
        nf, _ = get_fcst(airport, date_range_strs = [first_pull_dt, last_pull_dt]).shape
        found_results = (na >= 2) and (nf >= 2)
        print(airport, date_str, na,nf,found_results)
    except:
        found_results = False
        
    # Data exists and nothing found on the table so far
    if (query_result is None or len(query_result) == 0) and found_results:
        try:
            df_avf_compare = get_avf_compare(airport, date_str)
            df_avf_compare['airport_name'] = airport
            
            for c in columns:
                if c not in df_avf_compare.columns:
                    df_avf_compare[c] = np.nan
                    
            df_avf_compare = df_avf_compare[columns]
            df_avf_compare.to_sql('weather_avf_compare', index=False, con = conn, if_exists='append')
            
        except:
            print('something went wrong with {0} for {1}'.format(airport, date_str))
            sleep(10)
            
    # Either the data did not exist, or the data has already been loaded
    else:
        # Data already loaded
        if query_result is not None:
            print('Found {0} records for {1} on {2} in the database.'.format(
                len(query_result), airport, date_str)
            )
