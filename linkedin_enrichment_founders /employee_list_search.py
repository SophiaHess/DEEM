from collections import abc, defaultdict
import configparser
import re
import os
import sys
import datetime

import pandas as pd
import numpy as np
import time
import json
import ast 

from pyairtable import Table
from tqdm import tqdm

from fuzzywuzzy import fuzz, process

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from functions import airtable_to_dataframe, parse_args
from founders.helpers import clean_linkedin_url, clean_founder_name, clean_company_name
from exceptions import NoAssignedStartupException, NoEmployeeListException, InvalidEmployeeListException
import nominals

def find_founder_name_match_in_employee_list(row, founder_update_dicts_list):

    """
    This function finds the closest employee match in the startups_df employee list from a row in the airtable founders table

    The function appends the result of the founder-in-employee-list check to a fields dictionary for upload back into airtable
    args:
    row (dataframe row): a row from the founder airtable table

    returns: None

    """
    try:

        fields_dict = defaultdict(list)
        record_id = row['founder_record_id']

        founder_first_name = row['founder_first_name']
        founder_last_name = row['founder_last_name']

        #get the lists of first names and last names
        first_name_list = clean_founder_name(founder_first_name)
        last_name_list = clean_founder_name(founder_last_name)

        
        # Create a cleaned combined name string (without titles)
        # combined_name is without middle names i.e. 'Sara Julia Prof. Dr. Jen' becomes 'Sara Jen'
        combined_name = first_name_list[0] + ' ' + ' '.join(last_name_list)
        # combined_full_name is with middle names
        combined_full_name = ' '.join(first_name_list) + ' ' + ' '.join(last_name_list)

        #No assigned startup for the founder in the airtable
        urls_equal = np.nan
        founder_url = np.nan

        startup_name_list = row["startup_name (from founder_startups)"]
        startup_linkedin_url_list = row["startup_linkedin_url (from founder_startups)"]
        raw_employee_data_lists = row["employee_list_linkedin"]

        if row["founder_startups"] != row["founder_startups"]:
            fields_dict['validation_employee_list'] = "no_assigned_startup"
            raise NoAssignedStartupException()

        if raw_employee_data_lists == [] or raw_employee_data_lists != raw_employee_data_lists:
            fields_dict['validation_employee_list'] = "no_employee_list"
            raise NoEmployeeListException()

        if not pd.isnull(row['founder_linkedin_url']):
            founder_url = clean_linkedin_url(row['founder_linkedin_url'], get_just_id=False)


        # We do a couple of steps of converting the raw json repr. into a json, then filtering out bad values
        employee_lists = [ast.literal_eval(j_data) for j_data in raw_employee_data_lists if j_data != 'nan']
        employee_lists = [cleaned for sublist in employee_lists
            if (cleaned := [elem for elem in sublist if elem is not None])]


        if len(employee_lists) == 0:
            fields_dict['validation_employee_list'] = "invalid_or_empty_employee_list"
            raise InvalidEmployeeListException()            

        for employee_list in employee_lists:
            
            #Convert list of employee json to one dataframe
            employee_list_df = pd.json_normalize(employee_list)

            #Check if empty dataframe, if so then 
            if employee_list_df.empty:
                fields_dict['validation_employee_list'] = "invalid_or_empty_employee_list"
                raise InvalidEmployeeListException()

            employee_list_df = employee_list_df[~employee_list_df["name"].isnull()]
            employee_list_df = employee_list_df.drop_duplicates()


            #Find the closest name match using fuzzy matching of the founder's name in the employee list
            #Combined_name is the person's name from airtable
            #employee_list_df["name"] is a series of all the names in the json
            #extract returns a list of tuples of the name of the matchees, the match scores (/100), and the index of the founder matches in employee_list_df
            num_matches_to_capture = 1
            matches_pool = process.extract(combined_name, employee_list_df['name'], scorer=fuzz.WRatio, limit=num_matches_to_capture)
            matches_pool_full_name = process.extract(combined_full_name, employee_list_df['name'], scorer=fuzz.WRatio, limit=num_matches_to_capture)


            # We now have a list of the top matches. we obtain a filterered json dataframe with only the top matches
            matches_pool_df = employee_list_df.loc[[x[2] for x in matches_pool],:]
            matches_pool_full_name_df = employee_list_df.loc[[x[2] for x in matches_pool_full_name],:]

            #add the name matching score to the filtered dataframe for each possible match (in a new column called "name_ratio")
            matches_pool_df['name_ratio'] = [x[1] for x in matches_pool]
            matches_pool_full_name_df['name_ratio'] = [x[1] for x in matches_pool_full_name]

            matches = pd.concat([matches_pool_df, matches_pool_full_name_df], axis=0, ignore_index=True, sort=False)

            #take the match with the max name ratio
            best_match = matches[matches['name_ratio'] == matches['name_ratio'].max()]

            #pick the first best match (might need to handle what to do when there are two matches with an equal score, although this seems unlikely)
            best_match = best_match.iloc[0]
            match_name = best_match['name']
            match_score = round(best_match['name_ratio'], 2)

            matched_url = clean_linkedin_url(best_match['linkedin_url'], get_just_id=False)
            
            urls_equal = False
            if not founder_url != founder_url:
                urls_equal = (founder_url == matched_url)

            if match_score >=95 or urls_equal:
                fields_dict['validation_employee_list'].append("excellent")
            elif match_score >= 85 and match_score < 95:
                fields_dict['validation_employee_list'].append("good")
            elif match_score >= 75 and match_score < 85:
                fields_dict['validation_employee_list'].append("fair")
            elif match_score >= 65 and match_score < 75:
                fields_dict['validation_employee_list'].append("poor")
            elif match_score < 65:
                fields_dict['validation_employee_list'].append("no_match")



            fields_dict['founder_designation'].append(best_match['designation'])
            fields_dict['employee_list_match_score'].append(str(match_score))
            fields_dict['founder_linkedin_url_in_employee_list'].append(matched_url)


        fields_dict['founder_designation'] = json.dumps(fields_dict['founder_designation']) if len(fields_dict['founder_designation']) > 1 else fields_dict['founder_designation'][0]
        fields_dict['employee_list_match_score'] = json.dumps(fields_dict['employee_list_match_score']) if len(fields_dict['employee_list_match_score']) > 1 else fields_dict['employee_list_match_score'][0]
        fields_dict['founder_linkedin_url_in_employee_list'] = json.dumps(fields_dict['founder_linkedin_url_in_employee_list']) if len(fields_dict['founder_linkedin_url_in_employee_list']) > 1 else fields_dict['founder_linkedin_url_in_employee_list'][0]
        
        upload_dict = {"id":record_id, 
                    "fields":fields_dict}

           
        founder_update_dicts_list.append(upload_dict)
        

    except (NoAssignedStartupException, NoEmployeeListException, InvalidEmployeeListException) as e:
        upload_dict = {"id":record_id, 
                    "fields":fields_dict}
        founder_update_dicts_list.append(upload_dict)



