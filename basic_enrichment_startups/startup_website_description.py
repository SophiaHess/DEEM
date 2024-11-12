import configparser
import json
import sys
import datetime
import os
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import re
import urllib3
from urllib3.exceptions import InsecureRequestWarning


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


from functions import parse_args, translate_to_en

def scrape_website(url, error_file):
    try:
        # Send a GET request to the URL
        response = requests.get(url, verify=False)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            description_tag = soup.find('meta', attrs={'name': 'description'})
            website_description = description_tag.get('content') if description_tag else None

            return website_description

    except requests.RequestException as e:
        # print(f"Error: Unable to fetch the webpage ({e})")
        error_message = ({"url": url, "error": f"Unable to fetch the webpage ({e})"})
        json.dump(error_message, error_file, ensure_ascii=False, indent=4)
        return None


if __name__ == '__main__':
    # parse arguments from command line
    args = parse_args()
    # read config file
    config = configparser.ConfigParser()
    config.read(args.config_file)
    # allow for progress tracking in pandas apply function
    tqdm.pandas()

    # select only columns that are needed
    cols = ['record_id', 'startup_website', 'startup_description_web']

    # read from csv
    dataframe = pd.read_csv('./output/startup_data.csv')

    # ignore chained assignment warnings because of dataframe copy with relevant rows
    pd.options.mode.chained_assignment = None  # default='warn'

    # save current date for filename of error file
    current_date = datetime.now()
    # open file for error messages
    error_file_path = f'./output/{current_date.strftime("%Y%m%d")}_startups_errors.json'
    error_file = open(error_file_path, 'a', encoding='utf-8')

    # scrape each startup in dataframe
    print('scraping startups')
    urllib3.disable_warnings(InsecureRequestWarning)

    dataframe['startup_description_web'] = dataframe['startup_website'].apply(lambda x: pd.Series(scrape_website(x, error_file), dtype=object))

    # close error file
    error_file.close()
    def clean_text(text):
        # Remove unwanted characters (like '\n', '\xa0', '\t')
        text = re.sub(r'[\n\xa0\t]', ' ', text)

        # Remove extra whitespaces
        text = ' '.join(text.split())

        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s\.\,]', '', text)

        return text

    dataframe['startup_description_web'] = dataframe['startup_description_web'].astype(str)
    dataframe['startup_description_web'] = dataframe['startup_description_web'].apply(clean_text)
    dataframe.replace([' ', 'None', 'nan', '[]'], '', inplace=True)

    print('Translating...')
    dataframe['startup_description_web'] = dataframe['startup_description_web'].progress_apply(translate_to_en)

    dataframe.to_csv(f'./output/{current_date.strftime("%Y%m%d")}_startup_description_web.csv')
