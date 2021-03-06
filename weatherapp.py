import os
from flask import (    
    Flask, render_template, escape,
    request, g, jsonify, url_for,
    send_from_directory
)
import sqlite3
import pandas as pd
from forecast_tools import get_avf_heatmaps, get_fvf_heatmap_csv


from db_setup import weather_db_loc, airport_list_loc

import os

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(weather_db_loc)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/weather-app')
def airport_dropdown():
    airport_data = pd.read_csv(airport_list_loc)
    airport = airport_data['icao_designation'].values
    city    = airport_data['city'].values
    state   = airport_data['state'].values    
    
    return render_template(
        'index.html',
        airport=airport,
        city=city,
        state=state,
        selected_airport="KORD"
    )

@app.route('/weather-app/query', methods=['GET'])
def query():
    # Read the airport from the url
    af_type = request.args.get('af_type')
    airport = request.args.get('airport')
    start_date_str = request.args.get('start_date_str')
    end_date_str   = request.args.get('end_date_str')    

    print(start_date_str, end_date_str)
    
    if af_type is None:
        af_type = 'fcst'
    
    if airport is None:
        airport = 'KORD'        
        
    db = get_db()    
    c  = db.cursor()

    if af_type in ('fcst','forecast'):
        query_params = (airport, start_date_str, end_date_str)        
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
              AND forecast_time_stamps >= ?
              AND forecast_time_stamps <= ?
            ORDER BY pull_date, forecast_time_stamps
            ''',
            query_params
        )

    elif af_type in ('actl','actual'):
        query_params = (airport, start_date_str, end_date_str)        
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
              AND datetime <= ?
            ORDER BY datetime
            ''',
            query_params
        )
        

    rows = query.fetchall()
    columns = [desc[0] for desc in c.description]
    result = []
    for row in rows:
        row = dict(zip(columns, row))
        result.append(row)

    return jsonify(result)


@app.route('/weather-app/avf_heatmap', methods=['GET'])
def get_avf_heatmap():
    airport = request.args.get('airport')    
    temp_heatmap_tbl, _ = get_avf_heatmaps(airport)

    # Data labels
    columns   = list(temp_heatmap_tbl.columns)
    row_names = list(temp_heatmap_tbl.index)

    # Convert the table to csv
    temp_heatmap_str = temp_heatmap_tbl.to_csv(index=False)

    return temp_heatmap_str


@app.route('/weather-app/fvf_heatmap', methods=['GET'])
def get_fvf_heatmap():
    airport = request.args.get('airport')    
    fvf_heatmap_flat_csv = get_fvf_heatmap_csv(airport)
    
    return fvf_heatmap_flat_csv

@app.route('/weather-app/static/<path:path>', methods=['GET'])
def get_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    app.run(host='0.0.0.0')