def find_employee_calling_themselves_founder(row, all_founders_df, new_founder_dicts_list):
    """
    This function finds for each startup's employee list, if someone calls themselves a founder (or another word indicating a founder))
    It then checks if this person is in the airtable. 

    args:
    row: a row from the startups table dataframe
    
    returns:

    None: if there is no employee data (hidden themselves on linkedin) 
         or if they dont call themselves a founder/gründer etc. in their designation
    
    """


    # check if the employee info is null (hidden), and exit with None returned.
    if pd.isnull((row['employee_list_linkedin'])):
        return None

    if (row['employee_list_linkedin']) == "nan":
        return None


    j_data = ast.literal_eval(row['employee_list_linkedin'])
    employee_list_df = pd.json_normalize(j_data)

    if employee_list_df.empty:
        return None

    #Filter out entries in the founders table with no associated linked startup
    all_founders_df = all_founders_df[~all_founders_df['founder_startups'].isnull()]

    # Get a dataframe of all the employees in the founders table who are working at the present company
    # The line below is the more obvious way of doing it, but is less efficient
    # all_current_founders_at_companies = all_founders_df[all_founders_df['founder_startups'].apply(lambda x: row['record_id'] in x)]
    
    exploded_df = all_founders_df.explode('founder_startups')
    filtered_df = exploded_df[exploded_df['founder_startups'].astype(str).str.contains(row['record_id'])]
    all_current_founders_at_companies = filtered_df.drop_duplicates('founder_record_id')
    all_current_founders_at_companies = all_founders_df



    # list of possible strings a founder could have in their designation
    founder_indicator_strings = ["founder", "cofounder", 
                                    "co-founder", "gründer", "gründerin", 
                                    "co-fondateur", "fondateur", "cofondateur", 
                                    "geschäftsführung", "mitgründer", "unternehmensinhaber", 
                                    "geschäftsführender", "gesellschafter", "mitgründerin", 'geschäftsführer', 'gründung',
                                    "geschäftsführer", 
                                    "geschäftsführerin", "geschaftsinhaber",
                                    "inhaber", "inhaberin", "gesellschafter", "gesellschafterin"]
   


    umlaut_char_map = {'ue':ord('ü')}
    employee_list_df= employee_list_df[~employee_list_df['designation'].isnull()]
    # convert anglicized umlaut two-letter combinations to the unicode umlaut character
    employee_list_df['designation'] = employee_list_df['designation'].str.translate(umlaut_char_map)

    # use fuzzy partial matching to find if any substring or word in the designation is a word that indicates they could be a founder
    pattern = r"(?i)\b(" + r'|'.join(founder_indicator_strings)  + r")\b"
    employee_list_df['founder_indicator'] = employee_list_df['designation'].str.extract(pattern)
    
    employee_list_df = employee_list_df[employee_list_df['designation'].apply(lambda x: any([k not in x for k in nominals.EXCEPTIONS_TO_JOB_TITLES]))]

    employees_calling_themselves_founder = employee_list_df[~employee_list_df['founder_indicator'].isnull()]

    if employees_calling_themselves_founder.empty:
        return None

    # We now want to search if any of the employees_calling_themselves_founder are not in all_current_founders_at_companies
    # This means that there are people in the linkedin employee list who are not in the founders airtable, and yet they have founder in their designation
    employees_calling_themselves_founder['cleaned_name', 'match'] = np.nan
    employees_calling_themselves_founder['cleaned_name'] = employees_calling_themselves_founder.apply(lambda x: ' '.join(clean_founder_name(x["name"])),axis=1)
    
    #Remove emojis and other unwanted characters
    employees_calling_themselves_founder['cleaned_name'] = employees_calling_themselves_founder['cleaned_name'].str.encode("ascii", "ignore").str.decode('utf-8').str.strip()
    
    #Remove words between brackets
    employees_calling_themselves_founder['cleaned_name'] = employees_calling_themselves_founder['cleaned_name'].str.replace("[\(\[].*?[\)\]]", "", regex=True)

    #Create empty dataframe of entries in fields to be updated
    fields_df = pd.DataFrame()

    # Check if there are any founders at the current startup to compare to, and then use fuzzy matching to extract those where are match was not found
    if not all_current_founders_at_companies.empty:
        employees_calling_themselves_founder['match'] = employees_calling_themselves_founder['cleaned_name'].apply(lambda x: process.extractOne(x, all_current_founders_at_companies["founders_combined_name"], scorer=fuzz.QRatio))
        potential_missing_founders = employees_calling_themselves_founder[employees_calling_themselves_founder['match'].str[1] < 83]

        if potential_missing_founders.empty:
            return None
    
        _, potential_missing_founders['match_score'] , potential_missing_founders['match_index'] = zip(*potential_missing_founders['match'])
        potential_missing_founders = potential_missing_founders.reset_index(drop=True)

    else:
        potential_missing_founders = employees_calling_themselves_founder.reset_index()

    
   
        
    # We test if the designation string contains a pattern that matches "Founder {at/bei/of} Company" 
    # This is necessary because we may have detected people as founders because they have "founder" in their designation
    # but are not actually a founder at the startup in question.
    # The regex pattern looks for the founder indicator strings specified above, then maximum 4 words, then the company name.
    # All the following substrings would be detected 
    # E.g Founder at Acme, Cofounder of Acme, Gründer and Developer at Acme, Founder and CEO @ Acme
    startup_name = clean_company_name(row['startup_name'])
    escaped = startup_name.translate(str.maketrans({"(":  r"\(",")":  r"\)"}))
    escaped_startup_name = [i.replace("(", "\(").replace(")", "\)") for i in startup_name]
    pattern = r"(?i)\b(" + r'|'.join(founder_indicator_strings)  + r")\b(?:\s*)(?:[^\s]+ ){0,4}(?:\s*)@?" + fr"{escaped}"
    potential_missing_founders['pattern_match'] =  ~potential_missing_founders['designation'].str.extract(pattern).isnull()

    
    name_list = potential_missing_founders['cleaned_name'].str.split()

    fields_df['founder_first_name'] = name_list.str[0]
    fields_df['founder_last_name'] = potential_missing_founders[name_list.str.len() > 1]['cleaned_name'].str.split().str[-1]
    fields_df = fields_df.fillna('')

    fields_df['founder_linkedin_url'] = potential_missing_founders.apply(lambda row: clean_linkedin_url(row['linkedin_url']), axis=1)
    fields_df['founder_startups'] = row['record_id']
    fields_df['founder_designation'] = potential_missing_founders['designation']
    
    fields_df = fields_df.assign(validation_employee_list=[['potential_new_founder']]*len(fields_df))
    fields_df['designation_result'] = potential_missing_founders.apply(lambda row: ["designation_pattern_matched"] if row['pattern_match'] == True else [], axis=1)
    fields_df['validation_employee_list'] = fields_df['validation_employee_list'] + fields_df['designation_result'] 
    fields_df['founder_source'] = [['employee_list']] * len(fields_df)

    fields_df = fields_df.drop(columns=["designation_result"])

    new_founder_dicts_list.extend(fields_df.to_dict('records'))




    

