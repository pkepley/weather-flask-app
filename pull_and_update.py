from db_setup import data_input_root, weather_db_loc, df_airports
from pull_weather import midnight_pull_and_save, midnight_pull_df, midnight_time_zone
from datetime import datetime
from tzlocal import get_localzone
from update_weather_db import *

# What time is it now in our current timezone?
local_now_datetime = datetime.now(get_localzone())
print('Local now ({}) : {}'.format(get_localzone(), local_now_datetime))

# Update pull and save
midnight_pull_and_save(df_airports, out_root = data_input_root)

# Pull Date:
tz_to_run, pull_date_str = midnight_time_zone()
if pull_date_str is not None:
    pull_date_datetime = datetime.strptime(pull_date_str, '%Y-%m-%d')
    last_actl_datetime = pull_date_datetime + timedelta(days = -1)
    last_actl_date_str = last_actl_datetime.strftime('%Y-%m-%d')
else:
    last_actl_date_str = None

if tz_to_run is not None:
    # Connect to database
    db_conn = sqlite3.connect(weather_db_loc)
    
    # Update databases
    update_df, _ = midnight_pull_df(df_airports)
    update_list  = update_df['icao_designation'].to_list()
    update_all_db_from_disk(db_conn, data_input_root, df_airports,
                            update_list, last_actl_date_str)
