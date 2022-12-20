from tqdm import tqdm
import time
import numpy as np
import re
from geopy.geocoders import Nominatim


def get_geolocations_for_startups(startup_data, user_agent):
    """extracts geolocations from an addresses out of startup dataframe"""

    # register pandas functions for progress tracking
    tqdm.pandas()

    def get_geolocation_from_address(address):
        """extracts geolocation as latitude and longitude for a single address"""
        if address != '':
            #Todo get user_agent from config file
            geolocator = Nominatim(user_agent=user_agent, timeout=10)
            # send request with address
            geolocation = geolocator.geocode(address)
            # sleep for one second to avoid overloading the user_agent
            time.sleep(1)
            if geolocation is not None:
                return geolocation.latitude, geolocation.longitude
        return np.nan, np.nan

    def fill_address_from_columns(row):
        # Todo only take street, postal and city
        # remove NaN values so they dont get printed
        row.fillna('', inplace=True)
        # generate full address from street, postal and city
        address = f"{row['startup_street']}, {row['startup_postal']} {row['startup_city']}"
        # remove whitespaces if not all of street, postal and city where given
        address = re.sub(' +', ' ', address).strip(' ,')

        return address

    print('extracting geolocations:')
    # fill empty cells in headquarter address by combining postal, city and street from nuts extraction
    startup_data['startup_headquarter_address'] = startup_data.apply(fill_address_from_columns, axis=1)
    # extract geolocation for address
    startup_data['startup_latitude'], startup_data['startup_longitude'] = \
        zip(*startup_data['startup_headquarter_address'].progress_apply(get_geolocation_from_address))
    # change to string to avoid problems
    startup_data['startup_latitude'] = startup_data['startup_latitude'].fillna('').astype(str)
    startup_data['startup_longitude'] = startup_data['startup_longitude'].fillna('').astype(str)

    return startup_data
