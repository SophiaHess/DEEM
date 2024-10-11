import re

import pandas as pd
import numpy as np
from dateutil import parser, relativedelta

from calendar import monthrange
from datetime import datetime, date

import founders.nominals as nominals


from fuzzywuzzy import fuzz

def get_combined_name(first_name, last_name):
    
    #get the lists of first names and last names
    first_name_list = clean_founder_name(first_name)
    last_name_list = clean_founder_name(last_name)
    # combined_full_name is with middle names
    combined_full_name = ' '.join(first_name_list) + ' ' + ' '.join(last_name_list)
    return combined_full_name



def get_domain_from_url(url):
    """
    Extract second-level domain part of a given url

    args: 
        url (str): a website url 
    returns:
        str: extracted domain
    
    example:

        www.google.com -> google
        https://www.example.io/ -> example

    """

    if url  is None or url == "" or url != url:
        return None

    regex = r"(?:https?:)?\/?\/?(?:www.)?(.*?)(?:\.)"
    r = re.compile(regex)
    f_list = r.findall(url)
    return next(iter(f_list or []), np.nan)



def clean_founder_name(name):
    """
    This function removes titles and commas from a name.
    e.g "Maguire, MSc" returns ["Maguire"]
    and "Darcy Thomas" returns ["Darcy", "Thomas"]
    
    args: 
        name (str): a founder's first name or last name
    
    returns:
       list of strings: each space-separated name in the input string is returned
       as a sring in a list.

    """
    
    #Seperate the first name into a list of names, so that we can iterate through the list and search for each combination.
    # E.g "Darcy Thomas" -> ["Darcy", "Thomas"]. We can then search "Darcy Maguire" and "Thomas Maguire".
    words_to_remove = ['Dr.', 'Prof.', "Dr.-Prof", "Dr.-Ing.", "habil.", "rer.", "med.", "Freiherr", "MBA", "MSc", "MA", "MD", "PHD", "Jr.", "Sr."]
    all_nominals = nominals.DOCTOR_NOMINALS + nominals.MASTER_NOMINALS + nominals.BACHELOR_NOMINALS + nominals.OTHER_DEGREE_NOMINALS

    if pd.isnull(name):
        return ['']

    #Replace commas in name with spaces
    name = name.replace(',',' ')
    name = name.strip()
    
    #split first name string into a list of the separate names
    #remove the substrings that are thse in l2 (titles)
    l1 = name.split()
    name_list = [x for x in l1 if (x not in words_to_remove and x not in all_nominals)]

    if len(name_list) == 0:
        return ['']

    return name_list

def clean_linkedin_url(linkedin_url, get_just_id=False):
    """
    Remove subdomains and URL slugs from the startup linkedin url. 
    So that it is in a standard format.
    e.g de.linkedin.com/company/hygla/about/ -> www.linkedin.com/company/hygla

    args: 
        linkedin_url (str): a linkedin url
        get_just_id (bool, optional): if true, only the user/company slug "id" part of the url is returned

    returns:
       str: cleaned linkedin url
    """
    if linkedin_url != linkedin_url or linkedin_url == "" or linkedin_url is None:
        return ""

    linkedin_url = re.sub("\/\/..\.", "//www.", linkedin_url, count=0, flags=0)

    if get_just_id:
       regex = r"(?:https?:\/\/)?(?:[\w]+\.)?linkedin\.com\/(?:company|school|in)\/((?:[A-z0-9À-ÿ%-]+))?"
    else:
        regex = r"(?:https?:\/\/)?(?:[\w]+\.)?linkedin\.com\/(?:company|school|in)\/(?:[A-z0-9À-ÿ%-]+)?"

        
    r = re.compile(regex)
    f_list = r.findall(linkedin_url)
    return next(iter(f_list or []), np.nan)

def clean_company_name(company_name):

    if company_name != company_name or company_name == "":
        return ""

    l1 = company_name.split()
    l2 = ['GmbH', 'UG', "(haftungsbeschränkt)", 'Gbr', 'AG', 'KG', '(Haftungsbeschränkt)']
    name_list = [x for x in l1 if x.lower() not in [y.lower() for y in l2]]
    return ' '.join(name_list)

def get_domain_from_url(url):

    pattern = r"^(?:https?:\/\/)?(?:www\.)?([^\/]+)"
    
    if url is None or url != url:
        return ""
    
    m = re.search(pattern, url)

    return m.group(1)

def remove_parantheticals_from_string(text):

    if text != text or text is None:
        return "" 
    opening_braces = '\(\['
    closing_braces = '\)\]'
    non_greedy_wildcard = '.*?'
    return re.sub(f'[{opening_braces}]{non_greedy_wildcard}[{closing_braces}]', '', text).strip()


#comparison function to check if two names are similar
def are_names_similar(name1, name2, threshold=85):
    similarity = fuzz.partial_ratio(name1.lower(), name2.lower())
    return similarity >= threshold

def convert_str_to_datetime(date_str):
    try:
        return datetime.strptime(date_str, "%b %Y")
    except ValueError:
        return datetime.strptime(date_str, "%Y")