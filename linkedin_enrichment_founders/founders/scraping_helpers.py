import re


import pandas as pd
import numpy as np
from dateutil import parser, relativedelta

from calendar import monthrange
from datetime import datetime, date



def parse_datestring(daterangestring):
    """
    Converts date range string to a duration in years
    The duration is inclusive of the start and end month, so Aug 2010 to Aug 2011 would be 13 months, so 1.083 years
    args: 
        datestring (str): date range string

    returns:
        str: start str "xxx YYYY" i.e. "Aug 2022"
        str: end str "xxx YYYY" i.e. "Aug 2022"
       float: years in decimal format
       error: years in decimal format, margin of error

    examples:

        Both months are given:
            Nov 2017 - Dec 2018 -> ('Nov 2017', 'Dec 2018', 1.083, 0)

        If no months are given, it will be assume a median 1 year per year stated, or 6 months if only 1 year stated.
            2017 - 2018 -> ('2017', '2018', 1.083)
            2017 - 2017 -> ('2017', '2017', 0.5)

        1 of the months is given (a missing month will be interpreted as Jun)
            Feb 2017 - 2018 -> ('Feb 2017', '2018', 1.41 years, 0.5)

        Only one year is given
            2017 -> ('2017', '', 0.5, 0.5)

        Only one month and year is given
            July 2017 -> ('July 2017', '', 0.083, 0)

        Last part of date string is "- Present"
            Convert end of date range to current month and year and then calculate as above

        
    """

    error = 0
    #separate the date range string into the first and last date
    head, sep, tail_raw = daterangestring.partition(' - ')

    # If latter date doesnt exist (e.g string is just "2017" or "Jul 2017")
    # then set the latter date equal to the first.
    if tail_raw == '':
        tail = head
    elif tail_raw == "Present":
        tail = date.today().strftime("%b %Y") 
    else:
        tail = tail_raw

    # Now head and tail are in the formats:
    # head = "xxx XXXX" or "XXXX"
    # tail = "yyy YYYY" or "YYYY"

    dates = []
    for date_str in [head, tail]:
        try:
            formatted_date = datetime.strptime(date_str, "%b %Y")
        except ValueError:
            error+=0.5
            formatted_date = datetime.strptime(date_str, "%Y") + relativedelta.relativedelta(month=6)
        
        dates.append(formatted_date)
    
    fd, ld = dates

    if fd.year == ld.year and error > 0:
        diff = relativedelta.relativedelta(months=6)
        error=0.5
        if fd.year == date.today().year:
            fd = fd + relativedelta.relativedelta(month=1)
            diff = relativedelta.relativedelta(*list(reversed(sorted([ld,fd])))) + relativedelta.relativedelta(months=1)

    elif fd == ld:
        diff = relativedelta.relativedelta(months=1)
    else:
        diff = relativedelta.relativedelta(*list(reversed(sorted([ld,fd])))) + relativedelta.relativedelta(months=1)


    diff_in_decimal = diff.years + diff.months/12

    start_str = head
    end_str = tail_raw

    if tail == head:
        end_str = tail
    return start_str, end_str, diff_in_decimal, error


#These functions call javascript directly and are more performant than xpaths for DOM node traversal
def get_parent_element(driver, el):
    return driver.execute_script("return arguments[0].parentNode;", el)

def get_first_child_element(driver, el):
    return driver.execute_script("return arguments[0].children[0];", el)

def get_children_elements(driver, el):
    return driver.execute_script("return arguments[0].children;", el)

def get_parent_element(driver, el):
    return driver.execute_script("return arguments[0].parentNode;", el)

def get_inner_html_of_element(driver, el):
    return driver.execute_script("return arguments[0].innerHTML",el)
