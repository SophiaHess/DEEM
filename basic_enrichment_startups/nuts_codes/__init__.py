import numpy as np
import pandas as pd
import os

#######################################
# change: link your postal/nuts correspondence file
# create relative path to correspondence csv from this file always
corr_path = os.path.join(os.path.dirname(__file__), 'pc2020_DE_NUTS-2021_v3.0.csv')
#######################################
# read in correspondence table from csv file
corr = pd.read_csv(corr_path, sep=';', dtype={'CODE': object})
# change postal code to string to avoid problems
corr['CODE'] = corr['CODE'].astype(str)


def get_nuts3(postal):
    """returns nuts3 code for a postal code"""
    # remove leading or tailing whitespaces to avoid false negatives
    postal = postal.strip()
    # search for postal code in correspondence table
    if not postal == '':
        corr_row = corr.loc[corr['CODE'] == postal]
        if corr_row.empty:
            return 'no german address'
        value = corr_row.iloc[0]['NUTS3']
        return value
    return np.nan


def get_nuts3_code_from_addresses(startup_data):
    """extracts nuts3 codes from postal codes out of the startup dataframe"""
    # add column with nuts3 code
    startup_data['startup_nuts3_code'] = startup_data['startup_postal'].apply(get_nuts3)
    print('nuts3 codes extracted')

    return startup_data
