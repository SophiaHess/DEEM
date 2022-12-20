import numpy as np
from tqdm import tqdm
import re
import requests
import warnings


def process_json_output(j):
    """takes the json from the netestate api as input and extracts address and social links"""
    # check if input actually is a response dict
    if type(j) is dict:
        # extract street, postalcode and city
        if not len(j['results']) == 0:  # check if any results where found
            try:
                street = j['results'][0]['street']
            except KeyError:
                street = np.nan
            try:
                postal = j['results'][0]['zip']
            except KeyError:
                postal = np.nan
            try:
                city = j['results'][0]['city']
            except KeyError:
                city = np.nan

        else:
            street, postal, city = np.nan, np.nan, np.nan

        # extract linkedin company profile from social links
        try:
            if not len(j['social_links']) == 0:  # check if social links where found
                regex = r"(?:https?:)?\/\/(?:[\w]+\.)?linkedin\.com\/(?:company|school)\/(?:[A-z0-9-À-ÿ\.]+)\/?"
                r = re.compile(regex) #compile regex to filter list for then take first element
                f_list = list(filter(r.match, j['social_links']))
                # get first element or nan if no linkedin company link was found
                social_link = next(iter(f_list or []), np.nan)
            else:
                social_link = np.nan
        except KeyError:
            social_link = np.nan
    else:
        street, postal, city, social_link = np.nan, np.nan, np.nan, np.nan

    return street, postal, city, social_link


def crawl_startups_imprint(startup_data, key):
    """takes the startup dataframe and the netestate key to return address and social links from imprint of startups """
    # allow for progress tracking in pandas apply function
    tqdm.pandas()

    def create_api_call(url):
        """creates api call from url and api key and returns json response"""
        # get hostname from url with regular expression
        regex = r"https?:\/\/"
        hostname = re.sub(regex, '', url)
        # create request string
        request = f'https://crawler.netestate.de/impressumscrawler/api.cgi?hostname={hostname}&accesskey={key}&format=json'
        # send request and return json response
        try:
            call = requests.get(request, timeout=15)
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

    # send requests to netestate only for available websites
    startup_data['imprint_response'] = startup_data.loc[
        (startup_data['startup_website_status'] != 'failed to connect') &
        (startup_data['startup_website'].notnull()), 'startup_website']\
        .progress_apply(create_api_call)
    # progress json outputs
    print('extracting address and linkedin from results')
    startup_data['startup_street'], \
        startup_data['startup_postal'], \
        startup_data['startup_city'], \
        startup_data['startup_linkedin_url'] = \
        zip(*startup_data['imprint_response'].apply(process_json_output))

    # change postal code to string to avoid problems
    startup_data['startup_postal'] = startup_data['startup_postal'].fillna('')
    startup_data['startup_postal'] = startup_data['startup_postal'].astype(str)

    return startup_data
