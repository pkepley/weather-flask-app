import os, sys
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
from forecast_tools import get_avf_compare, get_fcst, get_actl
from pull_weather import midnight_pull_list

def check_table_exists(db_conn, table_name):
    # Cursor
    cur = db_conn.cursor()
    
    # Check to see if the weather forecast table exists
    cur.execute(
        '''
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
        AND name=?
        ''',
        (table_name,)
    )
    table_query_result = cur.fetchone()
    table_exists = table_query_result is not None

    return table_exists

def check_nws_actl_loaded(db_conn, airport_name, start_dt, end_dt = None):
    # default end date
    if end_dt is None:
        end_dt = datetime.strptime(start_dt, '%Y-%m-%d') + timedelta(days=1)
        end_dt = end_dt.strftime('%Y-%-m-%d')
        
    # Check if table exists
    actl_table_exists = check_table_exists(db_conn, 'weather_actl')
    
    # If the table exists, see if the data has been loaded
    if actl_table_exists:
        cur = db_conn.cursor()
        
        query_params = (airport_name, start_dt, end_dt)
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
        
        if query_result is not None and len(query_result) == 0:
            query_result = None
    else:
        query_result = None

    return query_result is not None

def update_nws_actl_db(db_conn, airport_name, df_nws_actl, actl_dt):    
    # db columns
    columns = ['datetime', 'date', 'time', 'wind_raw', 'wind_dir',
               'wind_speed', 'gust_speed', 'visibility', 'weather',
               'sky_conditions', 'air_temp', 'dew_point',
               'temp_6_hour_max', 'temp_6_hour_min',
               'relative_humidity', 'wind_chill', 'heat_index',
               'pressure', 'pressure_mb', 'precip_1_hour',
               'precip_3_hour', 'precip_6_hour', 'airport_name']

    # Check if data is loaded
    data_loaded = check_nws_actl_loaded(db_conn, airport_name, actl_dt)    

    # Load data if not present
    if data_loaded:
        print('Actl data found in db for {0} on {1}'.format(airport_name, actl_dt))
    else:
        print('Updating actl for {0} on {1}'.format(airport_name, actl_dt))        
        df_nws_actl['airport_name'] = airport_name

        for c in columns:
            if c not in df_nws_actl.columns:
                df_nws_actl[c] = np.nan

        # Ensure only listed columns are included ordered correctly                
        df_nws_actl = df_nws_actl[columns]

        # Load data
        df_nws_actl.to_sql('weather_actl', index=False, con = db_conn,
                           if_exists='append')
        
def check_nws_fcst_loaded(db_conn, airport_name, pull_dt):
    # Check if table exists
    fcst_table_exists = check_table_exists(db_conn, 'weather_fcst')
    
    # If the table exists, see if the data has been loaded
    if fcst_table_exists:
        cur = db_conn.cursor()
        
        query_params = (airport_name, pull_dt)
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
        
        if query_result is not None and len(query_result) == 0:
            query_result = None
    else:
        query_result = None

    return query_result is not None


def update_nws_fcst_db(db_conn, airport_name, df_nws_fcst, pull_dt):    
    # db columns
    columns = ['airport_name', 'pull_date', 'forecast_time_stamps',
               'temperature_dew_point', 'temperature_heat_index',
               'wind_speed_sustained', 'cloud_amount_total',
               'probability_of_precipitation_floating',
               'humidity_relative', 'direction_wind',
               'temperature_hourly', 'wind_speed_gust',
               'hourly_qpf_floating']

    # Check if data is loaded
    data_loaded = check_nws_fcst_loaded(db_conn, airport_name, pull_dt)    

    # Load data if not present
    if data_loaded:
        print('Fcst data found in db for {0} on {1}'.format(airport_name, pull_dt))
    else:
        print('Updating fcst for {0} on {1}'.format(airport_name, pull_dt))        
        
        df_nws_fcst['airport_name'] = airport_name

        for c in columns:
            if c not in df_nws_fcst.columns:
                df_nws_fcst[c] = np.nan

        # Ensure only listed columns are included ordered correctly
        df_nws_fcst = df_nws_fcst[columns]

        # Load data
        df_nws_fcst.to_sql('weather_fcst', index=False, con = db_conn,
                           if_exists='append')


