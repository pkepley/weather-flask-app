import os
import sqlite3
from scipy.interpolate import interp1d
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pytz import timezone

from db_setup import weather_db_loc, airport_list_loc

UTC = timezone('UTC')

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
            last_pull_dt =  (date_time + timedelta(days = 2)).strftime('%Y-%m-%d')
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
            nt_f, _ = df_curr_fcst.shape
            nt_a, _ = df_actl_times.shape
        except:
            nt_f = 0
            nt_a = 0
        
        if nt_f >= 2 and nt_a > 0:        
            # Interpolation range
            t_min = df_curr_fcst['forecast_time_stamps'].min()
            t_min_orig_tzinfo = t_min.tzinfo
            t_min = t_min.astimezone(UTC)
            t_max = df_curr_fcst['forecast_time_stamps'].max().astimezone(UTC)

            # First applicable date of forecast
            t_fcst_min = datetime.strptime(pull_dt, '%Y-%m-%d').replace(tzinfo = t_min_orig_tzinfo).astimezone(UTC)

            df_curr_fcst['seconds_since_min'] = (df_curr_fcst['forecast_time_stamps'].apply(lambda t: t.astimezone(UTC)) - t_fcst_min)
            df_curr_fcst['seconds_since_min'] = df_curr_fcst['seconds_since_min'].apply(lambda t: t.total_seconds())
            
            # Actual times in seconds to interpolate at
            df_interp = pd.DataFrame({'datetime' : all_actl_tms})
            df_interp['t_fcst_min'] = t_fcst_min
            df_interp['time_delta'] = (df_interp['datetime'].apply(lambda t: t.astimezone(UTC)) - t_fcst_min)
            df_interp['interp_seconds'] = df_interp['time_delta'].apply(lambda x: x.total_seconds())
            df_interp['interp_day'    ] = df_interp['time_delta'].apply(lambda x: x.days)#/ (3600 * 24)
            df_interp['interp_hour'   ] = df_interp['datetime'  ].apply(lambda x: x.hour)
            df_interp = df_interp[(df_interp['datetime'].apply(lambda t: t.astimezone(UTC)) >= t_min) &
                                  (df_interp['datetime'].apply(lambda t: t.astimezone(UTC)) <= t_max)]
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
    if all_interp_dfs:
        df_interp_all = pd.concat(all_interp_dfs)
    else:
        df_interp_all = pd.DataFrame({
            'pull_date' : [],  'datetime' : [],
            'interp_seconds' : [], 'interp_day' : [],
            'interp_hour' : [],  'fcst_temperature' : [],
            'fcst_wind_speed' : [], 'fcst_precip_prob':[]
        })
        df_interp_all['datetime'] = pd.to_datetime(df_interp_all['datetime'])

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
    db = sqlite3.connect(weather_db_loc)
    c  = db.cursor()
    
    query_params = (airport_name,)        
    query = c.execute(        
        '''
        SELECT 
        interp_day
        ,interp_hour
        ,avg(temp_delta) as avg_temp_delta
        ,avg(wind_speed_delta) as avg_wind_speed_delta
        FROM weather_avf_compare
        WHERE airport_name = ?
          AND interp_day >= 0
        GROUP BY interp_day, interp_hour
        ORDER BY interp_day, interp_hour
        ''',
        query_params
    )
    fcst_rows = query.fetchall()
    fcst_columns = [desc[0] for desc in c.description]    
    df_pivot_flat = pd.DataFrame(fcst_rows, columns = fcst_columns)

    temp_avf_heatmap_tbl = df_pivot_flat.pivot(
        index = 'interp_day',
        columns = 'interp_hour',
        values='avg_temp_delta'
    )
    
    wind_avf_heatmap_tbl = df_pivot_flat.pivot(
        index = 'interp_day',
        columns = 'interp_hour',
        values='avg_wind_speed_delta'
    )
    
    return temp_avf_heatmap_tbl, wind_avf_heatmap_tbl


def get_fvf_heatmap_tbl(airport_name):
    db = sqlite3.connect(weather_db_loc)
    c  = db.cursor()
    
    query_params = (airport_name,)        
    query = c.execute(            
        '''
        select
           cast(julianday(f1.forecast_time_stamps) - julianday(f1.pull_date || " 00:00:00-" || substr(f1.forecast_time_stamps, 21)) as integer) as day_of_snp1
          ,cast(julianday(f2.forecast_time_stamps) - julianday(f2.pull_date || " 00:00:00-" || substr(f2.forecast_time_stamps, 21)) as integer) as day_of_snp2
          ,cast(substr(f2.forecast_time_stamps, 12, 2) as int) as fcst_hour
          ,avg(f2.temperature_hourly - f1.temperature_hourly) as avg_temp_delta
          ,avg(f2.probability_of_precipitation_floating - f1.probability_of_precipitation_floating) as avg_prob_precip_delta
          ,avg(f2.wind_speed_sustained - f1.wind_speed_sustained) as avg_wind_speed_delta
          ,count(*) as cnt_snp2_v_snp1
        from weather_fcst as f1
        left join weather_fcst as f2
        on f1.forecast_time_stamps = f2.forecast_time_stamps
        and f1.airport_name = f2.airport_name
        where f1.airport_name = ?
        and f2.pull_date > f1.pull_date
        group by day_of_snp1, day_of_snp2, fcst_hour
        order by day_of_snp1, day_of_snp2, fcst_hour
        ''',
        query_params
    )
    fcst_rows = query.fetchall()
    fcst_columns = [desc[0] for desc in c.description]    
    df_pivot_flat = pd.DataFrame(fcst_rows, columns = fcst_columns)

    return df_pivot_flat

def get_fvf_heatmap_csv(airport_name):
    df_pivot_flat = get_fvf_heatmap_tbl(airport_name)
    
    return df_pivot_flat.to_csv(index=False)

def get_fvf_heatmap_array(airport_name):
    df_pivot_flat = get_fvf_heatmap_tbl(airport_name)

    temp_fvf_heatmap_tbl = df_pivot_flat.pivot_table(
        index   = ['day_of_snp2', 'day_of_snp1'],
        columns = ['fcst_hour'],
        values  = 'avg_temp_delta'
    )

    prob_precip_fvf_heatmap_tbl = df_pivot_flat.pivot_table(
        index   = ['day_of_snp2', 'day_of_snp1'],
        columns = ['fcst_hour'],
        values  = 'avg_prob_precip_delta'
    )

    wind_speed_fvf_heatmap_tbl = df_pivot_flat.pivot_table(
        index   = ['day_of_snp2', 'day_of_snp1'],
        columns = ['fcst_hour'],
        values  = 'avg_wind_speed_delta'
    )

    return temp_fvf_heatmap_tbl, wind_speed_fvf_heatmap_tbl, prob_precip_fvf_heatmap_tbl
