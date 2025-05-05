import argparse
import json
import re
import traceback
import pandas as pd
import numpy as np
import datetime
from tqdm import tqdm

from pyairtable import Table
# allow for progress tracking in pandas apply function
tqdm.pandas()

from googletrans import Translator


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


def read_config_file(config_file):
    """Read configuration file"""

    conf = {}
    with open(config_file) as file:
        for line in file:
            line = line.strip()
            if len(line) != 0 and line[0] != "#":
                parameter, value = line.strip().split('=', 1)
                # build dict with parameter and value
                conf[parameter] = value.strip(" '")
    return conf


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


def dataframe_to_airtable_create(dataframe, table_object, ret_failed=False, typecast=False):
    """creates airtable records from dataframe and returns dataframe with uploaded records"""
    # exit if passed dataframe is empty
    if dataframe.empty:
        print('no records to create')
        if ret_failed:
            return dataframe, dataframe
        else:
            return dataframe

    # replace nan with None to comply with json
    dataframe = dataframe.replace({np.nan: None})
    # remove record_id column if passed
    if 'record_id' in dataframe.columns:
        dataframe = dataframe.drop('record_id', axis=1)
    # creating list of dicts for each record in dataframe
    upload_dict = dataframe.to_dict(orient='records')
    print(f'{len(upload_dict)} records to create')

    # store empty list for all new records
    at_records = []
    failed_records = []
    # go through all records and save the resulting at record
    print('starting upload of records')
    for record in tqdm(upload_dict):
        try:
            at_record = table_object.create(record, typecast)
            at_records.append(at_record)
        except:
            print('failed uploading following record:')
            print(record)
            print('because of:')
            print(traceback.format_exc())
            failed_records.append(record)

    # create return dataframe with record_id and startup_id
    up_df = _create_dataframe_from_at_return(at_records)
    failed_df = pd.DataFrame.from_dict(failed_records)

    if ret_failed:
        return up_df, failed_df
    else:
        return up_df


def dataframe_to_airtable_update(dataframe, col_list, table_object, only_filled=False, typecast=False):
    """creating new records with columns in col_list from dataframe to airtable and returning the df with record_ids"""
    # check if dataframe is empty
    if dataframe.empty:
        print('--> no records to update!')
        return True
    # remove record_id from col_list in case it was passed
    if 'record_id' in col_list:
        col_list.remove('record_id')

    # replace all nan with None to comply with json standard
    dataframe = dataframe.replace({np.nan: None})

    def create_dict_for_uploading_record(row):
        fields = {}
        if only_filled:
            for field in col_list:
                if row[field] is not None:
                    fields[field] = row[field]
        else:
            for field in col_list:
                fields[field] = row[field]

        return {"id": row['record_id'],
                "fields": fields}

    try:
        updates = dataframe.apply(create_dict_for_uploading_record, axis=1).to_list()
    except AttributeError:
        # if no updates where generated
        print('no updates to upload')
        return True

    # uploading to airtable
    print('starting batch uploading')
    try:
        table_object.batch_update(updates, typecast=typecast)

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


def airtable_update_single_record(table_object, record_id, upload_dict):

    try:
        table_object.update(record_id, upload_dict, replace=False, typecast=True)
    except:
        print(f"Updating {record_id} failed")


def cap_sentence(s):
    return re.sub("(^|\s)(\S)", lambda m: m.group(1) + m.group(2).upper(), s)

def get_collapsed_ranges(ranges):
    ranges = iter(sorted(ranges))
    current_range = next(ranges)
    for start, end in ranges:
        if start > current_range[1]:
            yield current_range
            current_range = [start, end]
        elif end > current_range[1]:
            current_range[1] = end
    yield current_range


def in_dictlist(key, value, my_dictlist):
    for entry in my_dictlist:
        if entry[key] == value:
            return entry
    return {}


def separate_name_legal_state(string):
    """function that takes company name as string, extracts the legal state and returns name and legal state as tuple"""
    if string == '':
        return None, None
    expr = re.compile(r'(?i)(^.+?)(\b(?:g?gmbh|tgu|ug|gbr|ag|inc|ohg|kg|ltd)\b.*)?$')
    name, legal_state = expr.match(string).group(1, 2)
    try:
        name = name.strip()
        legal_state = legal_state.strip()
    except AttributeError:
        # happens if one capture group is empty
        pass

    return name, legal_state


def get_host_name_from_url(url):
    regex_host = re.compile(r'^(?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^:\/?\n]+)')
    try:
        host_name = regex_host.match(str(url)).group(1)
    except AttributeError:
        # happens if url was empty
        return np.NaN
    return host_name.strip()


class InvalidUrlException(Exception):
    """raised if an Url that is not a LinkedIn company profile is passed"""
    pass


def find_updates(source_df, at_df, update_tracking, id_col):
    """detects changes between source_df and at_df and returns update entrys for update table as dataframe"""
    # ensure both dataframes only contain update_tracking columns
    source_df = source_df[list(update_tracking.keys()) + [id_col, 'record_id']]
    at_df = at_df[list(update_tracking.keys()) + [id_col, 'record_id']]
    # set id_col as index
    source_df = source_df.set_index(id_col, drop=False).sort_index()
    at_df = at_df.set_index(id_col, drop=False).sort_index()
    # ensure that both dataframes have same length
    if len(at_df) != len(source_df):
        source_ids = source_df[id_col].tolist()
        at_ids = at_df[id_col].tolist()
        if len(source_ids) > len(at_ids):
            diff = list(set(source_ids) - set(at_ids))
        else:
            diff = list(set(at_ids) - set(source_ids))
        raise ValueError(
            f'Dataframes are not the same length\n'
            f'length source dataframe: {len(source_df)}\n'
            f'length airtable dataframe: {len(at_df)}\n'
            f'following ids are missing in one dataframe: {diff}'
        )
    # comparing new values with current values in airtable
    comp = at_df[update_tracking.keys()].compare(source_df[update_tracking.keys()], keep_shape=True)
    # drop rows without any changes
    comp = comp.dropna(axis=0, how='all')
    # add startup_ID to comp dataframe by dataframe index
    comp = comp.join(source_df['record_id'], how='left')

    # generate update table entries for each case in comp
    updates = {
        'message': [],
        'timestamp': [],
        'startup': [],
        'update_type': []
    }

    def _generate_update_entry(row):
        # go through columns in update tracking and see if there were changes
        for case, type in update_tracking.items():
            if pd.notna(row[case, 'self']):
                updates['message'].append(str({'old': row[case, "self"], 'new': row[case, "other"]}))
                updates['timestamp'].append(datetime.datetime.isoformat(datetime.datetime.today()))
                updates['startup'].append([row['record_id']])
                updates['update_type'].append(type)
            else:
                continue

    comp.apply(_generate_update_entry, axis=1)

    # generate updates dataframe from dictionary
    df_updates = pd.DataFrame(updates)

    return df_updates


def re_pat_word_in_list(words, base=str(r"(?i).*\b({})\b.*")):
    
    words = [re.escape(word) for word in words]

    return base.format(str('|').join(words))


def translate_to_en(untranslated_text):
    try:
        translator = Translator()
        translated = translator.translate(untranslated_text)
        return translated.text
    except:
        return "Translation Failed"


def ensure_lable_in_multiselect(lst, label):
    """takes current labels in form of a list and label that needs to be present as input and returns a list with all new multiselect options"""
    if lst is np.NaN:
        # in case of new datapoints there is no list for data_source --> empty list to be filled in next step
        lst = []
    if label in lst:
        return lst
    else:
        lst.append(label)
        return lst
