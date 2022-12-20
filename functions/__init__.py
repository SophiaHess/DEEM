import argparse
import json
import re
import traceback
import pandas as pd
import numpy as np
from tqdm import tqdm

from pyairtable import Table
# allow for progress tracking in pandas apply function
tqdm.pandas()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Checking URL Status")

    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument('-f',
                          dest="config_file",
                          help="configfile to use. Should contain Airtable API Key, Base ID and source table name",
                          required=True)
    args = parser.parse_args()

    return args


def remove_linebreaks(string):
    """takes a string as input, removes linebreaks and unnecessary spaces and returns the cleaned string"""
    # replace line breaks in about_us text with space
    out = string.replace("\n", " ")
    # replace multiple spaces with single space and strip from start and end
    out = re.sub(' +', ' ', out).strip()
    return out


def _create_dataframe_from_at_return(r_list):
    data = []
    print('creating dataframe from results')
    for row in r_list:
        data.append(row['fields'])

    df = pd.DataFrame(data)
    return df


def airtable_to_dataframe(table_object, view, fields=None, max_records=None):
    """reads in specified airtable table with all or specified fields into a DataFrame"""
    # create Table request from config if no fields are specified
    print(f'Requesting data from airtable at {view}')
    if fields is None:
        if max_records is None:
            request = table_object.all(view=view)
        else:
            request = []
            for page in table_object.iterate(view=view, max_records=max_records):
                request = request + page
    else:
        if max_records is None:
            request = table_object.all(view=view, fields=fields)
        else:
            request = []
            for page in table_object.iterate(view=view, fields=fields, max_records=max_records):
                request = request + page

    df = _create_dataframe_from_at_return(request)

    return df


def dataframe_to_airtable_create(dataframe, table_object):
    """creates airtable records from dataframe and returns dataframe with uploaded records"""
    # replace nan with None to comply with json
    dataframe = dataframe.replace({np.nan: None})
    # creating list of dicts for each record in dataframe
    upload_dict = dataframe.to_dict(orient='records')
    print(f'{len(upload_dict)} records to create')

    # store empty list for all new records
    at_records = []
    # go through all records and save the resulting at record
    print('starting upload of records')
    for record in tqdm(upload_dict):
        try:
            at_record = table_object.create(record)
            at_records.append(at_record)
        except:
            print('failed uploading following record:')
            print(record)
            print('because of:')
            print(traceback.format_exc())
            print('\n\nreturning all records already uploaded')

    # create return dataframe with record_id and startup_id
    r_df = _create_dataframe_from_at_return(at_records)

    return r_df


def dataframe_to_airtable_update(dataframe, col_list, table_object):
    """creating new records with columns in col_list from dataframe to airtable and returning the df with record_ids"""
    # replace all nan with None to comply with json standard
    dataframe = dataframe.replace({np.nan: None})

    def create_dict_for_uploading_record(row):
        fields = {}
        for field in col_list:
            fields[field] = row[field]

        return {"id": row['record_id'],
                "fields": fields}

    updates = dataframe.apply(create_dict_for_uploading_record, axis=1).to_list()

    # uploading to airtable
    print('starting batch uploading')
    try:
        table_object.batch_update(updates)

        return True

    except Exception:
        print('upload to airtable failed')
        print('following problem occurred:')
        print(traceback.format_exc())

        return False


def json_to_dataframe(path):
    """function for reading in json files from extractions into a pandas dataframe"""

    with open(path) as file:
        j_data = json.load(file)
    # flatten json file along first dictionary and change columns to rows
    raw = pd.json_normalize(j_data).transpose()
    # create a row for each entry per founder and keep founder key as column 'index'
    raw = raw.explode(0).reset_index()
    # generate columns for keys in each entry
    values = pd.json_normalize(raw[0])
    # add index to values
    dataframe = pd.concat([raw['index'], values], axis=1)

    return dataframe

    
def get_dataframe_of_airtable_view(config, table_name_param, view_name_param, columns = None):

    #Get airtable dataframe of given table and view 
    table = Table(config.get('Airtable', 'at_api_key'),
                base_id=config.get('Airtable', 'at_base_id'),
                table_name=config.get('Airtable', table_name_param))
    raw_df = airtable_to_dataframe(table, config.get('Airtable', view_name_param))

    #If columns are supplied to the function, then return the dataframe with only those columns
    if columns:
        df = raw_df[columns]
        return df
    else:
        return raw_df

