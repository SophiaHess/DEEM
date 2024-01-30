from dataclasses import dataclass
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import selenium.common.exceptions as selenium_exeptions
from selenium.webdriver import Chrome

import constants as c


@dataclass
class Contact:
    name: str = None
    occupation: str = None
    url: str = None


@dataclass
class Institution:
    institution_name: str = None
    institution_linkedin_url: str = None


@dataclass
class Experience(Institution):
    from_date: str = None
    to_date: str = None
    position_title: str = None
    location: str = None
    timeline_text: str = None
    duration_years: float = 0
    duration_margin: float = 0
    text_description: str = None

@dataclass
class Education(Institution):
    from_date: str = None
    to_date: str = None
    degree: str = None
    timeline_text: str = None
    duration_years: float = 0
    duration_margin: float = 0
    text_description: str = None


@dataclass
class Volunteer(Institution):
    from_date: str = None
    to_date: str = None
    field: str = None
    position_title: str = None
    duration_years: float = 0
    duration_margin: float = 0


@dataclass
class Interest(Institution):
    title = None


@dataclass
class Accomplishment(Institution):
    category = None
    title = None


@dataclass
class Scraper:
    driver: Chrome = None

    def is_signed_in(self):
        try:
            # wait for max of 5 seconds or until Verify Login ID is found raises Timeout error if fails
            WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.ID, c.VERIFY_LOGIN_ID)))
            return True
        except selenium_exeptions.TimeoutException:
            pass
        return False

    def __find_element_by_class_name__(self, class_name):
        try:
            self.driver.find_element(By.CLASS_NAME, class_name)
            return True
        except:
            pass
        return False

    def __find_element_by_xpath__(self, tag_name):
        try:
            self.driver.find_element(By.XPATH, tag_name)
            return True
        except:
            pass
        return False

    def __find_enabled_element_by_xpath__(self, tag_name):
        try:
            elem = self.driver.find_element(By.XPATH, tag_name)
            return elem.is_enabled()
        except:
            pass
        return False

    @classmethod
    def __find_first_available_element__(cls, *args):
        for elem in args:
            if elem:
                return elem[0]
