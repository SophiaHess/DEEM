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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

from linkedin_scraper import actions
from linkedin_scraper.company import Company
from functions import parse_args, remove_linebreaks, ensure_lable_in_multiselect


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
    # CAUTION: download the latest version of the Google Chrome Driver before executing this step: https://getwebdriver.com/chromedriver
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    service = Service(executable_path=r"../'PUT THE PATH TO YOUR CHROMEDRIVER'/chromedriver.exe")
    driver = webdriver.Chrome(service=service)
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
                'startup_address_raw_linkedin'
                ,'startup_follower_linkedin']
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
        lambda x: (x[:99000] + '...') if len(x) > 100000 else x
    )

    ################################################################
    dataframe.to_csv(f'../output/{current_date.strftime("%Y%m%d")}_startup_linkedin_extraction.csv')
    ################################################################
