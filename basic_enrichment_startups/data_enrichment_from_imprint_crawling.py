import configparser
import traceback
from pyairtable import Table
import time
import datetime
import os
import sys
from website_status_description import get_status_for_urls
from imprint_api import crawl_startups_imprint
from geolocation_extractor import get_geolocations_for_startups
import nuts_codes as nc
from functions import parse_args, airtable_to_dataframe, dataframe_to_airtable_update


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

if __name__ == '__main__':
    print('started at ', time.asctime())

    args = parse_args()
    # read config file
    config = configparser.ConfigParser()
    config.read(args.config_file)

    ################################################################
    # change: connect to your database
    # create startup dataframe 'startup_data' from your database
    # this is an example for an airtable database
    print('retrieving startup data from database and saving in dataframe')
    # necessary columns for this script
    load_cols = [
        'record_id',
        'startup_website'
    ]
    table = Table(config.get('Database', 'api_key'),
                  base_id=config.get('Database', 'base_id'),
                  table_name=config.get('Database', 'table_name'))
    startup_data = airtable_to_dataframe(table, config.get('Database', 'view'), fields=load_cols)
    ################################################################

    print('resulting dataframe:')
    print(startup_data.info())

    # create list that can be filled with columns that need to be updated in database
    update_cols = []

    # website url check
    try:
        print('--------------------')
        print('starting website url check:')
        startup_data = get_status_for_urls(startup_data)
        # add columns to update list
        update_cols.append('startup_website_status')
        update_cols.append('startup_alternative_website')
    except Exception:
        print('website check failed.')
        print('following problem occurred:')
        print(traceback.format_exc())

    # imprint crawling
    print('--------------------')
    try:
        print('starting imprint crawling:')
        startup_data = crawl_startups_imprint(startup_data, config.get('Imprint', 'imprint_key'))
        # add columns to update list
        update_cols.append('startup_street')
        update_cols.append('startup_postal')
        update_cols.append('startup_city')
        update_cols.append('startup_linkedin_url')
    except Exception:
        print('imprint crawling failed.')
        print('following problem occurred:')
        print(traceback.format_exc())

    # geolocation extraction
    print('--------------------')
    try:
        print('starting geolocation extraction:')
        startup_data = get_geolocations_for_startups(startup_data, config.get('Geolocation', 'user_agent'))
        # add columns to update list
        update_cols.append('startup_latitude')
        update_cols.append('startup_longitude')
    except Exception:
        print('geolocation extraction failed.')
        print('following problem occurred:')
        print(traceback.format_exc())

    # nuts3 code extraction
    print('--------------------')
    try:
        print('starting NUTS3 code extraction:')
        startup_data = nc.get_nuts3_code_from_addresses(startup_data)
        # add columns to update list
        update_cols.append('startup_nuts3_code')
    except Exception:
        print('nuts3 code extraction failed.')
        print('following problem occurred:')
        print(traceback.format_exc())

    ################################################################
    # change: connect to your database
    # update your database
    # example for an airtable database
    print('--------------------')
    print('starting upload to database:')
    # check will be true if upload was successfull
    check = dataframe_to_airtable_update(startup_data, update_cols, table)
    if check:
        print('upload finished successfully')
    else:
        print('upload to database failed.')
        print('saving dataframe as csv:')
        # get current date for file output
        current_date = datetime.date.today()
        startup_data.to_csv(f'./output/{current_date.strftime("%Y%m%d")}_data_enrichment_basic_output.csv')
    ################################################################
