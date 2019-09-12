import os
import sqlite3
from scipy.interpolate import interp1d
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pytz import timezone

from db_setup import weather_db_loc, airport_list_loc

# Get the original forecast
def get_fcst(airport_name, date_str = None, date_range_strs = None):
    # Connection to the database
    db = sqlite3.connect(weather_db_loc)
    c  = db.cursor()

    # Pull all dates
    if date_str is None and date_range_strs is None:
        # Forecast query 
        query_params = (airport_name,)        
        query = c.execute(        
            '''
            SELECT 
             pull_date
            ,forecast_time_stamps
            ,wind_speed_sustained
            ,probability_of_precipitation_floating
            ,temperature_hourly
            FROM weather_fcst
            WHERE airport_name = ?
            ORDER BY pull_date, forecast_time_stamps
            ''',
            query_params
        )

    # Pull a single date
    else:
        if date_str is not None:
            # date range to pull
            date_time = datetime.strptime(date_str, '%Y-%m-%d')
            first_pull_dt = (date_time + timedelta(days = 0)).strftime('%Y-%m-%d')
            last_pull_dt =  (date_time + timedelta(days = 1)).strftime('%Y-%m-%d')
        else:
            first_pull_dt = date_range_strs[0]
            last_pull_dt  = date_range_strs[1]
        
        # Forecast query
        query_params = (airport_name, first_pull_dt, last_pull_dt)        
        query = c.execute(        
            '''
            SELECT 
             pull_date
            ,forecast_time_stamps
            ,wind_speed_sustained
            ,probability_of_precipitation_floating
            ,temperature_hourly
            FROM weather_fcst
            WHERE airport_name = ?
              AND ? <= forecast_time_stamps
              AND forecast_time_stamps < ?
            ORDER BY pull_date, forecast_time_stamps
            ''',
            query_params
        )
    

    # Convert fcst query result to dataframe
    fcst_rows = query.fetchall()
    fcst_columns = [desc[0] for desc in c.description]    
    df_fcst = pd.DataFrame(fcst_rows, columns = fcst_columns)

    # Convert time stamp column to datetime
    df_fcst['forecast_time_stamps'] = pd.to_datetime(df_fcst['forecast_time_stamps'])
    
    return df_fcst



# Get the actual values
def get_actl(airport_name, date_str = None):
    # Connection to the database
    db = sqlite3.connect(weather_db_loc)
    c  = db.cursor()

    if date_str is None:
        # Actual query
        query_params = (airport_name,)        
        query = c.execute(        
            '''
            SELECT 
            datetime
            ,weather
            ,wind_speed
            ,precip_1_hour
            ,air_temp
            FROM weather_actl 
            WHERE airport_name = ?
            ORDER BY datetime
            ''',
            query_params
        )
    else:
        # date range to pull
        date_time = datetime.strptime(date_str, '%Y-%m-%d')
        first_pull_dt = (date_time + timedelta(days = 0)).strftime('%Y-%m-%d')
        last_pull_dt =  (date_time + timedelta(days = 1)).strftime('%Y-%m-%d')
        
        query_params = (airport_name, first_pull_dt, last_pull_dt)
        query = c.execute(        
            '''
            SELECT 
            datetime
            ,weather
            ,wind_speed
            ,precip_1_hour
            ,air_temp
            FROM weather_actl 
            WHERE airport_name = ?
              AND datetime >= ?
              AND datetime <  ? 
            ORDER BY datetime
            ''',
            query_params
        )
        

    # Convert actual query result to dataframe
    actl_rows = query.fetchall()
    actl_columns = [desc[0] for desc in c.description]    
    df_actl = pd.DataFrame(actl_rows, columns = actl_columns)

    # Convert datetime column to datetime
    df_actl['datetime'] = pd.to_datetime(df_actl['datetime'])    

    return df_actl


# Get the actual values
def get_actl_times(airport_name):
    # Connection to the database
    db = sqlite3.connect(weather_db_loc)
    c  = db.cursor()

    # Actual query
    query_params = (airport_name,)        
    query = c.execute(        
        '''
            SELECT 
             datetime
            FROM weather_actl 
            WHERE airport_name = ?
            ORDER BY datetime
        ''',
        query_params
    )

    # Convert actual query result to dataframe
    actl_rows = query.fetchall()
    actl_columns = [desc[0] for desc in c.description]    
    df_actl_times = pd.DataFrame(actl_rows, columns = actl_columns)

    # Convert datetime column to datetime
    df_actl_times['datetime'] = pd.to_datetime(df_actl_times['datetime'])    

    return df_actl_times


