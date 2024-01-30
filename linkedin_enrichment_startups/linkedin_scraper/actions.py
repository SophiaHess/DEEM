import getpass

import numpy as np

from . import constants as c
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time


def __prompt_email_password():
    u = input("Email: ")
    p = getpass.getpass(prompt="Password: ")
    return (u, p)


def page_has_loaded(driver):
    page_state = driver.execute_script('return document.readyState;')
    return page_state == 'complete'


def login(driver, email=None, password=None, cookie=None, timeout=10):
    if cookie is not None:
        return _login_with_cookie(driver, cookie)

    if not email or not password:
        email, password = __prompt_email_password()

    driver.get("https://www.linkedin.com/login")
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))

    email_elem = driver.find_element(By.ID,"username")
    email_elem.send_keys(email)

    password_elem = driver.find_element(By.ID, "password")
    password_elem.send_keys(password)
    password_elem.submit()

    try:
        if driver.url == 'https://www.linkedin.com/checkpoint/lg/login-submit':
            remember = driver.find_element(By.ID,c.REMEMBER_PROMPT)
            if remember:
                remember.submit()

        element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, c.VERIFY_LOGIN_ID)))
    except:
        pass


def _login_with_cookie(driver, cookie):
    driver.get("https://www.linkedin.com/login")
    driver.add_cookie({
        "name": "li_at",
        "value": cookie
    })


def search_for_company(name, driver):
    # remove unnecesarry stings from company name
    l1 = name.split()
    l2 = ['GmbH', 'UG', "(haftungsbeschränkt)", 'Gbr']
    name_list = [x for x in l1 if x not in l2]
    name_cleaned = ' '.join(name_list)


    # serching for company
    country_code = '%5B"101282230"%5D'
    company_size = '%5B%22B%22%2C%22C%22%2C%22D%22%5D'  # currently up to 200 employees
    time.sleep(3)
    driver.get(
        f'https://www.linkedin.com/search/results/companies/?companyHqGeo={country_code}&companySize={company_size}&keywords={name_cleaned}&origin=GLOBAL_SEARCH_HEADER'
    )

    # get first result item
    results_container = WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'search-results-container')))
    #results_container = driver.find_element_by_class_name('search-results-container')
    results = results_container.find_elements(By.CLASS_NAME, 'entity-result__title-text')  # Todo check after ui change
    result = next(iter(results or []), None)  # we are only looking at first serchresult for company name
    if result is not None:
        link = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
        return link
    else:
        # no results where found
        return np.nan
