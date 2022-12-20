import configparser
import json
import sys
import datetime
import os
import time
import traceback
import numpy as np
import pandas as pd
from ast import literal_eval
from tqdm import tqdm
from pyairtable import Table
from linkedin_scraper import Company, actions
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from functions import dataframe_to_airtable_update, parse_args, remove_linebreaks


def use_linkedin_scraper(row, driver, error_file, return_columns):
    link = row['startup_linkedin_url']
    record_id = row['record_id']
    name = row['startup_name']
    try:
        startup = Company(link, record_id=record_id, driver=driver, close_on_complete=False)
        output = json.loads(repr(startup))

        # replace line breaks in about_us text with space
        if output['about_us_linkedin'] is not None:
            output['about_us_linkedin'] = remove_linebreaks(output['about_us_linkedin'])

        # build list for return containing all specified columns
        out = []
        for col in return_columns:
            out.append(output[col])

        time.sleep(3)

        return out

    except Exception as e:
        print(f" Problem with {record_id} - {name} --> {e}")
        case = {
            "record_id": record_id,
            "starup_name": name,
            "error_message": traceback.format_exc()
        }
        json.dump(case, error_file, ensure_ascii=False, indent=4)

        # build same size output list filled with nan
        out = [np.nan for col in return_columns]

        return out


if __name__ == '__main__':
    # parse arguments from command line
    args = parse_args()
    # read config file
    config = configparser.ConfigParser()
    config.read(args.config_file)
    # allow for progress tracking in pandas apply function
    tqdm.pandas()

    # read in csv to dataframe
    df_raw = pd.read_csv(config.get('Scrape', 'csv_input'), sep=';')  # header=1 header is needed if column names are not in first row
    # define which company profiles are correct and should be processed
    validated = ['Passed', 'Corrected']
    df_raw['process'] = df_raw.apply(lambda x: True if x['linkedin_validation'] in validated else False, axis=1)
    # only keep entries that should be processed in new dataframe
    dataframe = df_raw.loc[df_raw['process']]
    # ignore chained assignment warnings because of dataframe copy with relevant rows
    pd.options.mode.chained_assignment = None  # default='warn'

    # save current date for filename of error file
    current_date = datetime.date.today()
    # open file for error messages
    error_file_path = f'./output/{current_date.strftime("%Y%m%d")}_errors.json'
    error_file = open(error_file_path, 'a', encoding='utf-8')

    # code to exclude chromedriver warnings
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('log-level=3')

    # start cromedriver and login to Linkedin
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    actions.login(driver, email=config.get('Linkedin', 'li_user'), password=config.get('Linkedin', 'li_pass'))

    # scrape each startup in new dataframe
    print('scraping startups')
    col_list = ['main_university_employees_linkedin',
                'n_linkedin_employees',
                'founding_year_linkedin',
                'company_size_linkedin',
                'industry_linkedin',
                'about_us_linkedin',
                'employee_list_linkedin']
    dataframe[col_list] = dataframe.progress_apply(
        lambda x: use_linkedin_scraper(x, driver, error_file, return_columns=col_list), axis=1, result_type='expand')
    # correct datatype of founding year
    dataframe.loc[dataframe['founding_year_linkedin'].notna(), 'founding_year_linkedin'] = \
        dataframe.loc[dataframe['founding_year_linkedin'].notna(), 'founding_year_linkedin'].astype('int')

    ################################################################
    # change: connect to your database
    # this is an example for airtable
    # uploading results do airtable
    print('file completed. preparing for airtable upload')
    print('uploading scraping results...')
    table = Table(config.get('Airtable', 'at_api_key'),
                  base_id=config.get('Airtable', 'at_base_id'),
                  table_name=config.get('Airtable', 'at_table_name'))
    cols_upload = col_list + ['linkedin_validation', 'startup_linkedin_url']
    check = dataframe_to_airtable_update(dataframe, cols_upload, table)
    if check:
        print('scraping upload successfull')
    else:
        print('upload to airtable failed')
        print('saving dataframe as csv:')
        dataframe.to_csv(f'./output/{current_date.strftime("%Y%m%d")}_linkedin_extraction.csv', mode='a')

    # uploading hand check labels for all that are not passed
    print('uploading failed check labels...')
    check_failed = df_raw.loc[~df_raw['process']]
    check = dataframe_to_airtable_update(check_failed, ['linkedin_validation'], table)
    if check:
        print('uploading failed check labels successful')
    else:
        print('uploading failed check labels failed!')

    error_file.close()
    driver.quit()
