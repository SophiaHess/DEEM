import pandas as pd
import requests
import os
import sys
import math
import numpy as np
import re
import csv
from urllib.parse import urlparse
import time
import urllib3
import logging


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from functions import get_host_name_from_url

def get_final_url(url):
    try:
        response = requests.head(url, allow_redirects = True)
        return response
    except requests.exceptions.RequestException:
        return None

#compare the URLs are redirect to same website or not
def compare_redirects(url1,url2):
    response1 = get_final_url(url1)
    response2 = get_final_url(url2)

    if response1 is None or response2 is None:
        return url1
    else:
        if(response1.url == response2.url):
            print("same website",response1.url,response1.status_code,response2.url,response2.status_code)
            return response1.url
        else:
            domainName1 = get_host_name_from_url(response1.url)
            domainName2 = get_host_name_from_url(response2.url )
            if(domainName1 == domainName2):
                print("same url", domainName1)
                return response1.url
            elif response2.status_code == 301:
                print("redirect to another website",response1.url,response1.status_code , response2.url, response2.status_code)
                return response2.url
            elif response2.status_code != 301:
                print("xxxxxx",response1.url,response2.url,response1.status_code,response2.status_code)
                return response1.url    
   
#------------------------------- CHECK 01 ---------------------------
# funtion to check NO REGION FILLED
def check_region(region,nuts3_code):
    #add address in the output
    region = str(region) 
    if  region.lower() == 'nan':
        # print("The value is NaN.",nuts3_code)
        return 'Baden-Württemberg'
    elif region.lower() == 'Unknown':
         nuts3_code = str(nuts3_code)
         if nuts3_code.lower() == 'nan':
              print('inside if condition for NUTS 3 CODE',nuts3_code)
              return 'Unknown'
         else:
              if 'DE1' in nuts3_code:
                   print("The value is NaN AND NOT HAVE NUTS3COE3",nuts3_code)
                   return 'Baden-Württemberg'
              else:
                   print("REGION IS UNKNOWN")
                   return 'Unknown'    
    else: 
        #  print("The value is not NaN.",region)
         return region
   
#------------------------------- CHECK 02 --------------------------- 
# function to check the ADDRESS WITH POSTAL CODE & NUT3CODE
def check_address(recordId,StartupName,City,PostalCode,Nut3Code,region):
    fileName = 'check_address.csv'
    City = str(City)
    PostalCode = str(PostalCode)
    Nut3Code = str(Nut3Code)
    region = str(region)
    if City != 'nan' and PostalCode != 'nan' and Nut3Code != 'nan':
        if region != 'nan':
            return region
        else:
            save_address(fileName,recordId,StartupName,City,PostalCode,Nut3Code, region)  
    elif City == 'nan' and PostalCode == 'nan':
        if  Nut3Code != 'nan':
            save_address(fileName,recordId,StartupName,City,PostalCode,Nut3Code, region)  

        else:
            save_address(fileName,recordId,StartupName,City,PostalCode,Nut3Code, region)  
 
    else:        
        save_address(fileName,recordId,StartupName,City,PostalCode,Nut3Code, region)  


#------------------------------- CHECK 03 ---------------------------
# function to check the STARTUP TYPE  
def check_startup_type(type):
    type = str(type)
    if type == 'nan':
        return 'classic'
    else:
        return type
# ------------------------------- CHECK 4---------------------------------
# function to check the MATURITY LEVEL OF STARTUP
def check_maturity_level(maturity,date_incorporation_startupdetector):
    maturity = str(maturity)
    date_incorporation_startupdetector = str(date_incorporation_startupdetector)

    if maturity == 'nan' and date_incorporation_startupdetector  == 'nan':
        return 'startup_project' 
    elif maturity == 'nan' and date_incorporation_startupdetector  != 'nan':
        return 'incorporated'
    else:
        return maturity


#-------------------------------- CHECK 5----------------------------
# function to check the STARTUP STATUS
def check_startup_status(Startup_Status, Website_Status,recordId, StartupName,Website):
    Dead_Status = ['failed to connect', '404 - not found', '404 - Not Found', '404 not found', '404 - Unknown site',
                   'missing url', 'not available', '503 service unavailbale', 'redirect error', '500']
    Startup_Status = str(Startup_Status)
    Website_Status = str(Website_Status)
    fileName = 'check_startup_website_status.csv'
    if Startup_Status == 'nan' or Startup_Status == 'unknown'or Startup_Status == 'Unknown':
        for Status in Dead_Status:
            index = Website_Status.find(Status)
            if index != -1:
                Webiste_Old_Status = Startup_Status
                Webiste_New_Status = 'dead'
                save_startup_website_status(fileName,recordId,StartupName,Website,Webiste_Old_Status,Webiste_New_Status)
                return 'dead'
        # If none of the statuses match, return 'active' outside the loop
        return 'active'
        # If Startup_Status is not 'nan' or 'unknown', return 'active'
    return Startup_Status
     
