import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .objects import Institution, Experience, Education, Scraper, Interest, Accomplishment, Contact
import os
from linkedin_scraper import selectors
import time


from linkedin_functions.linkedin_functions import parse_datestring


class Person(Scraper):

    __TOP_CARD = "pv-top-card"
    __WAIT_FOR_ELEMENT_TIMEOUT = 5
    __SHORT_WAIT_FOR_ELEMENT_TIMEOUT = 1
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
        get=True,
        scrape=True,
        close_on_complete=True,
        skills = None
    ):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about = about or []
        self.experiences = experiences or []
        self.educations = educations or []
        self.interests = interests or []
        self.honors = honors or []
        self.also_viewed_urls = []
        self.skills = skills or []
        

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

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

        print(f'Person Object Scraped for {self.name}')

    def add_about(self, about):
        self.about.append(about)

    def add_experience(self, experience):
        self.experiences.append(experience)

    def add_skill(self, skill):
        self.skills.append(skill)

    def add_education(self, education):
        self.educations.append(education)

    def add_interest(self, interest):
        self.interests.append(interest)

    def add_honor(self, honor):
        self.honors.append(honor)

    def add_location(self, location):
        self.location = location

    def add_contact(self, contact):
        self.contacts.append(contact)

    def scrape(self, close_on_complete=True):
        # Check if logged in, or if captcha/error was present and prompt user to log in
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            print("you are not logged in!")
            x = input("log in and after press any key to continue...")
            self.scrape_logged_in(close_on_complete=close_on_complete)

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        duration = None

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    self.__TOP_CARD,
                )
            )
        )

        self.name = root.find_element_by_class_name(selectors.PROFILE_NAME_H1).text.strip()

        base_url = driver.current_url

        # get About section text
        print(f'\nGetting {self.name}\'s About')
        try:
            #Get the about <div> using xpath, wait until element is present. Or if timed out then except is thrown and no about is assigned.
            about_div = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        selectors.PROFILE_ABOUT_DIV,
                    )
                )
            )

            #Get the parent element and then find the <span> element that contains the text
            about_container = about_div.find_element(By.XPATH,selectors.IMMEDIATE_PARENT)
            about = about_container.find_element_by_xpath("./div[2]/div/div/div/span").text  

        except:
            #if not present (person hasn't filled their about section)
            about = None

        if about:
            #If the about element was not None, then add it to the about attribute of the object.
            self.add_about(about.strip())


        # Experience page is structured like:
        # Labels are defined variables

        #               ┌─────────────┐
        #               │             ◄─────────┐
        #               │ ┌──┬──────┐ │         │
        #           ┌───┼─►  │      │ │         experience_section
        #           │   │ ┌──┤      │ │
        # company_img   │ │  │      │ │
        #               │ │  │      ◄─┼─────┐
        #               │ │  │      │ │     │
        #               │ └──┴──────┘ │    [experience_items]=[item,item]
        #               │             │     │
        #               │ ┌──┬──────┐ │     │
        #               │ │  │      │ │     │
        #               │ ├──┤      │ │     │
        #         ┌─────┼─┼──┼─►    ◄─┼─────┘
        #         │     │ │  │      │ │
        #         │     │ └──┴──────┘ │
        #    item_info  │             │
        #               └─────────────┘

        #

        print(f'Getting {self.name}\'s Experience')
        try:
            # Load the person's experience page, append slugs to base url
            driver.get(base_url + "details/experience")
            # Wait for page to load
            time.sleep(2)
            # Wait for the main container to load (with the list of experience elements)
            experience_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, selectors.DETAILS_SECTION)))
        except:
            experience_section = None

        time.sleep(self.__DOM_COOLDOWN)


        if experience_section is not None: 
            
            # Redefine element to avoid StaleElementReferenceException
            experience_section = driver.find_element_by_xpath(selectors.DETAILS_SECTION)

            # Get the list of each work experience
            experience_items = WebDriverWait(experience_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                EC.presence_of_all_elements_located((By.XPATH, selectors.DETAILS_ITEMS)))

            for item in experience_items:
                # Try getting the company <img> element
                try:
                    company_img = WebDriverWait(item, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(\
                    EC.presence_of_element_located((By.TAG_NAME,"img")))
                except:
                    company_img = None
                
                if company_img is None: 
                    # If the company is missing its own logo, then the structure is a bit different
                    # We can get the company url from the icon link
                    company_url = item.find_element_by_xpath("./div/div/div[1]/a").get_attribute("href")
                    
                    # If "search" is in the url, then the company doesn't have a proper linkedin page
                    if "/search/" in company_url:
                        company_url = ""
                else:
                    # If the company image does exist we can extract the name and url from the image attributes
                    company_name = company_img.get_attribute("alt").replace("logo","").strip()
                    company_url = company_img.find_element_by_xpath(selectors.GREATGRANDPARENT).get_attribute("href")
                

                # Navigate into the main experience container, getting a sub-container which contains more info
                item_info = item.find_element_by_xpath("./div/div/div[2]")
                
                # 
                # Each item_info div is structured like this.
                # Sometimes an info_item only has the info_head div, that is if the person
                # hasn't put any extra info about what the role was.

                # item_info:

                # ┌───────────────────────┐
                # │ info_head (div)       │◄──┐
                # ├───────────────────────┤   │
                # │                       │   │
                # │ info_main (div)       │   [infos] = [info_head,info_main]
                # │                       │   │
                # │                       │◄──┘
                # └───────────────────────┘               
                
                # 

                infos = item_info.find_elements_by_xpath("./div")
                
                time.sleep(self.__DOM_COOLDOWN)


                
                # If the length of infos is two, both the info_head and info_main are present
                if len(infos) == 2:

                    info_head = infos[0]
                    info_main = infos[1]
                    info_head_child = info_head.find_element_by_xpath(selectors.FIRST_IMMEDIATE_CHILD)

                    # Check if the person only has one role listed at this company
                    if info_head_child.tag_name == "div":

                        experience = Experience(
                            institution_name = company_name,
                            institution_linkedin_url = company_url)
                        role_head_elements = info_head_child.find_elements_by_xpath(selectors.IMMEDIATE_CHILDREN)
                        self.parse_role_info(experience, role_head_elements)
                        self.add_experience(experience)

                    # Otherwise different structure, and multiple roles are listed at the same company
                    else:
                        # Get company name
                        company_name = info_head.find_element_by_xpath("./a/div/span/span").text

                        # Get element list of the numerous positions at the company
                        positions_at_company = info_main.find_elements_by_xpath("./ul/li/div/div/div[1]/ul/li")
                        for position in positions_at_company:

                            # Initialise Experience object
                            experience = Experience(
                            institution_name = company_name,
                            institution_linkedin_url = company_url)
                            # Get the list of elements containing the info: length of time, role name, location
                            role_head_elements = position.find_elements_by_xpath("./div/div/div[2]/div/a/*")
                            # Parse the elements into variables and assign to the experience
                            self.parse_role_info(experience, role_head_elements)
                            
                            self.add_experience(experience)
                
                # If infos is 1, there is no info_main section i.e. the person has not put any info about their role
                # So the structure is a bit different 
                elif len(infos) == 1:
                    experience = Experience(
                            institution_name = company_name,
                            institution_linkedin_url = company_url)
                    info_head = infos[0]
                    role_head_elements = info_head.find_elements_by_xpath("./div[1]/*")
                    self.parse_role_info(experience, role_head_elements)
                    self.add_experience(experience)
            
        print(f'Getting {self.name}\'s Education')
        
        # Load education details page
        try:
            driver.get(base_url + "details/education")
            time.sleep(2)
            # Get main education container on this page
            education_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, selectors.DETAILS_SECTION)))
        except:
            education_section = None
        

        if education_section is not None:

            # Redefine element to avoid StaleElementReferenceException
            education_section = driver.find_element_by_xpath(selectors.DETAILS_SECTION)

            # Get list of each education item in the container
            education_items = WebDriverWait(education_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                EC.presence_of_all_elements_located((By.XPATH, selectors.DETAILS_ITEMS)))
            
            for item in education_items:

                item_info = item.find_element_by_xpath("./div/div/div[2]")
                infos = item_info.find_elements_by_xpath("./div")

                info_head = infos[0]

                # Extract the information about the education from various elements
                head_elements = info_head.find_elements_by_xpath("./a/*")
                name = head_elements[0].find_element_by_xpath("./span/span[1]").text
                url = info_head.find_element_by_xpath("./a").get_attribute("href")
                degree = head_elements[1].find_element_by_xpath("./span[1]").text
                timeline_text = head_elements[2].find_element_by_xpath("./span[1]").text
                
                # Convert datestring into start, end, duration and error margin
                start_str, end_str, duration_years, margin = parse_datestring(timeline_text)

                # Create education object and append to list of Educations
                education = Education(
                    from_date = start_str,
                    to_date = end_str,
                    institution_name = name,
                    institution_linkedin_url = url,
                    degree = degree,
                    duration_years = duration_years,
                    duration_margin = margin,
                    timeline_text = timeline_text
                )
                self.add_education(education)


        print(f'Getting {self.name}\'s Skills')

        # Navigate to skills page and get main skills container
        try:
            driver.get(base_url + "details/skills")
            time.sleep(2)
            skills_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, selectors.DETAILS_SECTION)))
        except:
            skills_section = None

        if skills_section is not None:
            
            # Redefine element to avoid StaleElementReferenceException
            skills_section = driver.find_element_by_xpath(selectors.DETAILS_SECTION)

            # Get a list of the elements with each skill
            try:
                skills_items = WebDriverWait(skills_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                    EC.presence_of_all_elements_located((By.XPATH, selectors.SKILLS_ITEMS)))
            except:
                skills_items = []

            # Iterate through each skill element and navigate into the heirarchy to get the text
            for item in skills_items:
                
                skill_name = item.find_element_by_xpath('./div/div/div[2]/div[1]/a/div/span/span[1]').text
                self.add_skill(skill_name)

        # Go to awards/honors page
        try:
            driver.get(base_url + "details/honors")
            time.sleep(2)
            honors_section = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, selectors.DETAILS_SECTION)))
        except:
            honors_section = None

        
        if honors_section is not None:
            
            # Redefine element to avoid StaleElementReferenceException
            honors_section = driver.find_element_by_xpath(selectors.DETAILS_SECTION)

            # Get a list of the elements with each skill
            try:
                honors_items = WebDriverWait(skills_section, self.__WAIT_FOR_ELEMENT_TIMEOUT).until( 
                    EC.presence_of_all_elements_located((By.XPATH, selectors.DETAILS_ITEMS)))
            except:
                honors_items = []

            # Iterate through each skill element and navigate into the heirarchy to get the text
            for item in honors_items:
                
                honor_name = item.find_element_by_xpath('./div/div/div[2]/div[1]/div/div/span/span').text
                self.add_honor(honor_name)



        if close_on_complete:
            driver.quit()

    def parse_role_info(self, experience, position_head_elements):

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
        try:

            #element1, the 1st line, is always the position title
            element1 = position_head_elements[0]
            experience.position_title = element1.find_element_by_xpath(selectors.GRANDCHILD_SPAN).text
            
            #element2, the 2nd line, is either the company name or the dates/duration
            element2 = position_head_elements[1]
            element2_text = element2.find_element_by_xpath("./span").text
            head, sep, tail = element2_text.partition(' · ')

            #we can tell if it is the company name or dates, if the text colour is black
            #i.e if the div doesn't have the "t-black--light" class then it is the company name
            if "t-black--light" not in element2.get_attribute("class"):
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
            element3 = position_head_elements[2]
            element3_text = element3.find_element_by_xpath("./span").text
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

            #element4 is always the location
            element4 = position_head_elements[3]
            element4_text = element4.find_element_by_xpath("./span").text 
            experience.location = element4_text

        #since not all of these lines may be there, we return from the function
        #if there is an error (i.e. element wasnt present)
        except:
            return


    @property
    def company(self):
        if self.experiences:
            return (
                self.experiences[0].institution_name
                if self.experiences[0].institution_name
                else None
            )
        else:
            return None

    @property
    def job_title(self):
        if self.experiences:
            return (
                self.experiences[0].position_title
                if self.experiences[0].position_title
                else None
            )
        else:
            return None

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
