import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait


from selenium.webdriver.common.keys import Keys

# turn off notifications
options = webdriver.ChromeOptions()
prefs = {"profile.default_content_setting_values.notifications": 2}
options.add_experimental_option("prefs", prefs)
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
driver.get("https://gtest2.amocrm.ru/settings/widgets/")


def find_element(XPATH):
    driver.find_element(By.XPATH, XPATH)


def click_the_button(XPATH):
    driver.find_element(By.XPATH, XPATH).click()


def search_for_button_on_a_page(XPATH):
    element = driver.find_element(By.XPATH, XPATH)
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()


def search_for_button_and_click(XPATH):
    element = driver.find_element(By.XPATH, XPATH)
    actions = ActionChains(driver)
    actions.move_to_element(element).perform()
    element.click()


def send_keys(XPATH, value):
    driver.find_element(By.XPATH, XPATH).send_keys(value)


# scroll_down
def scroll_down():
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


def wait_js():
    try:
        waiter = WebDriverWait(driver, 15)
        waiter.until(lambda web_driver: web_driver.execute_script('return document.readyState') == 'complete')
        waiter.until(lambda web_driver: web_driver.execute_script('return jQuery.active') == 0)
    except:
        pass


def refresh_page():
    wait_js()
    try:
        driver.refresh()
    except:
        alert = driver.switch_to_alert()
        alert.accept()


def close_connections():
    driver.quit()
