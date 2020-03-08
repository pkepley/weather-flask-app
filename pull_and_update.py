from db_setup import data_input_root, weather_db_loc, df_airports
from pull_weather import midnight_pull_and_save
from update_weather_db import *

midnight_pull_and_save(df_airports, out_root = data_input_root)
