import re
import pandas as pd
import numpy as np


def clean_linkedin_url_company(linkedin_url):
    # remove unnecessary part after company name from url
    reg = re.compile(r"(?:https?:)?\/\/(?:\w+\.)?linkedin\.com\/(?:company|school)\/(?:[A-z0-9-À-ÿ\.%]+)\/?")

    try:
        l_url = reg.match(str(linkedin_url)).group(0)
    except AttributeError:
        return np.nan
    return l_url


def linkedin_company_website_check(row):
    """checks if website from LinkedIn and website from airtable are the same"""
    try:
        li_website = row['website_from_linkedin']
        at_website = row['startup_website_merged']
    except KeyError:
        # not both websites where found
        return 'Failed'
    if pd.isnull(li_website) or pd.isnull(at_website) is None:
        return 'Failed'
    regex_url = re.compile(r'^(?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^:\/?\n.]+)')
    li_domain = regex_url.match(str(li_website)).group(1)
    at_domain = regex_url.match(str(at_website)).group(1)
    if li_domain == at_domain:
        return 'Passed'
    else:
        return 'Failed'
