
import os
import time
from random import choice
from faker import Faker
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from api_functions import AmoSession
from framework import random_data
from locators.locators_essence_page import LocatorsFeed
import configparser


config = configparser.ConfigParser()  # create parser object
dirname = os.path.abspath(__file__)
f = dirname.replace('/pages/base_app.py', '/settings.ini')
config.read(f)

username = config["Access"]["login"]
password = config["Access"]["password"]
subdomain = config["Access"]["subdomain"]


class MyException(Exception):

    def __init__(self, text):
        self.text_error = text


class BasePage:
    LOCATOR_MENU_SECTION = None

    def __init__(self, driver, logger):
        self.driver = driver
        # self.subdomain = subdomain
        self.base_url = "https://{0}.amocrm.ru/srv.php"
        self.logger = logger
        self.fake = Faker('ru_RU')

    def find_element_for_click(self, locator, time=10):
        try:
            element = WebDriverWait(self.driver, time).until(EC.element_to_be_clickable(locator),
                                                             message=f"Can't click element by locator {locator}")
            return element
        except TimeoutException:
            self.logger.error(f'Не могу кликнуть на {locator}, не доступен для клика')
            raise MyException(f'Заблокирован элемент для клика')

    def find_element(self, locator, time=10):
        self.wait_js()
        try:
            element = WebDriverWait(self.driver, time).until(EC.visibility_of_element_located(locator),
                                                             message=f"Can't find element by locator {locator}")
            return element
        except TimeoutException:
            self.logger.error(f'Элемент {locator} не был найден на странице')

    def find_element_on_DOM_page(self, locator, time=10):
        self.wait_js()
        try:
            element = WebDriverWait(self.driver, time).until(EC.presence_of_element_located(locator),
                                                             message=f"Can't find element by locator {locator}")
            return element
        except NoSuchElementException:
            self.logger.error(f'Элемент {locator} не был найден на странице')

    def find_visible_elements(self, locator, time=5):
        self.wait_js()
        try:
            return WebDriverWait(self.driver, time).until(EC.visibility_of_all_elements_located(locator),
                                                          message=f"Can't find elements by locator {locator}")
        except TimeoutException:
            self.logger.error(f'Элементы с локаторами {locator} не был найден на странице')
            return

    def find_located_elements(self, locator, time=10):
        self.wait_js()
        try:
            return WebDriverWait(self.driver, time).until(EC.presence_of_all_elements_located(locator),
                                                          message=f"Can't find elements by locator {locator}")
        except NoSuchElementException:
            self.logger.error(f'Элемент {locator} не был найден на странице')

    def refresh_page(self):
        self.wait_js()
        try:
            self.driver.refresh()
        except:
            alert = self.driver.switch_to_alert()
            alert.accept()

    def move_to_element_and_click(self, element=None, locator=None):
        try:
            if locator:
                element = self.find_element_for_click(locator)
            self.wait_js()
            act = ActionChains(self.driver)
            time.sleep(1)
            act.move_to_element(element).click(element).perform()
        except StaleElementReferenceException:
            self.get_screenshot(self.move_to_element_and_click.__name__)

    def move_to_element_and_clear(self, element=None, locator=None):
        try:
            if locator:
                element = self.find_element(locator)
            self.wait_js()
            act = ActionChains(self.driver)
            act.move_to_element(element).clear().perform()
            self.wait_js()
        except StaleElementReferenceException:
            self.get_screenshot(self.move_to_element_and_clear.__name__)

    def send_keys_to_element(self, message, element=None, locator=None, clear=False):
        # GO TO EL AND SEND_KEYS
        if locator:
            element = self.find_element(locator)
        act = ActionChains(self.driver)
        # if clear:
        #     element.clear().send_keys(message)
        act.move_to_element(element).send_keys(message).perform()
        self.wait_js()

    def send_keys_to_element_with_keys(self, message, element=None, locator=None):
        if locator:
            element = self.find_element(locator)
        self.wait_js()
        act = ActionChains(self.driver)
        act.move_to_element(element).send_keys(message, Keys.ENTER).perform()
        self.wait_js()

    def mouse_to_element(self, locator=None, elem=None):
        # not_found_error_catch = driver.find_element_by_xpath(xpath)
        if locator:
            elem = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator))
        act = ActionChains(self.driver)
        act.move_to_element(elem).perform()
        self.wait_js()

    def mouse_with_offset(self, xoffset=0, yoffset=0):
        act = ActionChains(self.driver)
        act.move_by_offset(xoffset=xoffset, yoffset=yoffset).perform()
        self.wait_js()

    def move_to_element_and_click_with_offset(self, element=None, locator=None, xoffset=0, yoffset=0):
        try:
            if locator:
                element = self.find_element_for_click(locator)
            self.wait_js()
            act = ActionChains(self.driver)
            act.move_to_element_with_offset(element, xoffset=xoffset, yoffset=yoffset).click().perform()
        except StaleElementReferenceException:
            self.get_screenshot(self.move_to_element_and_click_with_offset.__name__)
            self.wait_js()

    def drag_and_drop_mark_in_menu(self, target=None, element=None, locator_el=None, locator_tr=None):
        if locator_el:
            element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator_el))
        elif locator_tr:
            target = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located(locator_tr))

        act = ActionChains(self.driver)
        act.click_and_hold(element).move_by_offset(xoffset=0, yoffset=-20).move_to_element(target).move_by_offset(
            xoffset=-20, yoffset=0).release(element).perform()
        self.wait_js()

    def move_to_el(self, elem):
        self.actions = ActionChains(self.driver)
        return self.actions.move_to_element(elem)

    def go_to_site(self):
        return self.driver.get(self.base_url)

    def find_element_clickable(self, locator, time=5):
        return WebDriverWait(self.driver, time).until(EC.element_to_be_clickable(locator))

    def login(self):
        # Login with api
        self.driver.get(self.base_url.format(subdomain))
        self.driver.delete_all_cookies()
        session_id = random_data()
        server_type = os.getenv('ServerType')
        amo_session = AmoSession(test_name=session_id,
                                 subdomain=subdomain,
                                 login=username,
                                 api_key=None,
                                 password=password,
                                 srv_type=server_type)
        amo_session.create_session(init_mongo=True, use_password=True)
        auth_cookies = amo_session.load_cookies(session_id)
        # drop_collection_from_mongo(session_id)
        self.driver.delete_all_cookies()
        auth_cookies = auth_cookies.get_dict()
        for name, value in auth_cookies.items():
            self.driver.add_cookie({'name': name, 'value': value})
        self.driver.get('https://{0}.amocrm.ru/?lang=ru'.format(subdomain))
        self.logger.info('Страница загружена успешно')
        return amo_session

    def fast_login(self):
        self.driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Логин"]').send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "auth_submit").click()

    def start_test(self, func_name):
        self.logger.info(f"{func_name}, начнем!")

    def end_test(self):
        self.logger.info('==================Конец теста==================')

    def wait_js(self):
        try:
            waiter = WebDriverWait(self.driver, 15)
            waiter.until(lambda web_driver: web_driver.execute_script('return document.readyState') == 'complete')
            waiter.until(lambda web_driver: web_driver.execute_script('return jQuery.active') == 0)
        except:
            pass

    def try_wait(self, method):
        try:
            waiter = WebDriverWait(self.driver, 10)
            waiter.until(method=method)
        except TimeoutException:
            self.logger.error('что то пошло не так')

    def go_to_url(self, url):
        self.driver.get(url)

    def go_to_section(self):
        time.sleep(2)
        el = self.find_element(self.LOCATOR_MENU_SECTION)
        self.move_to_element_and_click(element=el)
        self.logger.info(f'Прием, нахожусь в секции {el.text}')
        time.sleep(2)

    def get_screenshot(self, func_name):
        self.driver.get_screenshot_as_png()
        self.driver.get_screenshot_as_file(f'screenshots/{func_name}')


