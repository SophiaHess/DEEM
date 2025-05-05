import selenium.common.exceptions as selenium_exeptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from .objects import Scraper
from .functions import check_if_element_exists
from .linkedin_functions_company import clean_linkedin_url_company
import time
import os
import json
import re
import warnings

AD_BANNER_CLASSNAME = ('ad-banner-container', '__ad')


def get_website_from_linkedin(li_url, driver):
    """returning website url from LinkedIn profile"""
    # instantiate company object with website only option
    company = Company(li_url, driver=driver, website_only=True, close_on_complete=False)
    website_li = company.website
    return website_li


class InvalidUrlException(Exception):
    """raised if an Url that is not a LinkedIn company profile is passed"""
    pass


class Company(Scraper):
    linkedin_url = None
    record_id = None
    name = None
    about_us = None
    website = None
    headquarters = None
    founding_year = None
    industry = None
    company_type = None
    company_size = None
    specialties = None
    startup_address_raw_linkedin = None
    startup_follower_linkedin = None
    main_university_employees = None
    employees = []
    showcase_pages = []
    affiliated_companies = []

    def __init__(self, linkedin_url=None, record_id=None, name=None, about_us=None, website=None, headquarters=None, startup_follower_linkedin = None,
                 founding_year=None, industry=None, company_type=None, company_size=None, specialties=None, startup_address_raw_linkedin = None,
                 main_university_employees=None, employees=[], showcase_pages=[], affiliated_companies=[],
                 driver=None, scrape=True, get_employees=True, close_on_complete=True, website_only=False):
        self.linkedin_url = linkedin_url
        self.record_id = record_id
        self.name = name
        self.about_us = about_us
        self.website = website
        self.headquarters = headquarters
        self.founding_year = founding_year
        self.industry = industry
        self.company_type = company_type
        self.company_size = company_size
        self.specialties = specialties
        self.startup_address_raw_linkedin = startup_address_raw_linkedin
        self.startup_follower_linkedin = startup_follower_linkedin
        self.main_university_employees = main_university_employees
        self.employees = employees
        self.showcase_pages = showcase_pages
        self.affiliated_companies = affiliated_companies

        # clean linkedin url to ensure we land on the starting page of the company profile
        try:
            self.linkedin_url = clean_linkedin_url_company(self.linkedin_url)
        except AttributeError:
            # if the url is not a valid linkedin company url
            raise InvalidUrlException

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") is None:
                    driver_path = os.path.join(os.path.dirname(__file__), 'drivers/chromedriver')
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        # driver.get(self.linkedin_url)
        self.driver = driver

        if website_only:
            # ensure scrape is set to fallse so only website is scraped
            scrape = False
            self.scrape(get_employees=False, website_only=True, close_on_complete=False)
        if scrape:
            self.scrape(get_employees=get_employees, close_on_complete=close_on_complete)

    def __get_text_under_subtitle(self, elem):
        return "\n".join(elem.text.split("\n")[1:])

    def __get_text_under_subtitle_by_class(self, driver, class_name):
        return self.__get_text_under_subtitle(driver.find_element(By.CLASS_NAME, class_name))

    def __ensure_driver_on_url(self, url):
        _ = self.driver.current_url
        if self.driver.current_url != url:
            self.driver.get(url)

    def __parse_employee__(self, employee_raw):
        try:
            employee_object = {}
            employee_object['name'] = (employee_raw.text.split("\n") or [""])[0].strip()
            employee_object['designation'] = (employee_raw.text.split("\n") or [""])[3].strip()
            employee_object['linkedin_url'] = employee_raw.find_element(By.TAG_NAME, "a").get_attribute("href")
            # print(employee_raw.text, employee_object)
            # _person = Person(
            #     # linkedin_url = employee_raw.find_element_by_tag_name("a").get_attribute("href"),
            #     linkedin_url = employee_raw.find_element_by_tag_name("a").get_attribute("href"),
            #     name = (employee_raw.text.split("\n") or [""])[0].strip(),
            #     driver = self.driver,
            #     get = True,
            #     scrape = False,
            #     designation = (employee_raw.text.split("\n") or [""])[3].strip()
            #     )
            # print(_person, employee_object)
            # return _person
            return employee_object
        except Exception as e:
            # print(e)
            return None

    def __parse_employee_search_result__(self, employee_raw):
        try:
            employee_object = {}
            employee_object['name'] = (employee_raw.text.split("\n") or [""])[0].strip()
            # dropout if name is just 'LinkedIn Member'
            if employee_object['name'] == 'LinkedIn Member':
                return None
            employee_object['designation'] = \
                employee_raw.find_element(By.CLASS_NAME, "entity-result__primary-subtitle").text.strip()
            employee_object['linkedin_url'] = employee_raw.find_element(By.TAG_NAME, "a").get_attribute("href")
            return employee_object

        except Exception as e:
            return None

    def __get_attributes_about_page(self):
        driver = self.driver
        # ensure we are on the about page
        self.__ensure_driver_on_url(os.path.join(self.linkedin_url, "about/"))

        # Use a more specific CSS selector to target the followers' element
        followers_elements = driver.find_elements(By.CSS_SELECTOR, ".org-top-card-summary-info-list__info-item")

        # Iterate through elements to find the one containing followers information
        n_follower = None
        for element in followers_elements:
            follower_text = element.text.strip()
            match = re.search(r'(\d+(?:\.\d+)?)([KM]?) followers', follower_text)  # Match digits followed by optional K or M and 'followers'
            if match:
                n_follower = match.group(1)
                suffix = match.group(2)
                if suffix == 'K':
                    n_follower = float(n_follower) * 1_000
                elif suffix == 'M':
                    n_follower = float(n_follower) * 1_000_000
                else:
                    n_follower = float(n_follower)
                break

        # location = driver.execute_script("return document.querySelector('.org-location-card.pv2 p').innerText")
        location_element = driver.execute_script("return document.querySelector('.org-location-card.pv2 p')")
        if location_element is not None:
            location = driver.execute_script("return document.querySelector('.org-location-card.pv2 p').innerText")
        else:
            location = "Address not found"
        # get all labels and values
        # Todo after UI change: find class name of section containing information on about page of company
        try:
            # element = driver.find_element(By.CSS_SELECTOR, '.org-location-card.pv2 p')
            # if element:
            #     location = element.text

            grid = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'artdeco-card.org-page-details-module__card-spacing.artdeco-card.org-about-module__margin-bottom')))

            labels = grid.find_elements(By.TAG_NAME, "dt")
            values = grid.find_elements(By.TAG_NAME, "dd")
            num_attributes = min(len(labels), len(values))
            # grid_locations = WebDriverWait(driver, 5).until(
            #     EC.presence_of_element_located((By.CLASS_NAME, '.org-locations-module__card-spacing.org-location-card.pv2')))

            # location = grid_locations.find_elements(By.TAG_NAME, "p")
        except selenium_exeptions.TimeoutException:
            # section containing "about" information not found
            labels, values, num_attributes, grid = [None] * 4
        return labels, values, num_attributes, grid, location, n_follower

    def scrape(self, get_employees=True, close_on_complete=True, website_only=False):
        if self.is_signed_in():
            self.scrape_logged_in(get_employees=get_employees,
                                  close_on_complete=close_on_complete,
                                  website_only=website_only)
        else:
            self.scrape_not_logged_in(get_employees=get_employees,
                                      close_on_complete=close_on_complete,
                                      website_only=website_only)

    def scrape_logged_in(self, get_employees=True, close_on_complete=True, website_only=False):
        # get information from about tab
        if website_only:
            self.get_website()
        else:
            self.get_about_us_information()
        if get_employees and self.n_employees_linkedin:
        # if get_employees:
            self.get_employees_information()

        if close_on_complete:
            self.driver.close()

    def scrape_not_logged_in(self, close_on_complete=True, retry_limit=10, get_employees=True, website_only=False):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1

        if website_only:
            try:
                self.website = self.__get_text_under_subtitle_by_class(driver, "website")
            except selenium_exeptions.NoSuchElementException:
                self.website = None
            return

        try:
            self.name = driver.find_element(By.CLASS_NAME, "name").text.strip()
        except selenium_exeptions.NoSuchElementException:
            self.name = None
        try:
            self.about_us = driver.find_element(By.CLASS_NAME, "basic-info-description").text.strip()
        except selenium_exeptions.NoSuchElementException:
            self.about_us = None
        try:
            self.specialties = self.__get_text_under_subtitle_by_class(driver, "specialties")
        except selenium_exeptions.NoSuchElementException:
            self.specialties = None
        try:
            self.website = self.__get_text_under_subtitle_by_class(driver, "website")
        except selenium_exeptions.NoSuchElementException:
            self.website = None
        try:
            self.headquarters = driver.find_element(By.CLASS_NAME, "adr").text.strip()
        except selenium_exeptions.NoSuchElementException:
            self.headquarters = None
        try:
            self.industry = driver.find_element(By.CLASS_NAME, "industry").text.strip()
        except selenium_exeptions.NoSuchElementException:
            self.industry = None
        try:
            self.company_size = driver.find_element(By.CLASS_NAME, "company-size").text.strip()
        except selenium_exeptions.NoSuchElementException:
            self.company_size = None
        try:
            self.company_type = self.__get_text_under_subtitle_by_class(driver, "type")
        except selenium_exeptions.NoSuchElementException:
            self.company_type = None
        try:
            self.founding_year = self.__get_text_under_subtitle_by_class(driver, "founded")
        except selenium_exeptions.NoSuchElementException:
            self.founding_year = None

        if get_employees:
            self.employees = self.get_employees_information()

        driver.get(self.linkedin_url)

        if close_on_complete:
            driver.close()

    def get_website(self):
        labels, values, num_attributes, *_ = self.__get_attributes_about_page()
        # set website to none if num_attributes is None Type object
        if num_attributes is None:
            self.website = None
            return
        # iterate through labels until we find website and return
        for i in range(num_attributes):
            txt = labels[i].text.strip()
            if txt == 'Website':
                self.website = values[i].text.strip()
                return
        return

    def get_about_us_information(self):
        labels, values, num_attributes, grid, location, n_follower = self.__get_attributes_about_page()

        self.startup_address_raw_linkedin = location
        self.startup_follower_linkedin = n_follower
        # get company name
        self.name = WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.XPATH, '//span[@dir="ltr"]'))).text.strip()
        
        try:
            elements = self.driver.find_elements(
                By.XPATH,
                "//dd[@class='t-black--light mb4 text-body-medium']/a/span"
            )
            if elements:
                associated_members_text = elements[0].text
                self.n_employees_linkedin = int(''.join(filter(str.isdigit, associated_members_text)))
            else:
                self.n_employees_linkedin = None
        except Exception as e:
            self.n_employees_linkedin = None


        # # Find the element containing the number of associated members
        # associated_members_element = self.driver.find_element(By.XPATH, "//dd[@class='t-black--light mb4 text-body-medium']/a/span")

        # # Extract the text from the element
        # associated_members_text = associated_members_element.text
        # # Extract only the number from the text
        # self.n_employees_linkedin = int(''.join(filter(str.isdigit, associated_members_text)))


        # iterate through labels and save corresponding values
        x_off = 0
        try:
            for i in range(num_attributes):
                txt = labels[i].text.strip()
                if txt == 'Website':
                    self.website = values[i + x_off].text.strip()
                elif txt == 'Industry':
                    self.industry = values[i + x_off].text.strip()
                elif txt == 'Company size':
                    self.company_size = values[i + x_off].text.strip()
                    if len(values) > len(labels):
                        x_off = 1
                elif txt == 'Headquarters':
                    self.headquarters = values[i + x_off].text.strip()
                elif txt == 'Type':
                    self.company_type = values[i + x_off].text.strip()
                elif txt == 'Founded':
                    self.founding_year = values[i + x_off].text.strip()
                elif txt == 'Specialties':
                    self.specialties = "\n".join(values[i + x_off].text.strip().split(", "))
        except TypeError:
            # happens if num_attributes is NoneType object because there was no about us information
            pass

        try:
            # get about us text
            descWrapper = grid.find_elements(By.TAG_NAME, "p")
            if len(descWrapper) > 0:
                self.about_us = descWrapper[0].text.strip()
        except AttributeError:
            # happens if grid is nonetype object
            pass

    def get_employees_information(self, wait_time=10):
        """returns employee information and university affiliation from people page"""
        total = []
        employees_lists_css = '.org-grid__content-height-enforcer'  # css selector for employee insights and short profiles
        list_css_carousel = "artdeco-carousel__content"  # class for element containing barcharts about university
        next_xpath = '//button[@aria-label="Next"]'
        driver = self.driver
        n_employees_linkedin = self.n_employees_linkedin

        # get number of employees on linkedin from top of page
        # try:
        #     connections_section = driver.find_element(By.CLASS_NAME, 'mt1')
        #     # get last link in connections section
        #     connections_links = connections_section.find_elements(By.TAG_NAME, 'a')
        #     all_employees_link = connections_links[-1]
        #     n_employees_text = all_employees_link.text
        #     all_employees_url = all_employees_link.get_attribute('href')
        #     # get number out of n_employees_text with regex
        #     n_employees_linkedin = int(re.findall(r'\b\d+\b|$', n_employees_text)[0])
        # except ValueError:
        #     # number was not detected properly
        #     n_employees_linkedin = None
        # except (selenium_exeptions.NoSuchElementException, IndexError):
        #     # no employees connected on linkedin
        #     n_employees_linkedin = 0

        # def _get_employee_search_results(search_container):
        #     # find and iterate through search results in list elements
        #     results_list = search_container.find_elements(By.TAG_NAME, 'ul')
        #     results_li = results_list[0].find_elements(By.TAG_NAME, 'li')
        #     for result in results_li:
        #         total.append(self.__parse_employee_search_result__(result))

        # def _check_if_not_last_page(current_search_container):
        #     # scroll to page navigation (bottom of page) so page state element can be found

        #     # get string stating current page and max pages | example 'Page 1 of 5'
        #     page_state_element = WebDriverWait(driver, 3).until(
        #         EC.presence_of_element_located((By.CLASS_NAME, 'artdeco-pagination__page-state')))
        #     # current_search_container.find_element_by_xpath('//div[@class="artdeco-pagination__page-state"]')
        #     page_state_string = page_state_element.get_attribute('textContent')
        #     # get numbers out of page string
        #     page_state = re.findall(r'\b\d+\b|$', page_state_string)
        #     if int(page_state[0]) < int(page_state[1]):
        #         return True
        #     else:
        #         return False

        # try:
        #     # go to search results page containing all employees on multiple pages
        #     driver.get(all_employees_url)
        #     # wait until search results are present
        #     search_container = WebDriverWait(driver, 3).until(
        #         EC.presence_of_element_located((By.CLASS_NAME, 'search-results-container')))
        #     _get_employee_search_results(search_container)
        #     # scroll to bottom of page to check if there are multiple pages:
        #     driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
        #     # wait to avoid robotic action
        #     time.sleep(5)
        #     if check_if_element_exists(driver, (By.CLASS_NAME, 'artdeco-pagination')):
        #         # stop as soon as 500 employees where found to avoid strings beeing to long for upload
        #         while _check_if_not_last_page(search_container):
        #             # stop if more than
        #             if len(total) > 500:
        #                 print(f'to many employees for {self.name}: more than 500 found')
        #                 break
        #             # click on next button to get to next search results page
        #             driver.find_element(By.XPATH, '//button[@aria-label="Next"]').click()
        #             # wait for the new search container to load
        #             search_container = WebDriverWait(driver, 3).until(
        #                 EC.presence_of_element_located((By.CLASS_NAME, 'search-results-container')))
        #             # get employee results
        #             _get_employee_search_results(search_container)
        #             # scroll to end of page to see if there are more pages
        #             driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
        #             # wait to avoid robotic actions discovery
        #             time.sleep(5)
        # except Exception as e:
        self.__ensure_driver_on_url(os.path.join(self.linkedin_url, "people/"))

        # _=WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, '//span[@dir="ltr"]')))

        # driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight*3/4));")
        # time.sleep(5)

        # Scroll down repeatedly until no new content is loaded
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(2)  # Adjust as needed
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        try:
            insights_employees = driver.find_element(By.CSS_SELECTOR, employees_lists_css)
            # find ul elements insight container ['employee insights', 'connected short profiles']
            results_lists = insights_employees.find_elements(By.TAG_NAME, "ul")
            results_list = results_lists[-1]  # employee list is last list in container
            employees_results_li = results_list.find_elements(By.TAG_NAME, "li")
            for res in employees_results_li:
                total.append(self.__parse_employee__(res))
        except IndexError:
            # no lists in the employees search result container
            employees_results_li = []
            results_list = []

        # def is_loaded(n_previous_results):
        #     if n_previous_results == 0:
        #         # when initial search found 0 results, there are no employees connected
        #         return False
        #     # scrolling to the end of the page and check 6 times for new elements
        #     loop = 0
        #     driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
        #     results_li = results_list.find_elements(By.TAG_NAME, "li")
        #     # stop if either: more results than previous results, loop > 6 or n_results >= n_employees_linkedin
        #     while len(results_li) == n_previous_results and loop <= 5:
        #         if (n_employees_linkedin != None and len(results_li) >= n_employees_linkedin):
        #             return False
        #         time.sleep(5)
        #         driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
        #         results_li = results_list.find_elements(By.TAG_NAME, "li")
        #         loop += 1
        #     return loop <= 5

        # def get_data(previous_results):
        #     results_li = results_list.find_elements(By.TAG_NAME, "li")
        #     for res in results_li[previous_results:]:
        #         total.append(self.__parse_employee__(res))

        # n_found_results = len(employees_results_li)
        # while is_loaded(n_found_results):
        #     try:
        #         driver.find_element(By.XPATH, next_xpath).click()
        #     except:
        #         pass
        #     _ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, employees_lists_css)))

        #     driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
        #     time.sleep(5)

        #     get_data(n_found_results)
        #     n_found_results = len(total)

        # check if all employees where found and raise warning
        if (n_employees_linkedin != None and len(total) != n_employees_linkedin):
            warnings.warn(f'{len(total)} out of {n_employees_linkedin} employees where found for {self.name}')

        # find university with most employees
        try:
            # ensure driver is on people page
            self.__ensure_driver_on_url(os.path.join(self.linkedin_url, "people/"))
            bar_list = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, list_css_carousel)))
            bar_li = bar_list.find_elements(By.TAG_NAME, "li")
            # second list element contains university information
            unis = bar_li[1]
            # find name of first university in list
            # Todo check class name after ui change
            uni_affiliation = unis.find_element(By.CLASS_NAME, "org-people-bar-graph-element__category").text
        except selenium_exeptions.NoSuchElementException:
            # Element is not present when there are no employees or no university
            uni_affiliation = None
        except selenium_exeptions.TimeoutException:
            # no bar_list element found
            # Todo does this only happen if there are no employees?
            uni_affiliation = None

        # write values into class attributes and return
        self.employees = total
        self.main_university_employees = uni_affiliation
        return

    def __repr__(self):
        # matching class attributes to airtable column names
        _output = {}
        _output['record_id'] = self.record_id
        _output['startup_name'] = self.name
        _output['linkedin_page'] = self.linkedin_url
        _output['about_us_linkedin'] = self.about_us
        _output['specialties'] = self.specialties
        _output['startup_address_raw_linkedin'] = self.startup_address_raw_linkedin
        _output['startup_follower_linkedin'] = self.startup_follower_linkedin
        _output['website_from_linkedin'] = self.website
        _output['industry_linkedin'] = self.industry
        _output['company_type'] = self.company_type
        _output['headquarters'] = self.headquarters
        _output['company_size_linkedin'] = self.company_size
        _output['main_university_employees_linkedin'] = self.main_university_employees
        _output['founding_year_linkedin'] = self.founding_year
        _output['affiliated_companies'] = self.affiliated_companies
        _output['showcase_pages'] = self.showcase_pages
        _output['employee_list_linkedin'] = self.employees
        _output['n_employees_linkedin'] = self.n_employees_linkedin

        return json.dumps(_output).replace('\n', '')
