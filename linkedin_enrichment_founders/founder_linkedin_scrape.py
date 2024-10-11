from collections import abc
import configparser
import datetime
import os
import sys
import pandas as pd
import numpy as np
from pyairtable import Table, utils
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

from linkedin_enrichment_startups.linkedin_scraper.person import Person
import linkedin_enrichment_startups.linkedin_scraper.actions as actions
from functions import parse_args, airtable_update_single_record
from founders.helpers import clean_linkedin_url, get_combined_name

def start_chrome_driver():
    """
    Initialises chrome objectfor reading and scraping

    args:
        None
    returns:
        WebDriver: chrome driver object
    """

    # code to exclude chromedriver warnings
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('log-level=3')
    
    service = Service()
    # start chromedriver and log in to linkedin
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def create_error_file():
    """
    Create error file for outputting exceptions

    args:
        None
    returns:
        file object: open writable error file
    """
    # save current date for filename of error file
    current_date = datetime.date.today()
    # open file for error messages
    error_file_path = f'./output/{current_date.strftime("%Y%m%d")}_founder_scraping_errors.json'
    error_file = open(error_file_path, 'a', encoding='utf-8')
    

    return error_file


def scrape_founder(founders_table, row, driver, error_file=None):
    """

    args:
    row (dataframe row): a single founder record, providing the url to be scraped
    driver (WebDriver object): driver object 
    error_file (file object, optional): writable file for outputting exceptions
    
    returns:
    
    """
    
    # Get link of person to scrape
    link = row['founder_linkedin_url']
    link = clean_linkedin_url(link)
    
    if isinstance(link, float):
        return None

    # Get record id of person being scraped, used after scraping to upload the scraped data back into airtable
    record_id = row['founder_record_id']
    
    # Scraping Object is initialised and run
    founder = Person(linkedin_url=link, name = get_combined_name(row["founder_first_name"], row["founder_last_name"]) , driver=driver, close_on_complete=False, error_file=error_file, record_id=record_id, add_delays=False)
    

    
    # Initialise empty dictionary, scraped information is stored in this dictionary
    upload_dict = {}
    
    # Check if the scraping was successful, if not then return False and don't upload anything. 
    # The error has been outputted to the error file in the Person class
    if founder.scraping_successful == False:

        upload_dict['scraped_founder_linkedin_url'] = 'Scraping Unsuccessful'
    else:
        
        # Convert the scraped list of Experience dataclass into a dataframe with each attribute as a column in the dataframe
        experiences_df = pd.DataFrame([t.__dict__ for t in founder.experiences])
        # Replace NaN values in the dataframe with None (to be able to upload json into airtable)
        experiences_df = experiences_df.replace({np.nan: None})
        # Convert dataframe to json representation, to be stored in airtable and so it is able to be read back in.
        upload_dict['scraped_experience'] = experiences_df.to_json()

        # Similarly, convert the scraped list of Education dataclass into a dataframe with each object attribute parsed into columns in the dataframe.
        educations_df = pd.DataFrame([t.__dict__ for t in founder.educations])
        # Replace NaN values in the dataframe with None
        educations_df = educations_df.replace({np.nan: None})
        # Convert dataframe to json representation, to be stored in airtable and so it is able to be read back in.
        upload_dict['scraped_education'] = educations_df.to_json()

        upload_dict['scraped_about'] = founder.about

        upload_dict['scraped_location'] = founder.location

        upload_dict['scraped_founder_linkedin_url'] = link

        # Check if skills were scraped; if not, set entry to "None Given", otherwise enter the raw list
        if len(founder.skills) == 0:
            upload_dict['scraped_skills'] = "None given"
        else:
            upload_dict['scraped_skills'] = founder.skills

        # Check if certifications were scraped; if not, set entry to "None Given", otherwise enter as json
        if len(founder.certifications) == 0:
            upload_dict['scraped_certs'] = "None given"
        else:
            upload_dict['scraped_certs'] = pd.DataFrame(founder.certifications).to_json()

        # Check if honors were scraped; if not, set entry to "None Given", otherwise enter as json
        if len(founder.honors) == 0:
            upload_dict['scraped_honors'] = "None given"
        else:
            upload_dict['scraped_honors'] = pd.DataFrame(founder.honors).to_json()

        # Check if volunteer_experiences were scraped; if not, set entry to "None Given", otherwise enter as json
        if len(founder.volunteer_experiences) == 0:
            upload_dict['scraped_volunt_exp'] = "None given"
        else:
            upload_dict['scraped_volunt_exp'] = pd.DataFrame(founder.volunteer_experiences).to_json()

    # Get today's date to enter as date of scraping
    upload_dict['scraped_date_last_scraped_linkedin'] = datetime.date.isoformat(datetime.date.today())
    

    # Update single row of the airtable, with the raw scraped data now stored in upload_dict
    # We upload the scraped data record by record so that if there any unpredictable failures during scraping
    # then we don't lose any previous information if we were to do it at the end of scraping
    airtable_update_single_record(founders_table, record_id, upload_dict)



if __name__ == '__main__':
    # parse arguments from command line
    args = parse_args()
    # read config file
    config = configparser.ConfigParser()
    config.read(args.config_file)

    # allow for progress tracking in pandas apply function
    tqdm.pandas()

    # ignore chained assignment warnings because of dataframe copy with relevant columns
    pd.options.mode.chained_assignment = None  # default='warn'

    founders_table = Table(config.get('Airtable', 'at_pat_token'),
                base_id=config.get('Airtable', 'at_base_id'),
                table_name=config.get('Founders', 'at_table_name'))
    
    # define columns that are needed in founders dataframe
    founders_col_list = ['founder_record_id', 'founder_linkedin_url', 'founder_startups', 'startup_name (from founder_startups)', 'startup_linkedin_url (from founder_startups)', 'founder_first_name', 'founder_last_name']
    
    # get complete founders dataframe (we'll need to search the entire set for employees)
    # import csv with the founders_col_list columns
    to_scrape_founders_df = pd.read_csv("./output/founders_search.csv")

    
    driver = start_chrome_driver() 
    actions.login(driver, email=config.get('Linkedin', 'li_user'), password=config.get('Linkedin', 'li_pass'))

    error_file = create_error_file()


    to_scrape_founders_df.progress_apply( 
        lambda row: scrape_founder(founders_table, row, driver, error_file), axis=1, result_type='expand')

    error_file.close()

    driver.quit()