if __name__ == '__main__':
    # parse arguments from command line
    args = parse_args()
    # read config file
    config = configparser.ConfigParser()
    config.read(args.config_file)

    # allow for progress tracking in pandas apply function
    tqdm.pandas()

    # create startup dataframe from airtable view
    print('retrieving startup and founders data from airtable and saving in dataframes')

    # ignore chained assignment warnings because of dataframe copy with relevant columns
    pd.options.mode.chained_assignment = None  # default='warn'

    founders_table = Table(config.get('Airtable', 'at_pat_token'),
                base_id=config.get('Airtable', 'at_base_id'),
                table_name=config.get('Founders', 'at_table_name'))

    startup_table = Table(config.get('Airtable', 'at_pat_token'),
                base_id=config.get('Airtable', 'at_base_id'),
                table_name=config.get('LI_Startups', 'at_table_name'))

    # define columns that are needed in founders dataframe
    founders_col_list = ['founder_record_id', 'founder_linkedin_url', 'founder_startups', 'startup_name (from founder_startups)', 'startup_linkedin_url (from founder_startups)', 'founder_first_name', 'founder_last_name']
    

    # get complete founders dataframe (we'll need to search the entire set for employees)
    all_founders_df = airtable_to_dataframe(founders_table, config.get('Founders', 'at_unfiltered_view'), fields=founders_col_list)

    all_founders_df = all_founders_df.reindex(columns=founders_col_list)
    all_founders_df['founder_first_name']

    # specify columns that are needed in startup dataframe
    startups_col_list = ['record_id', 'startup_linkedin_url', 'startup_name', 'employee_list_linkedin']
    startups_df = airtable_to_dataframe(startup_table, config.get('LI_Startups', 'at_view_name'), fields=startups_col_list)

    # search_existing_founders_in_employee_list = False
    search_new_founders_in_employee_list = True


    # The following code is not really necessary anymore. It was used for confirming founders
    # if search_existing_founders_in_employee_list:

    #     founder_update_dicts_list = []
    #     # for each row in the founders table, try to find a match in the json.
    #     all_founders_df.progress_apply(lambda row: find_founder_name_match_in_employee_list(row, founder_update_dicts_list), axis=1)
        
    #     print('\nUpdating Airtable with Founder Check...')
    #     founders_table.batch_update(founder_update_dicts_list, typecast=True)
    #     print('\nFinished Updating Airtable with Founder Check')


    if search_new_founders_in_employee_list:
        all_founders_df.loc[:, 'founders_combined_name'] = all_founders_df.apply(lambda row: clean_founder_name(row['founder_first_name'])[0] + ' ' + ' '.join(clean_founder_name(row['founder_last_name'])), axis=1)

        new_founder_dicts_list = []
        current_date = datetime.date.today()
        startups_df = startups_df.loc[~startups_df["employee_list_linkedin"].isnull()]
        startups_df.progress_apply(lambda row: find_employee_calling_themselves_founder(row, all_founders_df, new_founder_dicts_list), axis=1)

        print('\nUpdating Airtable with Potential New Founders...')
        founders_table.batch_create(new_founder_dicts_list, typecast=True)
        print("\nFinished Updating Airtable with Potential New Founders")