#-------------------------------- CHECK 6 ---------------------------
#function to check the LEGAL STATUS
def check_legal_status(recordId, StartupName,startup_legal_status):
    StartupName = str(StartupName)
    legal_status = ['GmbH', 'gmbH', 'gmbh', 'gGmbH', 'AG', 'Inc', 'GbR', 'Ltd', 'UG', 'inc', 'ggmbh', 'ggmbH', 'e.V.']

    for status in legal_status:
        # Check if the substring is present at the end of the original string, preceded by a space
        if StartupName.endswith(" " + status):
            modified_name = StartupName[:-len(status) - 1].strip()  # Remove legal status and the preceding space, and strip any extra spaces
            print('result:',StartupName,'---', modified_name)
            return modified_name,status

    # If no legal status is found, return the original string
    # print('result:', StartupName)
    return StartupName,startup_legal_status


#-------------------------------- CHECK 7----------------------------
def check_founding_year(recordId,StartupName,Legalstatus,date_incorporation_startupdetector,founding_date_merged,Maturity):
    fileName = 'check_founding_year.csv'

    if date_incorporation_startupdetector  == 'nan' or founding_date_merged == 'nan' or Legalstatus != 'nan':
        save_startupName(fileName,recordId,StartupName,Legalstatus,date_incorporation_startupdetector,founding_date_merged,Maturity)
    else: 
        return StartupName
    

    # if Legalstatus != 'nan' and founding_date_merged == 'nan':
    #     save_startupName(fileName,recordId,StartupName,Legalstatus,date_incorporation_startupdetector,founding_date_merged,Maturity)

#-------------------------------- CHECK 8----------------------------
# function to check the STARTUP DESCRIPTION
def check_startup_description(recordId,StartupName,description):
    fileName = 'check_startup_missing_description.csv'
    description = str(description)
    if description == 'nan':
        # print(record_id,StartupName,description)
        file_exists = False
        try:
            with open(fileName, 'r'):
                file_exists = True
        except FileNotFoundError:
            pass

        # Open the CSV file in append mode, creating it if it doesn't exist
        with open(fileName, 'a', newline='',encoding='utf-8') as csvfile:
            fieldnames = ['RecordID', 'StartupName']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # If the file didn't exist, write the header
            if not file_exists:
                writer.writeheader()

            # Write the startup name and record ID to the CSV file
            writer.writerow({'RecordID': recordId, 'StartupName': StartupName})


#-------------------------------- CHECK 9 ---------------------------
# function to check the WEBSITE REDIRECT 
def is_valid_url(url):
    return urlparse(url).scheme in ['http', 'https']

