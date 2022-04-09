import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.common.keys import Keys

# Settings
options = webdriver.ChromeOptions()
prefs = {"profile.default_content_setting_values.notifications": 2}
options.add_experimental_option("prefs", prefs)
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
driver.get("https://gtest2.amocrm.ru/settings/widgets/")


class ActionsWithElements:

    def __init__(self, XPATH):
        self.XPATH = XPATH

    def find_element(self):
        driver.find_element(By.XPATH, self.XPATH)

    def click_the_button(self):
        driver.find_element(By.XPATH, self.XPATH).click()

    def search_for_button_on_a_page(self):
        element = driver.find_element(By.XPATH, self.XPATH)
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()

    def search_for_button_and_click(self):
        element = driver.find_element(By.XPATH, self.XPATH)
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        element.click()


class SendKeys(ActionsWithElements):

    def __init__(self, XPATH, value):
        self.XPATH = XPATH
        self.value = value

    def find_element(self):
        driver.find_element(By.XPATH, self.XPATH).send_keys(self.value)


#scroll_down
def scroll_down(self):
    # Get scroll height.
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:

        # Scroll down to the bottom.
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load the page.
        time.sleep(2)

        # Calculate new scroll height and compare with last scroll height.
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break

        last_height = new_height



# scroll up
def scroll_up():
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)

def take_screenshot(test_name):
    """ Take screenshot. Call it when test failed """
    dt_now = datetime.datetime.now()
    screenshot_basename = '{:%d_%m_%Y_%H_%M_%S}_{}.png'.format(dt_now, test_name)
    driver.save_screenshot(screenshot_basename)


