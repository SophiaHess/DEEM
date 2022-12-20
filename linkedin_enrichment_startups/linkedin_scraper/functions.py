import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as selenium_exceptions

def time_divide(string):
    duration = re.search("\((.*?)\)", string)

    if duration != None:
        duration = duration.group(0)
        string = string.replace(duration, "").strip()
    else:
        duration = "()"
        string = string + "––()"

    times = string.split("–")
    return (times[0].strip(), times[1].strip(), duration[1:-1])


def check_if_element_exists(driver, locator):
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located(locator))
        return True
    except selenium_exceptions.TimeoutException:
        return False
