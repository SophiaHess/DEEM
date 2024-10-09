import configparser
import datetime
import os
import sys
import traceback

import numpy as np
import pandas as pd
from tqdm import tqdm

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

from linkedin_scraper.linkedin_functions_company import linkedin_company_website_check, clean_linkedin_url_company
from linkedin_scraper.company import get_website_from_linkedin
from linkedin_scraper import actions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

if __name__ == '__main__':
    # parse arguments from command line
    args = parse_args()
    # read config file
    config = configparser.ConfigParser()
    config.read(args.config_file)

    # allow for progress tracking in pandas apply function
    tqdm.pandas()

    ################################################################
    # input data from csv with the columns
    # OR: connect to your database:
    # select only columns that are needed
    col_list = ['startup_name', 'record_id', 'startup_linkedin_url', 'startup_website_merged', 'data_source']
    
    # import csv with the col_list columns
    # dataframe = pd.read_csv("../output/linkedin_search.csv")
    # ensure dataframe has all necessary columns
    for column in col_list:
        if column not in dataframe.columns:
            dataframe[column] = np.nan
    ################################################################

    # code to exclude chromedriver warnings
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('log-level=3')

    # start chrome driver
    print('starting chrome driver')

    # CAUTION: download the latest version of the Google Chrome Driver before executing this step: https://getwebdriver.com/chromedriver
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    service = Service(executable_path=r"../'PUT THE PATH TO YOUR CHROMEDRIVER'/chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    try:
        # login on linkedin
        actions.login(driver, email=config.get('Linkedin', 'li_user'), password=config.get('Linkedin', 'li_pass'))

        # search for all startups without linkedin url
        print('search for missing linkedin urls')
        dataframe.loc[(dataframe['startup_linkedin_url'].isna()), 'startup_linkedin_url'] = \
            dataframe.loc[(dataframe['startup_linkedin_url'].isna())].progress_apply(
            lambda x: actions.search_for_company(x['startup_name'], driver), axis=1)
        # clean found linkedin urls
        print('cleaning linkedin urls')
        dataframe.loc[(dataframe['startup_linkedin_url'].notna()), 'startup_linkedin_url'] = \
            dataframe.loc[(dataframe['startup_linkedin_url'].notna())].progress_apply(
                lambda x: clean_linkedin_url_company(x['startup_linkedin_url']), axis=1)

        # find websites for all startups with linkedin urls
        print('get websites from found linkedin profiles')
        dataframe.loc[(dataframe['startup_linkedin_url'].notna()), 'website_from_linkedin'] = \
            dataframe.loc[(dataframe['startup_linkedin_url'].notna())].progress_apply(
            lambda x: get_website_from_linkedin(x['startup_linkedin_url'], driver), axis=1)
    except:
        print(traceback.format_exc())

    # quit chromedriver
    driver.quit()

    # perform check between website from database and the one found on linkedin
    print('perform website check')
    dataframe['validation_linkedin'] = dataframe.progress_apply(linkedin_company_website_check, axis=1)

    # save output to csv file
    current_date = datetime.date.today()
    path = f'../output/{current_date.strftime("%Y%m%d")}_linkedin_company_search_results.csv'
    print(f'saving csv file at {path}')
    dataframe.to_csv(f'../output/{current_date.strftime("%Y%m%d")}_linkedin_company_search_results.csv')
