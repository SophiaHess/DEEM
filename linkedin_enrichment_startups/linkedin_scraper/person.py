import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.color import Color
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup


import os
import time
from random import randint
import traceback
import re
import json
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
sys.path.append(os.path.dirname(os.path.dirname(SCRIPT_DIR)))

import objects
import dom_selectors
import exceptions 
from linkedin_founders.scraping_helpers import *
from founders.helpers import clean_linkedin_url


class Person(objects.Scraper):

    __TOP_CARD = "artdeco-card"
    __WAIT_FOR_ELEMENT_TIMEOUT = 8
    __DOM_COOLDOWN = 1
    

    def __init__(
        self,
        linkedin_url=None,
        name=None,
        about=None,
        experiences=None,
        educations=None,
        interests=None,
        accomplishments=None,
        company=None,
        job_title=None,
        contacts=None,
        driver=None,
        honors=None,
        certifications=None,
        volunteers=None,
        scrape=True,
        close_on_complete=True,
        skills = None,
        error_file = None,
        record_id = None,
        add_delays = False
    ):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about = about or ""
        self.experiences = experiences or []
        self.educations = educations or []
        self.interests = interests or []
        self.honors = honors or []
        self.also_viewed_urls = []
        self.skills = skills or []
        self.certifications = certifications or []
        self.volunteer_experiences = volunteers or []
        self.error_file = error_file
        self.record_id = record_id
        self.scraping_successful = False
        self.add_delays = add_delays or False

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(
                        os.path.dirname(__file__), "drivers/chromedriver"
                    )
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

        if self.scraping_successful:
            print(f'Person Object Scraped for {self.name}')
        else:
            print(f'Scraping Unsuccessful for {self.name}')

    def add_about(self, about):
        self.about = about

    def add_experience(self, experience):
        self.experiences.append(experience)

    def add_skills(self, skill):
        self.skills.extend(skill)

    def add_education(self, education):
        self.educations.append(education)

    def add_interest(self, interest):
        self.interests.append(interest)

    def add_honors(self, honor):
        self.honors.extend(honor)

    def add_certification(self, certification):
        self.certifications.append(certification)

    def add_volunteer_experiences(self, volunteer):
        self.volunteer_experiences.append(volunteer)


    def add_location(self, location):
        self.location = location

    def scrape(self, close_on_complete=True):
        # Check if logged in, or if captcha/error was present and prompt user to log in
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            self.scrape_logged_in(close_on_complete=close_on_complete)

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        duration = None
        if "https://" not in self.linkedin_url:
            self.linkedin_url = "https://"  + self.linkedin_url
            
        driver.get(self.linkedin_url)
        time.sleep(self.__DOM_COOLDOWN)

        try:
            
            if '/404/' in driver.current_url:
                raise exceptions.InvalidFounderURLException
            
            root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.CLASS_NAME,
                        self.__TOP_CARD,
                    )
                )
            )

        
               
            #self.name = root.find_element(By.CLASS_NAME, dom_selectors.PROFILE_NAME_H1).text.strip()
            try:
                self.name = root.find_element(By.TAG_NAME, 'h1').text.strip()
            except Exception:
                # Try XPath as a fallback
                self.name = WebDriverWait(root, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'inline') and contains(@class, 'break-words')]"))
                            ).text.strip()
            

            base_url = clean_linkedin_url(driver.current_url) + '/'

            WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')

            time.sleep(3)
            
            about_present = len(driver.find_elements(By.ID, "about")) > 0
            experience_present = len(driver.find_elements(By.ID, "experience")) > 0
            education_present = len(driver.find_elements(By.ID, "education")) > 0
            skills_present = len(driver.find_elements(By.ID, "skills")) > 0
            honors_present = len(driver.find_elements(By.ID, "honors_and_awards")) > 0
            certs_present = len(driver.find_elements(By.ID, "licenses_and_certifications")) > 0
            volunteering_present = len(driver.find_elements(By.ID, "volunteering_experience")) > 0

            founder_location = driver.find_element(By.XPATH,'//*[@id="profile-content"]/div/div[2]/div/div/main/section/div[2]/div[2]/div[2]/span[1]').text
            if founder_location:
                #If the about element was not None, then add it to the about attribute of the object.
                self.add_location(founder_location.strip())

            if about_present:
                # get About section text
                print(f'\nGetting {self.name}\'s About\n')
                try:
                    #Get the about <div> using xpath, wait until element is present. Or if timed out then except is thrown and no about is assigned.
                    about_div = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                dom_selectors.PROFILE_ABOUT_DIV,
                            )
                        )
                    )

                    #Get the parent element and then find the <span> element that contains the text
                    about_container = get_parent_element(driver, about_div)
                    about = about_container.find_element(By.XPATH, "./div[3]/div/div/div/span[1]").text  

                except:
                    #if not present (person hasn't filled their about section)
                    about = None
            else:
                about = None

            if about:
                #If the about element was not None, then add it to the about attribute of the object.
                self.add_about(about.strip())

            if experience_present:
                print(f'Getting {self.name}\'s Experience\n')
                try:
                    # Load the person's experience page, append slugs to base url
                    driver.get(base_url + "details/experience")

                    

                    # Wait for the main container to load (with the list of experience elements)
                    experience_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.visibility_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                    # print("Experience section found successfully.")
                except:
                    experience_section = None
                    #print("Saving page source for debugging...")
                    # with open("debug_experience_section.html", "w", encoding="utf-8") as f:
                    #     f.write(driver.page_source)  # Save the page for manual inspection
                    


            else:
                experience_section = None

            if self.add_delays:
                time.sleep(randint(1,3))

            

            if experience_section is not None: 
                
                # Redefine element to avoid StaleElementReferenceException
                experience_section = driver.find_element(By.XPATH, dom_selectors.DETAILS_SECTION)
                # print(experience_section.text) 
                try:
                    # Get the list of each work experience
                    experience_items = WebDriverWait(experience_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                        EC.presence_of_all_elements_located((By.XPATH, dom_selectors.DETAILS_ITEMS)))
                
                except StaleElementReferenceException:
                    experience_section = driver.find_element(By.XPATH, dom_selectors.DETAILS_SECTION)
                    experience_items = WebDriverWait(experience_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                        EC.presence_of_all_elements_located((By.XPATH, dom_selectors.DETAILS_ITEMS)))
                
                

                for item in experience_items:
                    # Try getting the company <img> element

                    if "Career Break" in item.text:
                        continue

                    try:
                        company_img = item.find_elements(By.TAG_NAME, "img")[0]
                    except:
                        company_img = None
                    
                    if company_img is None: 
                        ch = get_first_child_element(driver, item.find_element(By.XPATH, "./div/div/div[1]"))
                        if ch.tag_name != 'a':
                            company_url = ''
                            company_name = ''
                        else:
                            # If the company is missing its own logo, then we can get the company url from the icon link
                            company_url = item.find_element(By.XPATH, "./div/div/div[1]/a").get_attribute("href")
                            company_name = ""
                        # If "search" is in the url, then the company doesn't have a proper linkedin page
                        if "/search/" in company_url:
                            company_url = ""
                    else:
                        # If the company image does exist we can extract the name and url from the image attributes
                        company_name = company_img.get_attribute("alt").replace("logo","").strip()
                        company_url = company_img.find_element(By.XPATH, dom_selectors.GREATGRANDPARENT).get_attribute("href")
                    
                    

                    # Navigate into the main experience container, getting a sub-container which contains more info
                    infos = item.find_elements(By.XPATH, "./div/div/div[2]/div")

                    info_head = infos[0]
                    if len(infos) > 1:
                        info_main = infos[1]

                    info_head_html = get_inner_html_of_element(driver, info_head)
                    head_soup = BeautifulSoup(info_head_html, features="lxml")

                    # Check if the person only has one role listed at this company
                    if head_soup.select_one("html > body > *").name == "div":

                        experience = objects.Experience(
                            institution_name = company_name,
                            institution_linkedin_url = company_url)

                        role_head_elements = head_soup.select("html > body > div:first-child > *")
                        
                        if len(infos) == 2:
                            experience.text_description = info_main.text.strip()
                        self.parse_role_info(experience, role_head_elements)
                        self.add_experience(experience)
                        

                    # Otherwise different structure, and multiple roles are listed at the same company
                    else:

                        # Get company name
                        company_location = None
                        if head_soup.body.a.div.span.span is None:
                            company_name = head_soup.body.a.div.span.text
                        else:
                            company_name = head_soup.body.a.div.span.span.text

                        company_location_elems = head_soup.body.select('a > span.t-black--light')
                        if len(company_location_elems) > 0:
                            company_location = company_location_elems[0].span.text

                        # Get element list of the numerous positions at the company
                        info_main_html = get_inner_html_of_element(driver, info_main)
                        main_soup = BeautifulSoup(info_main_html, features="lxml")

                        positions = main_soup.body.select("ul > li > div > div > div:first-child > ul > li")

                        for position in positions:

                            # Initialise Experience object
                            experience = objects.Experience(
                            institution_name = company_name,
                            institution_linkedin_url = company_url)

                            if company_location:
                                experience.location = company_location

                            role_text_description = position.select("li > div > div > div:nth-child(2) > div:nth-child(2) span[aria-hidden='true']")
                            if len(role_text_description) > 0:
                                experience.text_description = role_text_description[0].text.strip()

                            # Get the list of elements containing the info: length of time, role name, location
                            role_head_elements = position.select("li > div > div > div:nth-child(2) > div:first-child > a > *")
                            # Parse the elements and assign to the experience
                            self.parse_role_info(experience, role_head_elements, multiple_roles_at_cmp=True)

                            self.add_experience(experience)



            if education_present:
                print(f'Getting {self.name}\'s Education')
                
                # Load education details page
                try:
                    driver.get(base_url + "details/education")
                    # Get main education container on this page
                    education_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                except:
                    education_section = None
            else:
                education_section = None
            


            if self.add_delays:
                time.sleep(randint(1,3))

            if education_section is not None:

                # Redefine element to avoid StaleElementReferenceException
                education_section = driver.find_element(By.XPATH, dom_selectors.DETAILS_SECTION)

                try:
                    # Get the list of each work experience
                    education_items = WebDriverWait(education_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                        EC.presence_of_all_elements_located((By.XPATH, dom_selectors.DETAILS_ITEMS)))
                
                except StaleElementReferenceException:
                    education_section = driver.find_element(By.XPATH, dom_selectors.DETAILS_SECTION)
                    education_items = WebDriverWait(education_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                        EC.presence_of_all_elements_located((By.XPATH, dom_selectors.DETAILS_ITEMS)))
                
            
                
                for item in education_items:

                    item_info = item.find_element(By.XPATH, "./div/div/div[2]")
                    infos = item_info.find_elements(By.XPATH, "./div")

                    info_head = infos[0]

                    # Extract the information about the education from various elements
                    head_elements = info_head.find_elements(By.XPATH, "./a/*")

                    # Create education object, parse info and append to list of Educations
                    education = objects.Education()
                    self.parse_details_info(education, head_elements, 'education')

                    if len(infos) > 1:
                        info_main = infos[1]
                        education.text_description = info_main.text.strip()
                    self.add_education(education)
            

            if self.add_delays:
                time.sleep(randint(1,3))

            if skills_present:
                time.sleep(self.__DOM_COOLDOWN)
                print(f'Getting {self.name}\'s Skills')

                # Navigate to skills page and get main skills container
                try:
                    driver.get(base_url + "details/skills")
                    skills_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                except:
                    skills_section = None

                if skills_section is not None:
                    time.sleep(self.__DOM_COOLDOWN)
                    # Redefine element to avoid StaleElementReferenceException
                    skills_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                    skills_html = get_inner_html_of_element(driver, skills_section)
                    skills_soup = BeautifulSoup(skills_html, features="lxml")
                    
                    #List of all skill elements containing text
                    skills_els = skills_soup.html.body.select("div:nth-child(2) > div:nth-child(2) > div > div > div:first-child > ul > li > div > div > div:nth-child(2) > div:first-child")
                    [[j.decompose() for j in i.select(".visually-hidden")] for i in skills_els]

                    # Iterate through each skill element and navigate into the heirarchy to get the text
                    self.add_skills([i.text.strip() for i in skills_els])
            

            if self.add_delays:
                time.sleep(randint(1,3))

            if honors_present:
                time.sleep(self.__DOM_COOLDOWN)
                print(f'Getting {self.name}\'s Honors')
                # Go to awards/honors page
                try:
                    driver.get(base_url + "details/honors")
                    honors_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                except:
                    honors_section = None

                
                if honors_section is not None:
                    time.sleep(self.__DOM_COOLDOWN)
                    # Redefine element to avoid StaleElementReferenceException
                    honors_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                    honors_html = get_inner_html_of_element(driver, honors_section)
                    honors_soup = BeautifulSoup(honors_html, features="lxml")
                    [j.decompose() for j in honors_soup.select(".visually-hidden")]

                    honors_els = honors_soup.html.body.select("div:nth-child(2) > div > div > ul > li")
                    honors = [i.text.strip() for i in honors_els]

                    self.add_honors(honors)

            

            if self.add_delays:
                time.sleep(randint(1,3))

            if certs_present:
                time.sleep(self.__DOM_COOLDOWN)
                print(f'Getting {self.name}\'s Certifications')
                # Go to certifications page
                try:
                    driver.get(base_url + "details/certifications")
                    certs_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                except:
                    certs_section = None

                
                if certs_section is not None:
                    
                    # Redefine element to avoid StaleElementReferenceException
                    certs_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                    # Get a list of the elements with each certification
                    try:
                        certs_items = WebDriverWait(certs_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                            EC.presence_of_all_elements_located((By.XPATH, dom_selectors.DETAILS_ITEMS)))
                    except:
                        certs_items = []

                    # Iterate through each certification element and navigate into the heirarchy to get the text
                    for item in certs_items:
                        if len(item.find_elements(By.XPATH, './div/section')) > 0 :
                            break
                        else:
                            cert_text = item.text.strip()
                            self.add_certification((cert_text))


            if self.add_delays:
                time.sleep(randint(1,3))
            
            if volunteering_present:
                time.sleep(self.__DOM_COOLDOWN)
                # Go to volunteering page
                try:
                    driver.get(base_url + "details/volunteering-experiences")
                    volunt_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, dom_selectors.DETAILS_SECTION)))
                except:
                    volunt_section = None

                
                if volunt_section is not None:
                    
                    # Redefine element to avoid StaleElementReferenceException
                    volunt_section = driver.find_element(By.XPATH, dom_selectors.DETAILS_SECTION)

                    # Get a list of the elements with each volunteer
                    try:
                        volunt_items = WebDriverWait(volunt_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                            EC.presence_of_all_elements_located((By.XPATH, dom_selectors.DETAILS_ITEMS)))
                    except:
                        volunt_items = []

                    # Iterate through each volunteer element and navigate into the heirarchy to get the text
                    for item in volunt_items:
                        
                        item_info = item.find_element(By.XPATH, "./div/div/div[2]")
                        infos = item_info.find_elements(By.XPATH, "./div")

                        info_head = infos[0]

                        # Extract the information about the education from various elements
                        head_elements = info_head.find_elements(By.XPATH, "./div/*")

                        # Create education object, parse info and append to list of Educations
                        volunteer = objects.Volunteer()
                        self.parse_details_info(volunteer, head_elements, 'volunteer')
                        self.add_volunteer_experiences(volunteer)


            self.scraping_successful = True

        except Exception as e:
            
            self.output_error(e)

        if close_on_complete:
            driver.quit()

    def parse_details_info(self, details_object, head_elements, details_type):

        # Iterate through each head element
        for el in head_elements:
            
            el_classes = el.get_attribute("class")
            text_content = el.text.partition('\n')[0]

            #Check if the current element is bold, i.e. the first in the item
            has_bold_class = (el.value_of_css_property("font-weight") == "600")
            if has_bold_class:
                # Get the parent element
                parent = el.find_element(By.XPATH, dom_selectors.IMMEDIATE_PARENT)
                
                if details_type == 'education':
                    url = parent.get_attribute("href")
                    details_object.institution_name = text_content
                    # If the url contains "search", it means the education institution doesnt have an official page on linkedin (or the user didnt select it from the drop down)
                    # So only store the linkedin url if it is a real linkedin profile page
                    if "/search/" not in url:
                        details_object.institution_linkedin_url = url
                elif details_type == 'volunteer':
                    details_object.role_title = text_content

                # Continue to next element in iteration
                continue

            
            if "t-black--light" not in el_classes:
                #text is black, not grey
                if details_type == "education":
                    details_object.degree = text_content
                if details_type == "volunteer":
                    details_object.institution_name = text_content
                continue

            if bool(re.search(r'\d', text_content)):
                text_content = text_content.partition('·')[0].strip()
                details_object.timeline_text = text_content
                start_str, end_str, duration_years, margin = parse_datestring(text_content)
                details_object.from_date = start_str
                details_object.to_date = end_str
                details_object.duration_years = duration_years
                details_object.duration_margin = margin
                continue
            
            details_object.field = text_content

    def output_error(self, e):
        print(f" Problem with {self.name} --> {e}")
        case = {
            "founder_name": self.name,
            "error_message": traceback.format_exc()
        }
        json.dump(case, self.error_file, ensure_ascii=False, indent=4)



    def remove_newline_from_str(string):
        return string.partition('\n')[0]


    def parse_role_info(self, experience, position_head_elements, multiple_roles_at_cmp=False):

        """
        position_head_elements is a section on the linkedin experience page
        that looks like this:

        Position Name
        Institution
        Apr 2021 - Oct 2022 · 1 yr 7 mos
        City, State
        

        However sometimes, one or more of these lines could be missing.
        The months in the dates could also be missing
        So we need to also be able to handle any of the following:

        | Position Name
        | Institution

        | Position Name
        | Month 2021 - Month 2022 · 1 yr 7 mos

        | Position Name
        | 2020 - 2020 · Less than a year

        | Position Name
        | Apr 2018 - Mar 2020 · 2 yrs
        | Stuttgart

        """
        # START_TIME = time.time()
        try:
            #Remove hidden elements
            [[j.decompose() for j in i.select(".visually-hidden")] for i in position_head_elements]
            #element1, the 1st line, is always the position title
            experience.position_title = position_head_elements[0].text.strip()
            
            #element2, the 2nd line, is either the company name or work type or the dates/duration
            element2_text = position_head_elements[1].text.strip()
            head, sep, tail = element2_text.partition(' · ')

            #we can tell if it is the company name or dates, if the text colour is black then it is company name or work type
            #i.e if the div doesn't have the "t-black--light" class then it is the company name
            if "t-black--light" not in position_head_elements[1].get("class"):
                if not multiple_roles_at_cmp:
                    experience.institution_name = head
            else:
                experience.timeline_text = head
                start_str, end_str, duration_years, margin = parse_datestring(head)
                experience.from_date = start_str
                experience.to_date = end_str
                experience.duration_years = duration_years
                experience.duration_margin = margin

            #element3, the 3rd line, is either the dates/duration, or location
            # if it has the ' · ' separator, then it is the dates and duration
            element3_text = position_head_elements[2].text.strip()
            if ' · ' in element3_text:
                head, sep, tail = element3_text.partition(' · ')
                experience.timeline_text = head
                start_str, end_str, duration_years, margin = parse_datestring(head)
                experience.from_date = start_str
                experience.to_date = end_str
                experience.duration_years = duration_years
                experience.duration_margin = margin

            else:
                experience.location = element3_text

            #element4 is always the location, if it exists
            element4_text = position_head_elements[3].text.strip()
            experience.location = element4_text

        #since not all of these lines may be there, we return from the function
        #if there is an error (i.e. element wasnt present)
        except:

            return


    def __repr__(self):
        return "{name}\n\nAbout\n{about}\n\nExperience\n{exp}\n\nEducation\n{edu}\n\nInterest\n{int}\n\nAccomplishments\n{acc}\n\nContacts\n{conn}".format(
            name=self.name,
            about=self.about,
            exp=self.experiences,
            edu=self.educations,
            int=self.interests,
            acc=self.accomplishments,
            conn=self.contacts,
        )