class LocatorLeftMenu:
    locator_search_field = (By.ID, 'search-input')
    locator_center_notification = (By.CSS_SELECTOR, '.nav__notifications')
    locator_select_user_in_center_notification = (By.CLASS_NAME, 'notification__item_not-multiaction')
    locator_unread_notifications = (By.CLASS_NAME, 'notification-chat__container-icon')


class LeftMenu(BasePage):

    def click_on_notification_center(self):
        self.move_to_element_and_click(locator=LocatorLeftMenu.locator_center_notification)

    def click_search_field(self):
        self.move_to_element_and_click(locator=LocatorLeftMenu.locator_search_field)

    def suggest_users_in_search(self):
        users = self.find_visible_elements(locator=LocatorLeftMenu.locator_select_user_in_center_notification)
        return users

    def choose_user_for_internal_chat(self):
        self.click_on_notification_center()
        search_field = self.find_element(locator=LocatorLeftMenu.locator_search_field)
        user_name = 'test'
        search_field.click()
        search_field.send_keys(user_name, Keys.RETURN)
        user = self.suggest_users_in_search()[0]
        user.click()
        time.sleep(5)

    def choose_user_for_direct_chat(self):
        self.click_on_notification_center()
        search_field = self.find_element(locator=LocatorLeftMenu.locator_search_field)
        user_name = 'test'
        search_field.clear()
        search_field.send_keys(user_name, Keys.RETURN)
        user = self.suggest_users_in_search()[0]
        user.click()
        time.sleep(5)

    def get_quantity_from_counter(self):
        counter = self.find_element(locator=LocatorsFeed.locator_counter_users)
        print(counter.text)
        return int(counter.text)

    def get_chat(self):
        messages = self.find_visible_elements(locator=LocatorLeftMenu.locator_unread_notifications)
        msg = choice(messages)
        return msg

    def choose_chat(self):
        msg = self.get_chat()
        self.move_to_element_and_click(msg)
