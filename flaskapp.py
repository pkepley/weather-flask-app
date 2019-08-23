import os
from flask import (    
    Flask, render_template, escape,
    request, g, jsonify, url_for
)
import sqlite3
import pandas as pd

weather_db = '/var/www/html/flaskapp/db/weather.sqlite'
app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(weather_db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def airport_dropdown():
    airport_data = pd.read_csv('/var/www/html/flaskapp/data/airports.csv')
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

@app.route('/query', methods=['GET'])
def query():
    # Read the airport from the url
    af_type = request.args.get('af_type')
    airport = request.args.get('airport')

    if af_type is None:
        af_type = 'fcst'
    
    if airport is None:
        airport = 'KORD'        
        
    db = get_db()    
    c  = db.cursor()

    if af_type == 'fcst':
        query_params = (airport,)        
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

    elif af_type == 'actl':
        query_params = (airport,)        
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
        

    rows = query.fetchall()
    columns = [desc[0] for desc in c.description]
    result = []
    for row in rows:
        row = dict(zip(columns, row))
        result.append(row)

    return jsonify(result)

if __name__ == "__main__":
    app.run()
