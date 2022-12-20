import requests
import selenium.common.exceptions as selenium_exeptions
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from .objects import Scraper
from .person import Person
from .functions import check_if_element_exists
import time
import os
import json
import re
import warnings

AD_BANNER_CLASSNAME = ('ad-banner-container', '__ad')


def getchildren(elem):
    return elem.find_elements_by_xpath(".//*")


class CompanySummary(object):
    linkedin_url = None
    name = None
    followers = None

    def __init__(self, linkedin_url=None, name=None, followers=None):
        self.linkedin_url = linkedin_url
        self.name = name
        self.followers = followers

    def __repr__(self):
        if self.followers is None:
            return """ {name} """.format(name=self.name)
        else:
            return """ {name} {followers} """.format(name=self.name, followers=self.followers)


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
    main_university_employees = None
    employees = []
    showcase_pages = []
    affiliated_companies = []

    def __init__(self, linkedin_url=None, record_id=None, name=None, about_us=None, website=None, headquarters=None,
                 founding_year=None, industry=None, company_type=None, company_size=None, specialties=None,
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
        self.main_university_employees = main_university_employees
        self.employees = employees
        self.showcase_pages = showcase_pages
        self.affiliated_companies = affiliated_companies

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") is None:
                    driver_path = os.path.join(os.path.dirname(__file__), 'drivers/chromedriver')
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        driver.get(linkedin_url)
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
        return self.__get_text_under_subtitle(driver.find_element_by_class_name(class_name))

    def __parse_employee__(self, employee_raw):
        try:
            employee_object = {}
            employee_object['name'] = (employee_raw.text.split("\n") or [""])[0].strip()
            employee_object['designation'] = (employee_raw.text.split("\n") or [""])[3].strip()
            employee_object['linkedin_url'] = employee_raw.find_element_by_tag_name("a").get_attribute("href")
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
            #print(e)
            return None

    def __parse_employee_search_result__(self, employee_raw):
        try:
            employee_object = {}
            employee_object['name'] = (employee_raw.text.split("\n") or [""])[0].strip()
            # dropout if name is just 'LinkedIn Member'
            if employee_object['name'] == 'LinkedIn Member':
                return None
            employee_object['designation'] = \
                employee_raw.find_element_by_class_name("entity-result__primary-subtitle").text.strip()
            employee_object['linkedin_url'] = employee_raw.find_element_by_tag_name("a").get_attribute("href")
            return employee_object

        except Exception as e:
            return None

    def __get_attributes_about_page(self):
        driver = self.driver
        driver.get(os.path.join(self.linkedin_url, "about"))
        # get all labels and values
        # Todo after UI change: find class name of section containing information on about page of company
        grid = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'artdeco-card.p5.mb4')))

        labels = grid.find_elements_by_tag_name("dt")
        values = grid.find_elements_by_tag_name("dd")
        num_attributes = min(len(labels), len(values))
        return labels, values, num_attributes, grid

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
        driver = self.driver

        # open company url if not already current url
        if driver.current_url != self.linkedin_url:
            driver.get(self.linkedin_url)

        _ = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, '//span[@dir="ltr"]')))

        self.name = driver.find_element_by_xpath('//span[@dir="ltr"]').text.strip()

        # get information from about tab
        if website_only:
            self.get_website()
        else:
            self.get_about_us_information()

        if get_employees:
            self.get_employees_information()

        if close_on_complete:
            driver.close()

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
            self.name = driver.find_element_by_class_name("name").text.strip()
        except selenium_exeptions.NoSuchElementException:
            self.name = None
        try:
            self.about_us = driver.find_element_by_class_name("basic-info-description").text.strip()
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
            self.headquarters = driver.find_element_by_class_name("adr").text.strip()
        except selenium_exeptions.NoSuchElementException:
            self.headquarters = None
        try:
            self.industry = driver.find_element_by_class_name("industry").text.strip()
        except selenium_exeptions.NoSuchElementException:
            self.industry = None
        try:
            self.company_size = driver.find_element_by_class_name("company-size").text.strip()
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

        # get showcase
        try:
            driver.find_element_by_id("view-other-showcase-pages-dialog").click()
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'dialog')))

            showcase_pages = driver.find_elements_by_class_name("company-showcase-pages")[1]
            for showcase_company in showcase_pages.find_elements_by_tag_name("li"):
                name_elem = showcase_company.find_element_by_class_name("name")
                companySummary = CompanySummary(
                    linkedin_url=name_elem.find_element_by_tag_name("a").get_attribute("href"),
                    name=name_elem.text.strip(),
                    followers=showcase_company.text.strip().split("\n")[1]
                )
                self.showcase_pages.append(companySummary)
            driver.find_element_by_class_name("dialog-close").click()
        except:
            pass

        # affiliated company
        try:
            affiliated_pages = driver.find_element_by_class_name("affiliated-companies")
            for i, affiliated_page in enumerate(
                    affiliated_pages.find_elements_by_class_name("affiliated-company-name")):
                if i % 3 == 0:
                    affiliated_pages.find_element_by_class_name("carousel-control-next").click()

                companySummary = CompanySummary(
                    linkedin_url=affiliated_page.find_element_by_tag_name("a").get_attribute("href"),
                    name=affiliated_page.text.strip()
                )
                self.affiliated_companies.append(companySummary)
        except:
            pass

        if get_employees:
            self.employees = self.get_employees_information()

        driver.get(self.linkedin_url)

        if close_on_complete:
            driver.close()

    def get_website(self):
        labels, values, num_attributes, *_ = self.__get_attributes_about_page()
        # iterate through labels until we find website and return
        for i in range(num_attributes):
            txt = labels[i].text.strip()
            if txt == 'Website':
                self.website = values[i].text.strip()
                return
        return

    def get_about_us_information(self):
        labels, values, num_attributes, grid = self.__get_attributes_about_page()
        # iterate through labels and save corresponding values
        x_off = 0
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

        descWrapper = grid.find_elements_by_tag_name("p")
        if len(descWrapper) > 0:
            self.about_us = descWrapper[0].text.strip()

        #driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")

        # try:
        #     _ = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'company-list')))
        #     showcase, affiliated = driver.find_elements_by_class_name("company-list")
        #     driver.find_element_by_id("org-related-companies-module__show-more-btn").click()
        #
        #     # get showcase
        #     for showcase_company in showcase.find_elements_by_class_name("org-company-card"):
        #         companySummary = CompanySummary(
        #             linkedin_url=showcase_company.find_element_by_class_name("company-name-link").get_attribute("href"),
        #             name=showcase_company.find_element_by_class_name("company-name-link").text.strip(),
        #             followers=showcase_company.find_element_by_class_name("company-followers-count").text.strip()
        #         )
        #         self.showcase_pages.append(companySummary)
        #
        #     # affiliated company
        #
        #     for affiliated_company in showcase.find_elements_by_class_name("org-company-card"):
        #         companySummary = CompanySummary(
        #             linkedin_url=affiliated_company.find_element_by_class_name("company-name-link").get_attribute(
        #                 "href"),
        #             name=affiliated_company.find_element_by_class_name("company-name-link").text.strip(),
        #             followers=affiliated_company.find_element_by_class_name("company-followers-count").text.strip()
        #         )
        #         self.affiliated_companies.append(companySummary)
        #
        # except:
        #     pass

    def get_employees_information(self, wait_time=10):
        """returns employee information and university affiliation from people page"""
        total = []
        list_css = "list-style-none"  # class for elements under barcharts containing short employee profiles
        list_css_carousel = "artdeco-carousel__content"  # class for element containing barcharts about university
        next_xpath = '//button[@aria-label="Next"]'
        driver = self.driver

        # get number of employees on linkedin from top of page
        try:
            connections_section = driver.find_element_by_class_name('mt1')
            # get last link in connections section
            connections_links = connections_section.find_elements_by_tag_name('a')
            all_employees_link = connections_links[-1]
            n_employees_text = all_employees_link.text
            all_employees_url = all_employees_link.get_attribute('href')
            # get number out of n_employees_text with regex
            n_employees_linkedin = int(re.findall(r'\b\d+\b|$', n_employees_text)[0])
        except ValueError:
            # number was not detected properly
            n_employees_linkedin = None
        except (selenium_exeptions.NoSuchElementException, IndexError):
            # no employees connected on linkedin
            n_employees_linkedin = 0

        def _get_employee_search_results(search_container):
            # find and iterate through search results in list elements
            results_list = search_container.find_elements_by_tag_name('ul')
            results_li = results_list[0].find_elements_by_tag_name('li')
            for result in results_li:
                total.append(self.__parse_employee_search_result__(result))

        def _check_if_not_last_page(current_search_container):
            # scroll to page navigation (bottom of page) so page state element can be found

            # get string stating current page and max pages | example 'Page 1 of 5'
            page_state_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'artdeco-pagination__page-state')))
                #current_search_container.find_element_by_xpath('//div[@class="artdeco-pagination__page-state"]')
            page_state_string = page_state_element.get_attribute('textContent')
            # get numbers out of page string
            page_state = re.findall(r'\b\d+\b|$', page_state_string)
            if int(page_state[0]) < int(page_state[1]):
                return True
            else:
                return False

        try:
            # go to search results page containing all employees on multiple pages
            driver.get(all_employees_url)
            # wait until search results are present
            search_container = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'search-results-container')))
            _get_employee_search_results(search_container)
            # scroll to bottom of page to check if there are multiple pages:
            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
            # wait to avoid robotic action
            time.sleep(4)
            if check_if_element_exists(driver, (By.CLASS_NAME, 'artdeco-pagination')):
                while _check_if_not_last_page(search_container):
                    # click on next button to get to next search results page
                    driver.find_element_by_xpath('//button[@aria-label="Next"]').click()
                    # wait for the new search container to load
                    search_container = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'search-results-container')))
                    # get employee results
                    _get_employee_search_results(search_container)
                    # scroll to end of page to see if there are more pages
                    driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
                    # wait to avoid robotic actions discovery
                    time.sleep(3)
            # go back to people page
            driver.get(os.path.join(self.linkedin_url, "people"))
        except Exception as e:
            driver.get(os.path.join(self.linkedin_url, "people"))

            _ = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, '//span[@dir="ltr"]')))

            driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight*3/4));")
            time.sleep(1)

            results_list = driver.find_element_by_class_name(list_css)
            results_li = results_list.find_elements_by_tag_name("li")
            for res in results_li:
                total.append(self.__parse_employee__(res))

            def is_loaded(previous_results):
                # scrolling to the end of the page and check 6 times for new elements
                loop = 0
                driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
                results_li = results_list.find_elements_by_tag_name("li")
                # stop if either: more results than previous results, loop > 6 or n_results >= n_employees_linkedin
                while len(results_li) == previous_results and loop <= 5:
                    if (n_employees_linkedin != None and len(results_li) >= n_employees_linkedin):
                        return False
                    time.sleep(1)
                    driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
                    results_li = results_list.find_elements_by_tag_name("li")
                    loop += 1
                return loop <= 5

            def get_data(previous_results):
                results_li = results_list.find_elements_by_tag_name("li")
                for res in results_li[previous_results:]:
                    total.append(self.__parse_employee__(res))

            results_li_len = len(results_li)
            while is_loaded(results_li_len):
                try:
                    driver.find_element_by_xpath(next_xpath).click()
                except:
                    pass
                _ = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, list_css)))

                driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight*2/3));")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight*3/4));")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
                time.sleep(1)

                get_data(results_li_len)
                results_li_len = len(total)

        # check if all employees where found and raise warning
        if (n_employees_linkedin != None and len(total) == n_employees_linkedin):
            pass
        else:
            warnings.warn(f'{len(total)} out of {n_employees_linkedin} employees where found for {self.name}')

        # find university with most employees
        try:
            bar_list = driver.find_element_by_class_name(list_css_carousel)
            bar_li = bar_list.find_elements_by_tag_name("li")
            # second list element contains university information
            unis = bar_li[1]
            # find name of first university in list
            # Todo check class name after ui change
            uni_affiliation = unis.find_element_by_class_name("org-people-bar-graph-element__category").text
        except selenium_exeptions.NoSuchElementException:
            # Element is not present when there are no employees or no university
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
        _output['n_linkedin_employees'] = len(self.employees)

        return json.dumps(_output).replace('\n', '')
