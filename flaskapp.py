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
    airport = request.args.get('airport')
    limit   = request.args.get('limit')
    if airport is None:
        airport = 'KORD'        
    #if limit is None:
    #    limit = 10
        
    db = get_db()    
    c  = db.cursor()

    if limit is not None:
        query_params = (airport, limit)        
        query = c.execute(        
            '''
            SELECT 
            * 
            FROM weather_fcst 
            WHERE airport_name = ?
            ORDER BY pull_date, forecast_time_stamps
            LIMIT ?
            ''',
            query_params
        )
    else:
        query_params = (airport,)        
        query = c.execute(        
            '''
            SELECT 
            * 
            FROM weather_fcst 
            WHERE airport_name = ?
            ORDER BY pull_date, forecast_time_stamps
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
