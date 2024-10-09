from collections import defaultdict

import configparser
import os
import sys

import pandas as pd
import numpy as np
import re
import requests
import warnings
import ast
import json

from pyairtable import Table
from tqdm import tqdm
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from functions import airtable_to_dataframe, parse_args

from data_enrichment_from_imprint_crawling.airtable_urls.website_status_description import check_url_status

from helpers import get_domain_from_url, clean_founder_name
import time


def netestate_request(url, key):
    """creates api call from url and api key and returns json response"""
    # get hostname from url with regular expression
    regex = r"https?:\/\/"
    hostname = re.sub(regex, '', url)
    # create request string
    request = f'https://crawler.netestate.de/impressumscrawler/api.cgi?hostname={hostname}&accesskey={key}&format=json'
    # send request and return json response
    try:
        call = requests.get(request, timeout=60)
        response = call.json()
        # raise uncritical error if callsleft on api reach a limit of 500
        if int(response['callsleft']) < 500:
            warnings.warn('less than 500 netestate calls left.')
        return response
    except (requests.ConnectionError, requests.ConnectTimeout, requests.ReadTimeout, requests.Timeout) as error:
        print(error)
        return np.nan
    except requests.exceptions.JSONDecodeError:
        # return NaN for invalid responses
        return np.nan
    except KeyError:
        # happens if callsleft is missing from response. in this case it should just return the json response
        return response


def founder_netestate_imprint_search(row, founders_df, founder_create_dicts_list, startup_updates_dicts_list):

    
     # Create an empty dictionary for appending founder airtable fields for update
    startups_fields_dict = defaultdict(list)
    startup_record_id = row['record_id']

    
    raw_response = row['imprint_data_raw']

    if raw_response is None or raw_response != raw_response:
        return
    
    response = json.loads(raw_response)

    if response != response:
        return
    else:

        if 'social_links' in response.keys():
            startups_fields_dict['imprint_social_links'] = json.dumps(response['social_links'])
            
        if response['results'] != []:

            managers = response['results'][0]['managers']
                
            if len(managers) > 0:

                managers = pd.DataFrame(managers).drop_duplicates('fullname').to_dict('records')

                for manager in managers:
                    founders_fields_dict = {}
                    names = manager['fullname'].split()
                    founders_fields_dict['founder_first_name'] = names[0]
                    if len(names) > 0:
                        founders_fields_dict['founder_last_name'] = names[-1]

                    founders_fields_dict['founder_startups'] = [startup_record_id]
                    founder_create_dicts_list.append(founders_fields_dict)
                               
    startups_upload_dict = {"id":startup_record_id, 
            "fields":startups_fields_dict}
    startup_updates_dicts_list.append(startups_upload_dict)


if __name__ == '__main__':
    # parse arguments from command line
    args = parse_args()
    # read config file
    config = configparser.ConfigParser()
    config.read(args.config_file)

    # allow for progress tracking in pandas apply function
    tqdm.pandas()

    # create startup dataframe from airtable view
    print('retrieving startup and founders data from airtable and saving in dataframes')

    # ignore chained assignment warnings because of dataframe copy with relevant columns
    pd.options.mode.chained_assignment = None  # default='warn'

    founders_table = Table(config.get('Airtable', 'at_pat_token'),
                base_id=config.get('Airtable', 'at_base_id'),
                table_name=config.get('Founders', 'at_table_name'))



    snov_api_id = config.get('Snov', 'snov_api_id')
    snov_secret_id = config.get('Snov', 'snov_secret_id')

    # define columns that are needed in founders dataframe
    founders_col_list = ['founder_record_id', 'founder_linkedin_url', 'founder_startups', 'startup_name (from founder_startups)', 'startup_linkedin_url (from founder_startups)', 'startup_website (from founder_startups)', 'founder_first_name', 'founder_last_name']
    
    # get complete founders dataframe (we'll need to search the entire set for employees)
    founders_df = airtable_to_dataframe(founders_table, config.get('Founders', 'at_unfiltered_view'), fields=founders_col_list)



    startup_table = Table(config.get('Airtable', 'at_pat_token'),
                base_id=config.get('Airtable', 'at_base_id'),
                table_name=config.get('Airtable', 'at_startups_table_name'))
    
    # specify columns that are needed in startup dataframe
    startups_col_list = ['record_id', 'startup_linkedin_url', 'startup_name', 'employee_list_linkedin', 'startup_website']
    startups_df = airtable_to_dataframe(startup_table, config.get('LI_Startups', 'at_view_name'), fields=startups_col_list)




    founder_create_dicts_list = []
    startup_updates_dicts_list = []
    startups_df.progress_apply(lambda row: founder_netestate_imprint_search(row, founders_df, founder_create_dicts_list, startup_updates_dicts_list), axis=1, result_type='expand')

    
    print('\nUpdating Airtable with  Results ...')
    founders_table.batch_create(founder_create_dicts_list, typecast=True)
    startup_table.batch_update(startup_updates_dicts_list, typecast=True)
