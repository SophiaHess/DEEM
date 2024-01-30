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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))


from linkedin_scraper import actions
from linkedin_scraper.company import Company
from functions import dataframe_to_airtable_update, parse_args, remove_linebreaks, airtable_to_dataframe, ensure_lable_in_multiselect


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
            "startup_linkedin": link,
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
    if config.get('LI_Startups', 'input_file').split('.')[-1] == 'csv':
        df_raw = pd.read_csv(config.get('LI_Startups', 'input_file'))  # header=1 header is needed if column names are not in first row
    elif config.get('LI_Startups', 'input_file').split('.')[-1] == 'xlsx':
        df_raw = pd.read_excel(config.get('LI_Startups', 'input_file'))
    else:
        print('unknown file type of input file.')
        sys.exit()

    # table = Table(config.get('Airtable', 'at_pat_token'),
    #               base_id=config.get('Airtable', 'at_base_id'),
    #               table_name=config.get('LI_Startups', 'at_table_name'))
    # # select only columns that are needed
    # cols = ['startup_name', 'record_id', 'startup_linkedin_url', 'startup_website_merged', 'data_source', 'website_from_linkedin', 'validation_linkedin']
    # # get data from airtable Todo
    # df_raw = airtable_to_dataframe(table, 'for_update_processing', cols)


    # fill startup_website_merged with website from airtable if empty
    df_raw['startup_website_merged'] = df_raw['startup_website_merged'].fillna(df_raw['website_from_linkedin'])
    # define which company profiles are correct and should be processed
    validated = ['Passed', 'Corrected']
    df_raw['process'] = df_raw.apply(lambda x: True if x['validation_linkedin'] in validated else False, axis=1)
    # only keep entries that should be processed in new dataframe
    dataframe = df_raw.loc[df_raw['process']]
    # dataframe = dataframe.iloc[:3]
    # ignore chained assignment warnings because of dataframe copy with relevant rows
    pd.options.mode.chained_assignment = None  # default='warn'

    # save current date for filename of error file
    current_date = datetime.date.today()
    # open file for error messages
    error_file_path = f'../output/{current_date.strftime("%Y%m%d")}_startups_errors.json'
    error_file = open(error_file_path, 'a', encoding='utf-8')

    # code to exclude chromedriver warnings
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('log-level=3')

    # start cromedriver and login to Linkedin
    service = Service(executable_path=r"../../chromedriver/chromedriver.exe")
    driver = webdriver.Chrome(service=service)
    #driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    actions.login(driver, email=config.get('Linkedin', 'li_user'), password=config.get('Linkedin', 'li_pass'))

    # scrape each startup in dataframe
    print('scraping startups')
    col_list = ['main_university_employees_linkedin',
                'n_employees_linkedin',
                'founding_year_linkedin',
                'company_size_linkedin',
                'industry_linkedin',
                'about_us_linkedin',
                'employee_list_linkedin',
                'startup_address_raw_linkedin']
    dataframe[col_list] = dataframe.progress_apply(
        lambda x: use_linkedin_scraper(x, driver, error_file, return_columns=col_list), axis=1, result_type='expand')

    # close error file and quit driver
    error_file.close()
    driver.quit()

    # set data source to linkedin
    dataframe['data_source'] = dataframe['data_source'].fillna(value='[]')
    dataframe['data_source'] = dataframe['data_source'].apply(
        lambda x: literal_eval(x) + ['linkedin'])

    # dataframe['data_source'] = dataframe['data_source'].apply(lambda x: ensure_lable_in_multiselect(x, 'linkedin'))

    # correct datatype of founding year
    dataframe['founding_year_linkedin'] = dataframe['founding_year_linkedin'].astype('Int64')
    dataframe['founding_year_linkedin'] = dataframe['founding_year_linkedin'].apply(lambda x: str(x) if pd.notna(x) else x)
    # convert employee list to string and truncate at char limit for upload to airtable
    dataframe['employee_list_linkedin'] = dataframe['employee_list_linkedin'].astype('str')
    dataframe['employee_list_linkedin'] = dataframe['employee_list_linkedin'].apply(
        lambda x: (x[:99997] + '...') if len(x) > 100000 else x
    )

    ################################################################
    dataframe.to_csv(f'../output/{current_date.strftime("%Y%m%d")}_startup_linkedin_extraction.csv')
    ################################################################
    # change: connect to your database
    # this is an example for airtable
    # uploading results do airtable
    print('file completed. preparing for airtable upload')
    print('uploading scraping results...')
    table = Table(config.get('Airtable', 'at_pat_token'),
                  base_id=config.get('Airtable', 'at_base_id'),
                  table_name=config.get('LI_Startups', 'at_table_name'))
    cols_upload = col_list + ['validation_linkedin', 'startup_linkedin_url', 'data_source', 'startup_website_merged', 'website_from_linkedin']

    check = dataframe_to_airtable_update(dataframe, cols_upload, table)
    if check:
        print('scraping upload successfull')
    else:
        print('upload to airtable failed')
        print('saving dataframe as csv:')
        dataframe.to_csv(f'../output/{current_date.strftime("%Y%m%d")}_startup_linkedin_extraction.csv', mode='a')

    # uploading hand check labels for all that are not passed
    print('uploading failed check labels...')
    check_failed = df_raw.loc[~df_raw['process']]
    check = dataframe_to_airtable_update(check_failed, ['validation_linkedin'], table)
    if check:
        print('uploading failed check labels successful')
    else:
        print('uploading failed check labels failed!')

    dataframe.to_csv(f'../output/{current_date.strftime("%Y%m%d")}_startup_linkedin_extraction.csv')
    # check_failed.to_csv(f'../output/{current_date.strftime("%Y%m%d")}_check_failed.csv')
    ################################################################
