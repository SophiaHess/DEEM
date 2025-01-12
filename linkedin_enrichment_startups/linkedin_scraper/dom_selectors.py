# CSS class selectors for element selection

PROFILE_NAME_H1 = 'text-heading-xlarge'

EXPERIENCE_LIST_CONTAINER = "pvs-list__outer-container"

# CSS XPATH definitions for element selection

PROFILE_ABOUT_SEEMORE_BUTTON = "//button[@class,'inline-show-more-text__button']"

PROFILE_ABOUT_DIV = "//div[@id='about']"

#DETAILS_SECTION = "//main[@class='scaffold-layout__main']/section" Darcy v
DETAILS_SECTION = "//div[contains(@class, 'pvs-list__container')]" #perfect


#DETAILS_ITEMS = "./div[2]/div/div[1]/ul/li"
DETAILS_ITEMS = ".//li[contains(@class, 'pvs-list__paged-list-item') and contains(@class, 'artdeco-list__item')]"


SKILLS_ITEMS = "./div[2]/div[2]/div/div/div/ul/li"

IMMEDIATE_CHILDREN_DIVS = "./div"

IMMEDIATE_CHILDREN = "./*"

FIRST_IMMEDIATE_CHILD = "./*[1]"

IMMEDIATE_GRANDCHILDREN_DIVS = "./*/div"

IMMEDIATE_PARENT = "./.."

GRANDPARENT = "../.."

GREATGRANDPARENT = "../../.."

GRANDCHILD_SPAN = "./span/span"

CHILD_SPAN = "./span"