def get_fcst_interp(airport_name, date_str = None):
    df_actl_times = get_actl(airport_name, date_str)    
    df_fcst = get_fcst(airport_name, date_str = date_str)        
    
    # All of the unique actual times and forecast pull_dts
    all_actl_tms = pd.Series(df_actl_times.datetime.unique())
    all_pull_dts = pd.Series(df_fcst.pull_date.unique())
    
    all_interp_dfs = []
    
    for pull_dt in all_pull_dts:
        # Data frame for the current pull date
        df_curr_fcst = df_fcst.loc[df_fcst['pull_date'] == pull_dt, df_fcst.columns]
        df_curr_fcst.reindex()

        # must have at least 2 datapoints to interpolate
        try:
            nt, _ = df_curr_fcst.shape
        except:
            nt = 0
        
        if nt >= 2:        
            # Interpolation range
            t_min = df_curr_fcst['forecast_time_stamps'].min()
            t_max = df_curr_fcst['forecast_time_stamps'].max()

            # First applicable date of forecast
            t_fcst_min = datetime.strptime(pull_dt, '%Y-%m-%d').replace(tzinfo = t_min.tzinfo)
            
            df_curr_fcst['seconds_since_min'] = (df_curr_fcst['forecast_time_stamps'] - t_fcst_min)
            df_curr_fcst['seconds_since_min'] = df_curr_fcst['seconds_since_min'].apply(lambda t: t.total_seconds())
            
            # Actual times in seconds to interpolate at
            df_interp = pd.DataFrame({'datetime' : all_actl_tms})
            df_interp['t_fcst_min'] = t_fcst_min
            df_interp['time_delta'] = (df_interp['datetime'] - t_fcst_min)
            df_interp['interp_seconds'] = df_interp['time_delta'].apply(lambda x: x.total_seconds())
            df_interp['interp_day'    ] = df_interp['time_delta'].apply(lambda x: x.days)#/ (3600 * 24)
            df_interp['interp_hour'   ] = df_interp['datetime'  ].apply(lambda x: x.hour)
            df_interp = df_interp[(df_interp['datetime'] >= t_min) & (df_interp['datetime'] <= t_max)]
            df_interp.reindex()
            df_interp['pull_date'] = pull_dt
            
            # Interpolate temperature
            cs_temperature = interp1d(
                df_curr_fcst['seconds_since_min'], 
                df_curr_fcst['temperature_hourly'],
                fill_value="extrapolate"
            )
            df_interp['fcst_temperature'] = cs_temperature(df_interp['interp_seconds'])
            
            # Interpolate sustained wind speed
            cs_wind_speed = interp1d(
                df_curr_fcst['seconds_since_min'], 
                df_curr_fcst['wind_speed_sustained'],
                fill_value="extrapolate"
            )
            df_interp['fcst_wind_speed'] = cs_wind_speed(df_interp['interp_seconds'])
            
            # Interpolate probability of precipitation
            cs_precip = interp1d(
                df_curr_fcst['seconds_since_min'], 
                df_curr_fcst['probability_of_precipitation_floating'],
                fill_value="extrapolate"
            )
            df_interp['fcst_precip_prob'] = cs_wind_speed(df_interp['interp_seconds'])
            
            # Re-arrange
            df_interp = df_interp[['pull_date', 'datetime', 'interp_seconds', 'interp_day', 'interp_hour',
                                  'fcst_temperature', 'fcst_wind_speed', 'fcst_precip_prob']]
            
            all_interp_dfs.append(df_interp)

    # Append all together
    df_interp_all = pd.concat(all_interp_dfs)

    return df_interp_all


def get_avf_compare(airport_name, date_str = None):
    df_actl = get_actl(airport_name, date_str)
    df_fcst_interp = get_fcst_interp(airport_name, date_str)

    # Compare
    df_interp_compare = pd.merge(
        df_fcst_interp, 
        df_actl[['datetime', 'air_temp', 'wind_speed', 'precip_1_hour']], 
        on='datetime', 
        how='left'
    )
    
    #df_compare
    df_interp_compare['temp_delta'] = df_interp_compare['fcst_temperature'] - df_interp_compare['air_temp']
    df_interp_compare['wind_speed_delta'] = df_interp_compare['fcst_wind_speed'] - df_interp_compare['wind_speed']
    
    return df_interp_compare
    
def get_avf_heatmaps(airport_name):
    df_avf_compare = get_avf_compare(airport_name)
    
    temp_avf_heatmap_tbl = pd.pivot_table(
        df_avf_compare, 
        values='temp_delta',
        index=['interp_day'], 
        columns =['interp_hour'],
        aggfunc=np.mean
    )

    wind_avf_heatmap_tbl = pd.pivot_table(
        df_avf_compare, 
        values='wind_speed_delta',
        index=['interp_day'], 
        columns =['interp_hour'],
        aggfunc=np.mean
    )

    return temp_avf_heatmap_tbl, wind_avf_heatmap_tbl