def check_nws_avf_compare_loaded(db_conn, airport_name, fcst_date_str):
    # Check if table exists
    avf_table_exists = check_table_exists(db_conn, 'weather_avf_compare')
    
    # If the table exists, see if the data has been loaded
    if avf_table_exists:
        cur = db_conn.cursor()
        
        # Pull a single all snapshots records for this day's forecast:
        fcst_date_time = datetime.strptime(fcst_date_str, '%Y-%m-%d')
        next_date_str = (fcst_date_time + timedelta(days = 1)).strftime('%Y-%m-%d')
        
        query_params = (airport_name, fcst_date_str, next_date_str)
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
        
        if query_result is not None and len(query_result) == 0:
            query_result = None
    else:
        query_result = None

    return query_result is not None

def update_nws_avf_compare_db(db_conn, airport_name, fcst_date_str):
    # db columns    
    columns = ['airport_name', 'pull_date', 'datetime',
               'interp_seconds', 'interp_day', 'interp_hour',
               'fcst_temperature', 'fcst_wind_speed',
               'fcst_precip_prob', 'air_temp', 'wind_speed',
               'precip_1_hour', 'temp_delta', 'wind_speed_delta']

    # Check if data is loaded
    data_loaded = check_nws_avf_compare_loaded(db_conn, airport_name, fcst_date_str)    

    # Load data if not present
    if data_loaded:
        print('AvF data found in db for {0} on {1}'.format(airport_name, fcst_date_str))
    else:
        print('Updating AvF for {0} on {1}'.format(airport_name, fcst_date_str))
        
        try:
            df_avf_compare = get_avf_compare(airport_name, fcst_date_str)
            df_avf_compare['airport_name'] = airport_name

            
            for c in columns:
                if c not in df_avf_compare.columns:
                    df_avf_compare[c] = np.nan

            # Ensure only listed columns are included ordered correctly            
            df_avf_compare = df_avf_compare[columns]
        
            # Load data        
            df_avf_compare.to_sql('weather_avf_compare', index=False,
                                  con = db_conn, if_exists='append')

        except:
            print(('something went wrong loading avf compare ' + 
                   'for {0} for comparison date {1}'.format(airport_name, fcst_date_str)))

def update_actl_db_from_disk(db_conn, data_input_root, airport_list, actl_dt):
    # Load data for each airport
    for airport_name in airport_list:    
        # Expected location for the airport's forecast
        airport_actl_path = os.path.join(
            data_input_root,
            airport_name,
            'nws_actual_{0}.csv'.format(actl_dt)
        )

        # May have gzipped it
        if not os.path.exists(airport_actl_path):
            airport_actl_path = airport_actl_path + '.gz'

        # Update dB
        if os.path.exists(airport_actl_path):
            df_nws_actl = pd.read_csv(airport_actl_path)
            update_nws_actl_db(db_conn, airport_name, df_nws_actl, actl_dt)

def update_fcst_db_from_disk(db_conn, data_input_root, airport_list, pull_dt):
    # Load data for each airport
    for airport_name in airport_list:    
        # Expected location for the airport's forecast
        airport_fcst_path = os.path.join(
            data_input_root,
            airport_name,
            'nws_fcst_{0}.csv'.format(pull_dt)
        )

        # May have gzipped it
        if not os.path.exists(airport_fcst_path):
            airport_fcst_path = airport_fcst_path + '.gz'

        # Update dB
        if os.path.exists(airport_fcst_path):
            df_nws_fcst = pd.read_csv(airport_fcst_path)
            update_nws_fcst_db(db_conn, airport_name, df_nws_fcst, pull_dt)


def update_fcst_db_from_disk(db_conn, data_input_root, airport_list, pull_dt):
    # Load data for each airport
    for airport_name in airport_list:    
        # Expected location for the airport's forecast
        airport_fcst_path = os.path.join(
            data_input_root,
            airport_name,
            'nws_fcst_{0}.csv'.format(pull_dt)
        )

        # May have gzipped it
        if not os.path.exists(airport_fcst_path):
            airport_fcst_path = airport_fcst_path + '.gz'

        # Update dB
        if os.path.exists(airport_fcst_path):
            df_nws_fcst = pd.read_csv(airport_fcst_path)
            update_nws_fcst_db(db_conn, airport_name, df_nws_fcst, pull_dt)

def update_avf_db_from_list(db_conn, airport_list, fcst_date_str):
    for airport_name in airport_list:        
        update_nws_avf_compare_db(db_conn, airport_name, fcst_date_str)                            