def website_redirect_check(recordId, StartupName, url, timeout=5, max_retries=3):
    if not urlparse(url).scheme:
        url = 'https://' + url
    fileName = 'website_redirect_check.csv'

    for _ in range(max_retries):
        try:
            result = requests.get(url, timeout=timeout)
            result.raise_for_status()  # Raises an HTTPError for bad responses
            break
        except requests.Timeout:
            logging.error(f'Timeout error occurred for {url}.')
            return None
        except requests.RequestException as e:
            logging.error(f'Request error: {e}')
            return None
        except Exception as e:
            logging.error(f'An unexpected error occurred: {e}')
            return None
        time.sleep(2)
    else:
        logging.error(f'Max retries exceeded for {url}.')
        return None

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if result.status_code == 301 or result.status_code == 308:
        if is_valid_url(result.url):
            logging.info(f'Redirect detected for {url}.')
            file_exists = False
            try:
                with open(fileName, 'r'):
                    file_exists = True
            except FileNotFoundError:
                pass

            with open(fileName, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['RecordID', 'StartupName', 'Old_URL', 'New_URL']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({'RecordID': recordId, 'StartupName': StartupName, 'Old_URL': url, 'New_URL': result.url})

        else:
            logging.warning(f'The new website is not valid for {url}.')
            return None
    else:
        logging.info(f'Website did not move permanently for {url}.')
        return None
#-------------------------------- function to save results in file---
def save_address(fileName, recordId, StartupName,City,PostalCode,Nut3Code,Region):
    # Check if the file already exists
    file_exists = False
    try:
        with open(fileName, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    # Open the CSV file in append mode, creating it if it doesn't exist
    with open(fileName, 'a', newline='',encoding='utf-8') as csvfile:
        fieldnames = ['RecordID', 'StartupName','City','PostalCode','Nut3Code','Region']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # If the file didn't exist, write the header
        if not file_exists:
            writer.writeheader()

        # Write the startup name and record ID to the CSV file
        writer.writerow({'RecordID': recordId, 'StartupName': StartupName,'City':City,'PostalCode':PostalCode,'Nut3Code':Nut3Code,'Region':Region})

def save_startupName(fileName, recordId, startName,Legalstatus,date_incorporation_startupdetector,founding_date_merged,Maturity):
    # Check if the file already exists
    file_exists = False
    try:
        with open(fileName, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    # Open the CSV file in append mode, creating it if it doesn't exist
    with open(fileName, 'a', newline='' , encoding='utf-8') as csvfile:
        fieldnames = ['RecordID', 'StartupName','Legalstatus','date_incorporation_startupdetector','founding_date_merged','Maturity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # If the file didn't exist, write the header
        if not file_exists:
            writer.writeheader()

        # Write the startup name and record ID to the CSV file
        writer.writerow({'RecordID': recordId, 'StartupName': startName,'Legalstatus':Legalstatus,'date_incorporation_startupdetector':date_incorporation_startupdetector,'founding_date_merged':founding_date_merged,'Maturity':Maturity})


def save_startup_website_status(fileName,recordId,StartupName,Website,Webiste_Old_Status,Webiste_New_Status):
    # Check if the file already exists
    file_exists = False
    try:
        with open(fileName, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    # Open the CSV file in append mode, creating it if it doesn't exist
    with open(fileName, 'a', newline='' , encoding='utf-8') as csvfile:
        fieldnames = ['RecordID', 'StartupName','Website','Webiste_Old_Status','Webiste_New_Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # If the file didn't exist, write the header
        if not file_exists:
            writer.writeheader()

        # Write the startup name and record ID to the CSV file
        writer.writerow({'RecordID': recordId, 'StartupName': StartupName,'Website':Website,'Webiste_Old_Status':Webiste_Old_Status,'Webiste_New_Status':Webiste_New_Status})


if __name__ == "__main__":
    
    dataframe = pd.read_csv("add-your-csv-file.csv", encoding='utf-8')

    if 'q_validation_website' not in dataframe.columns:
        dataframe['q_validation_website'] = True
    for index, row in dataframe.iterrows():
        recordId = row['record_id']
        startupName = row['startup_name']
        startup_type = row['startup_type']
        url1 = row['startup_website_merged']
        url2 = row['website_from_linkedin']
        startup_region = row['startup_region_nuntium']
        startup_city = row['startup_city']
        startup_postal = row['startup_postal']
        maturity_level = row['startup_maturity']
        startup_status = row['startup_status']
        startup_website_status = row['startup_website_status']
        startup_nuts3_code = row['startup_nuts3_code']
        date_incorporation_startupdetector = row['date_incorporation_startupdetector']
        startupDescription = row['startup_description']
        startup_legal_status = row['startup_legal_status']
        founding_date_merged = row['founding_date_merged']


        result = compare_redirects(url1, url2)
        region = check_region(startup_region,startup_nuts3_code)
        check_address(recordId,startupName,startup_city,startup_postal,startup_nuts3_code,startup_region)
        startup_type = check_startup_type(startup_type)
        MaturityLevel = check_maturity_level(maturity_level,date_incorporation_startupdetector)
        Startup_status = check_startup_status(startup_status,startup_website_status,recordId,startupName,url1)
        startupName,legalStatus = check_legal_status(recordId,startupName,startup_legal_status)
        check_founding_year(recordId,startupName,startup_legal_status,date_incorporation_startupdetector,founding_date_merged,maturity_level)
        check_startup_description(recordId,startupName,startupDescription)
        website_redirect_check(recordId,startupName,url1)


        dataframe.at[index, 'q_validation_website'] = result
        dataframe.at[index, 'startup_region_nuntium'] = region 
        dataframe.at[index, 'startup_type'] = startup_type
        dataframe.at[index, 'startup_maturity'] = MaturityLevel
        dataframe.at[index, 'startup_name'] = startupName
        dataframe.at[index, 'startup_legal_status'] = legalStatus
        dataframe.at[index, 'startup_status'] = Startup_status
    # Update the CSV file with the results.
    dataframe.to_csv("your-csv-file.csv",index=False,encoding="utf-8")     

