
#!/usr/bin/python3
import random
import time
import datetime
import string
import os
import subprWebDriverWaitocess
from faker import Faker
import requests
import yaml
import json
import codecs
import paramiko
import sys
import conftest
from conftest import logger
from random import randint
from random import choice
from random import getrandbits
from random import sample
from pymongo import MongoClient
from selenium import webdriver
from selenium import common
from selenium.common.exceptions import NoSuchElementException, TimeoutException, UnexpectedAlertPresentException
from api_functions import AmoSession
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions as EC
import configparser


config = configparser.ConfigParser()  # создаём объекта парсера
dirname = os.path.abspath(__file__)
f = dirname.replace('framework.py', 'settings.ini')
config.read(f)

login = config['Access']['login']
password = config['Access']['password']
subdomain = config['Access']['subdomain']


ServerType = os.getenv('ServerType')

SUBDOMAINS_JSON = 'subdomains.json'
CONTROLLERS_XPATHS = {
    'save_btn': "//button[contains(@class,'button-input_add js-button-with-loader card-top-save-button "
                "card-top-name__right__save button-input_blue')]",
    'card_settings_in': "//div[contains(@class,'card-fields__fields-block')]//span[contains(text(), 'Настроить')]",
    'card_settings_out': "//div[@class='card-cf__close js-card-cf-close']//*[local-name()='svg']",
    'create_btn': "//a[contains(@class,'button-input_blue js-navigate-link')]"
}
fake = Faker('ru_RU')


class SMSWidgetError(Exception):
    pass


class WidgetInstallError(Exception):
    pass


class MyException(Exception):
    pass


class KnownFuckingBug(Exception):
    pass


def wait_js():
    try:
        waiter = WebDriverWait(driver, 15)
        waiter.until(lambda web_driver: web_driver.execute_script('return document.readyState') == 'complete')
        waiter.until(lambda web_driver: web_driver.execute_script('return jQuery.active') == 0)
    except:
        pass


def wait_element_and_click(xpath=None, webelement=None, controller=None):
    """ Wait element 10 seconds and click on it
    - In the case of using xpath:
    Xpath is first positional argument so there is no need to specify argument
    example:
        wait_element_and_click('//*div..')

    - In the case of using webelement:
    Because webelement is the second  positional argument you must specify
    it for correct use.
    example:
        elements = driver.find_elements_by_name('Some_name')
        element = choice(elements)
        wait_element_and_click(webelement=element) """
    wait_js()
    if xpath or controller:

        try:
            WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, xpath or CONTROLLERS_XPATHS[controller])))
        except exceptions.TimeoutException:
            logger.exception("Элемент не был найден на странице")
        except exceptions.UnexpectedAlertPresentException:
            logger.exception('Несогласованная логика')
            close_connections()
        finally:
            element = driver.find_element_by_xpath(xpath or CONTROLLERS_XPATHS[controller])
            ActionChains(driver).move_to_element(element).click().perform()
            time.sleep(0.5)
    elif webelement:
        ActionChains(driver).move_to_element(webelement).click().perform()
        time.sleep(0.5)
    else:
        raise MyException("Argument not found")
    wait_js()


def wait_element_and_clear(xpath, use_send_keys=False):
    """ Wait element 10 second and clear it. Useful for clearing forms """
    wait_js()
    try:
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath)))
    finally:
        if not use_send_keys:
            driver.find_element(By.XPATH, xpath).clear()
        else:
            driver.find_element(By.XPATH, xpath).send_keys(Keys.CONTROL + Keys.BACKSPACE)
    wait_js()


def wait_element_and_send_text(message, xpath, with_assert=True, use_send_keys=False):
    """ Wait element and send text """
    wait_js()
    try:
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath)))
    finally:
        wait_element_and_clear(xpath, use_send_keys=use_send_keys)
        driver.find_element_by_xpath(xpath).send_keys(message)
    if with_assert:
        assert WebDriverWait(driver, 10).until(
            expected_conditions.text_to_be_present_in_element_value(
                (By.XPATH, xpath), str(message)))
    wait_js()


def wait_element_and_send_text_elem(xpath, message):
    """ Wait element and send text """
    wait_js()
    try:
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath)))
    finally:
        wait_element_and_clear(xpath)
        driver.find_element_by_xpath(xpath).send_keys(message)
    assert WebDriverWait(driver, 10).until(
        expected_conditions.text_to_be_present_in_element((By.XPATH, xpath),
                                                          str(message)))
    wait_js()


# todo здесь изменяла функцию
def wait_element_and_send(xpath, message, keys_return=False):
    """ Wait element and send text """
    wait_js()
    try:
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, xpath)))
    finally:
        if keys_return:
            driver.find_element_by_xpath(xpath).send_keys(message + Keys.ENTER)
        else:
            driver.find_element_by_xpath(xpath).send_keys(message)
    wait_js()


def new_session(url="https://amocrm.ru"):
    """ Init new webdriver session """
    global driver
    driver = choose_driver()
    driver.set_window_size(1920, 1080)

#
# def set_logging(test_name):
#     # Create a custom logger
#     global logger
#     logger = logging.getLogger()
#     # Create handlers
#     f_handler = logging.FileHandler(f'logs/{test_name}.log')
#     f_handler.setLevel(logging.ERROR)
#     # Create formatters and add it to handlers
#     f_format = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
#     f_handler.setFormatter(f_format)
#     # Add handlers to the logger
#     logger.addHandler(f_handler)


def choose_driver():
    chrome_options = webdriver.ChromeOptions()
    caps = DesiredCapabilities.CHROME
    caps['loggingPrefs'] = {'performance': 'ALL'}
    prefs = {'profile.default_content_setting_values': {'notifications': 2}}
    chrome_options.add_experimental_option("prefs", prefs)
    if '--localdriver' in sys.argv:
        return webdriver.Chrome(
            '/usr/local/selenium_drivers/chromedriver',
            chrome_options=chrome_options,
            desired_capabilities=caps
        )
    else:
        return webdriver.Remote(
            command_executor='http://10.13.248.72:4444/wd/hub',
            desired_capabilities=caps,
        )


def change_lang(lang):
    url = driver.current_url
    l = '&' if '?' in url else '?'
    url += '{l}lang={lang}'.format(l=l, lang=lang)
    driver.get(url)


def login_func(stand, account=False, sign_in=True,
               test_name=None):
    """ Login function. Choice login pair
    Parameter:
    :stand - str, stage
    :account - account key from setting.yml
    :test_name - collection key as a key in MongoDB
    :new_password - bool, if True type new password for account
                             False use standart password
    :sign_in - bool, if True then sign in account
                        False then stay at promo page
    """
    # Go to main page
    if ServerType == 'PROD_USA':
        url = "https://www.amocrm.com/srv.php"
        domain = 'com'
    else:
        url = "https://www.amocrm.ru/srv.php"
        domain = 'ru'
    # driver.get(url)
    # Get login/password data from settings.yml
    # with open('settings.yml') as auth_pair:
    #     pair = yaml.safe_load(auth_pair)
    # if account:
    #     login = pair['auth'][ServerType][stand][account]
    # elif test_name:
    #     data = find_data_in_mongo(test_name)
    #     login = data['name'] + '@example.com'
    # else:
    #     login = pair['auth'][ServerType][stand]['login']


    # Login with api
    driver.get('https://{0}.amocrm.{1}/srv.php'.format(subdomain, domain))
    driver.delete_all_cookies()
    session_id = random_data()
    amo_session = AmoSession(test_name=session_id,
                             subdomain=subdomain,
                             login=login,
                             api_key=None,
                             password=password,
                             srv_type=ServerType)
    amo_session.create_session(init_mongo=True, use_password=True)
    auth_cookies = amo_session.load_cookies(session_id)
    drop_collection_from_mongo(session_id)
    driver.delete_all_cookies()
    auth_cookies = auth_cookies.get_dict()
    for name, value in auth_cookies.items():
        driver.add_cookie({'name': name, 'value': value})
    driver.get('https://{0}.amocrm.{1}/?lang=ru'.format(subdomain, domain))
    return amo_session


def get_subdomain_from_promo(login, password):
    """
    This function get subdomian of account from promo page
    :param login: login name of user's account
    :type login: str
    :param password: password from user account
    :type password: str
    :return str
    """
    subdomain = get_subdomains_from_file(SUBDOMAINS_JSON, login)
    if subdomain:
        return subdomain
    else:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                                 'Chrome/39.0.2171.95 Safari/537.36'
                   }
        csrf_token = requests.get('https://www.amocrm.ru', headers=headers, )
        payload = {'username': login, 'password': password, 'csrf_token': csrf_token.cookies['csrf_token']}
        auth_cookies = requests.post('https://www.amocrm.ru/oauth2/authorize', payload).cookies
        try:
            r = requests.get('https://www.amocrm.ru/v3/accounts', cookies=auth_cookies).json()
            subdomain = r['_embedded']['items'][0]['subdomain']
        except AttributeError:
            return None
        save_subdomain_in_file(subdomain, SUBDOMAINS_JSON, login)
        return subdomain


def get_subdomains_from_file(file, login):
    """
    This function get saved subdomain from file to boost login speed
    :param file: file name where to save data
    :type file: str
    :param login: login name of account
    :type login: str
    """
    with open(file) as subdomain_file:
        data = json.load(subdomain_file)
    if login in data[ServerType]:
        return data[ServerType][login]['subdomain']
    else:
        return None


def save_subdomain_in_file(subdomain, file, login):
    """
    This function save subdomain in file to boost login speed
    :param subdomain: subdomain name
    :type subdomain: str
    :param file: file name where to save data
    :type file: str
    :param login: login name of account
    :type login: str
    """
    with codecs.open(file, 'r', 'utf-8-sig') as subdomain_file:
        keys = json.load(subdomain_file)
    keys[ServerType][login] = {'subdomain': subdomain}
    with open(file, 'w') as subdomain_file:
        json.dump(keys, subdomain_file, indent=3)


def manual_login_func(stand, account=False, new_password=False, sign_in=True,
                      test_name=None):
    """ Login function. Choice login pair
    Parameter:
    :stand - str, stage
    :account - account key from setting.yml
    :test_name - collection key as a key in MongoDB
    :new_password - bool, if True type new password for account
                             False use standart password
    :sign_in - bool, if True then sign in account
                        False then stay at promo page
    """
    # Go to main page
    if ServerType == 'PROD_USA':
        driver.get("https://www.amocrm.com")
    else:
        driver.get("https://amocrm.ru")
    # Get login/password data from settings.yml
    with open('settings.yml') as auth_pair:
        pair = yaml.load(auth_pair)
    if account:
        login = pair['auth'][ServerType][stand][account]
    elif test_name:
        data = find_data_in_mongo(test_name)
        login = data['name'] + '@example.com'
    else:
        login = pair['auth'][ServerType][stand]['login']
    password = pair['auth'][ServerType][stand]['password']
    if new_password:
        password = password[::-1]
    # Login
    wait_element_and_click('//*[@id="page_header__auth_button"]/div')
    wait_element_and_send_text('//*[contains(@id, "auth-email")]', login)
    wait_element_and_send_text('//*[contains(@id, "auth-password")]', password)
    wait_element_and_send('//*[@id="form_auth__button_submit"]', Keys.RETURN)
    if sign_in:
        if ServerType == 'PROD_USA':
            driver.get('https://www.amocrm.com')
        else:
            driver.get('https://amocrm.ru')
        wait_element_and_click('//*[contains(@class, "js-user-select-current '
                               'user-select__user-current")]')
        wait_element_and_click('//*[contains(@class, "user-select__link")]')
    else:
        time.sleep(0.5)


def to_lead():
    wait_element_and_click('//*[@id="nav_menu"]/div[1]/a/div[1]')
    wait_element_and_click(
        '//*[contains(@class,"dashboard-tile__item")]'
        '//*[contains(@class,"dashboard-tile__item-top")]'
        '//*[contains(@href,"/leads/list/?")]')
    wait_element_and_click(
        '//*[contains(@href,"/leads/add/")]')


def fill_lead(test_name=None, only_name=False):
    """ Fill field in lead.
    Parameters:
    :test_name - name of test used as a key in MongoDB collection;
    :only_name - in some tests there is no need to fill all fields in card so
                if only_name = True then fucntion create empty lead with name.
    """
    lead_name = random_data()
    wait_element_and_click('//*[contains(@placeholder, "Lead #XXXXXX")]')
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Lead #XXXXXX")]', lead_name)
    if not only_name:
        wait_element_and_send_text(
            '//*[@id="lead_card_budget"]', randint(100, 999))
        # Tags
        wait_element_and_click(
            '//*[contains(@class, " multisuggest__list-item js-multisuggest-item")]')
        tag1 = random_data()
        wait_element_and_send_text(
            '//*[contains(@class, "multisuggest__input '
            'js-multisuggest-input")]',
            tag1)
        wait_element_and_send(
            '//*[contains(@class, "multisuggest__input '
            'js-multisuggest-input")]',
            Keys.ENTER)
        wait_element_and_send_text(
            '//*[contains(@class, "multisuggest__input '
            'js-multisuggest-input")]',
            random_data())
        wait_element_and_send(
            '//*[contains(@class, "multisuggest__input '
            'js-multisuggest-input")]',
            Keys.ENTER)
    # Save
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span/span')
    time.sleep(5)  # Don't touch this
    if test_name:
        save_data_to_mongo(test_name, {'xpath': './/*[@id="person_n"]',
                                       'value': lead_name})
        if not only_name:
            save_data_to_mongo(test_name, {'xpath': '//*[@id="0"]/ul/li/input',
                                           'value': tag1})


def create_note(test_name=None, init_mongo=True):
    """ Create note in card and check data changes """
    data = random_data()
    time.sleep(0.5)
    mouse_to_element(
        '//*[contains(@class, "feed-compose__message-wrapper")]' +
        '//*[@class ="feed-compose-switcher"]')
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@data-id, "note")]')
    time.sleep(1)
    wait_element_and_send_text_elem(
        '//*[contains(@class, ' +
        '"control-contenteditable__area feed-compose__message")]',
        data)
    wait_element_and_click(
        '//*[contains(@class, "card-holder__feed")]' +
        '//*[contains(@class, "button-input") and contains(text(), "Add")]')
    time.sleep(0.5)
    if test_name:
        if init_mongo:
            save_data_to_mongo(test_name, {'note': data})
        else:
            update_data_in_mongo(test_name, {'note': data})


def check_note_data(test_name):
    """ Check data changes in note """
    data = find_data_in_mongo(test_name)
    # Edit data in note
    new_data = random_data()
    wait_element_and_click('//*[text() = "{}"]'.format(data['note']))
    wait_element_and_send_text('//*[text() = "{}"]'.format(data['note']),
                               new_data)
    # Click edit
    wait_element_and_click(
        '//*[contains(@class, "button") and contains(text(), "Edit")]')
    refresh_page()
    # Check changes
    note = driver.find_element_by_xpath(
        '//*[contains(@class, "feed-note__body")]' +
        '//*[text()="{}"]'.format(new_data))
    assert new_data == note.text


def create_another_contact():
    wait_element_and_click('//*[@id="new_contact_n"]')
    wait_element_and_send_text('//*[@id="new_contact_n"]', random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[1]' +
        '/div[1]/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[2]' +
        '/div[1]/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[3]/div[2]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[4]/div[1]/div[2]/input',
        random_data())
    time.sleep(1)
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(0.5)


def change_resp_person():
    time.sleep(2)
    users = ['Mister Amo', 'Senior Amo', 'Frau Amo', 'PanAmo', 'Am Am Crm']
    drop_down = choice(users)
    wait_element_and_click(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li')
    wait_element_and_send_text(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        drop_down)
    wait_element_and_send(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        Keys.ENTER)
    time.sleep(1)
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span/span')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept ")]')


def scroll_feed():
    # Scroll page down. First click on note element to be able to send PAGE DOWN key
    wait_element_and_click(
        '//*[contains(@class, "feed-note  feed-note-with-context")]')
    wait_element_and_send(
        '//*[contains(@class, "feed-note__textarea custom-scroll' +
        ' textarea-autosize")]',
        Keys.PAGE_DOWN)


def check_filter():
    # Checking filter
    # Click on the eye -> Open filter
    refresh_page()
    time.sleep(2)
    wait_element_and_click(
        '//*[contains(@class, "feed-notes-filter__eye")]')
    wait_element_and_click(
        '//*[contains(@class, "js-notes-filter-all-linked' +
        ' js-form-changes-skip")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept ' +
        'js-button-with-loader modal-body__actions__save ' +
        'js-notes-filter-apply button-input_blue")]')
    # Close filter
    wait_element_and_click(
        '//*[contains(@class, "card-fields__top-name-wrapper")]')
    # Open filter -> Remove "All events", after return it back
    for i in range(2):
        wait_element_and_click(
            '//*[contains(@class, "feed-notes-filter__eye js-notes-filter")]')
        wait_element_and_click(
            '//*[@title = "All events"]')
        wait_element_and_click(
            '//*[contains(@class, "feed-notes-filter")]' +
            '//*[contains(@class, "button-input") ' +
            'and contains(text(), "Apply")]')
        time.sleep(0.5)


def refresh_page(pause=2):
    """ Refresh page after pause
    Parameters:
    :pause - int, number of seconds to pause
    """
    time.sleep(pause)
    driver.refresh()
    time.sleep(3)


def to_dashboard():
    wait_element_and_click('//*[@id="nav_menu"]/div[1]/a/div[1]')


def check_recent_activity():
    time.sleep(2)
    wait_element_and_click('//*[@id="dashboard_holder"]/div/div[1]')
    wait_element_and_click(
        '//*[contains(@class,"button-input    dashboard-search__events js-dashboard-search-events")]')


def to_contact():
    wait_element_and_click('//*[@id="nav_menu"]/div[1]/a/div[1]')
    wait_element_and_click(
        '//*[contains(@class,"dashboard-tile__item")]'
        '//*[contains(@class,"dashboard-tile__item-top")]'
        '//*[contains(@href,"/contacts/list/contacts/")]')
    wait_element_and_click(
        '//*[contains(@href,"/contacts/add/")]')


def fill_contact(test_name=None, only_name=False):
    """ Fill field in contact.
    Parameters:
    :test_name - name of test used as a key in MongoDB collection;
    :only_name - in some tests there is no need to fill all fields in card so
                if only_name = True then function create empty lead with name.
    """
    contact_name = random_data()
    wait_element_and_send_text('.//*[@id="person_n"]', contact_name)
    if not only_name:
        # Tags
        wait_element_and_click('//*[contains(@id, "add_tags")]')
        tag1 = random_data()
        tag2 = random_data()
        wait_element_and_send_text('//*[@id="0"]/ul/li/input', tag1)
        wait_element_and_send('//*[@id="0"]/ul/li/input', Keys.ENTER)
        wait_element_and_send_text('//*[@id="0"]/ul/li/input', tag2)
        wait_element_and_send('//*[@id="0"]/ul/li/input', Keys.ENTER)
        wait_element_and_click(
            '//*[contains(@class,"card-fields__linked-block js-linked_elements_wrapper")]')
        # work phone
        work_phone = random_data()
        # work email
        work_email = random_data() + '@example.com'
        wait_element_and_send_text(
            '//*[contains(@id,"edit_card")]' +
            '//*[contains(@class,"control-phone__formatted js-form-changes-skip")]',
            work_phone)
        wait_element_and_send_text(
            '//*[@id="edit_card"]/div/div[4]/div[2]/' +
            'div[1]/div[2]/div/div[1]/input',
            work_email)
        wait_element_and_send_text(
            '//*[@id="edit_card"]/div/div[4]/div[3]/div[2]/input',
            random_data())
    # Save
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span')
    time.sleep(1)
    if test_name:
        save_data_to_mongo(test_name, {'xpath': './/*[@id="person_n"]',
                                       'value': contact_name})
        if not only_name:
            save_data_to_mongo(test_name, {'xpath': '//*[@id="0"]' +
                                                    '/ul/li/input',
                                           'value': tag1})
            save_data_to_mongo(test_name, {'xpath': 'work_phone',
                                           'value': work_phone})
            save_data_to_mongo(test_name, {'xpath': 'work_email',
                                           'value': work_email})


def fill_contact_company(test_name=None):
    """ Fill company fields in card """
    wait_element_and_click('//*[@id="card_tabs"]/div[3]/span')
    wait_element_and_click('//*[@id="new_company_n"]')
    company_name = random_data()
    wait_element_and_send_text('//*[@id="new_company_n"]', company_name)
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div/div[1]' +
        '/div[1]/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div/div[2]' +
        '/div[1]/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div/div[3]/div[2]/div/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div/div[4]/div[2]/div/textarea',
        random_data())
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span/span')
    time.sleep(0.5)
    if test_name:
        save_data_to_mongo(test_name,
                           {
                               'company_name_xpath': '//*['
                                                     '@id="new_company_n"]',
                               'value': company_name})


def create_clock_task(rand_time=True, rand_user=True):
    wait_element_and_send_text_elem(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        random_data())
    mouse_to_element(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div['
        '1]/div')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "tips-item js-tips-item js-switcher-task")]')
    if rand_time:
        # Choice random time
        periods_list = ["This week",
                        "In 7 days",
                        "In 30 days",
                        "In 1 year",
                        ]
        wait_element_and_click(
            '//*[contains(@class, "tasks-date__caption")]')
        wait_element_and_click(
            '//*[contains(@class, "tasks-date__list__item js-tasks-date-preset") and contains(text(), "{}")]'.format(
                choice(periods_list)))
    else:
        wait_element_and_click('//*[contains(@class, "tasks-date__caption")]')
        wait_element_and_click(
            '//*[contains(@class, "tasks-date__list__item js-tasks-date-preset") and contains(text(), "Today")]')
    # Random user
    if rand_user:
        users = ['Mister Amo', 'Senior Amo', 'Frau Amo', 'PanAmo', 'Amo CRM']
        wait_element_and_click('//*[@id="feed_compose_user"]')
        wait_element_and_click('//*[@id="feed_compose_user"]/div')
        wait_element_and_send_text(
            '//*[@id="feed_compose_user"]/div/ul/li[2]/input', choice(users))
        wait_element_and_send(
            '//*[@id="feed_compose_user"]/div/ul/li[2]/input',
            Keys.ENTER)
    wait_element_and_click(
        '//*[contains(@class, "feed-compose__inner")]' +
        '//*[contains(text(), "Set")]')
    # time.sleep(1)


def fill_contact_leads():
    time.sleep(1)
    wait_element_and_click('//*[@id="card_tabs"]/div[4]/span')
    time.sleep(1)
    wait_element_and_click(
        '//*[@id="card_fields"]/div[2]/div[2]/' +
        'div[2]/div/div/div[3]/div/div[1]/div')
    wait_element_and_send_text('//*[@id="quick_add_lead_name"]', random_data())
    wait_element_and_send_text('//*[@id="quick_add_lead_budget"]', "731")


def fill_contact_leads_contact():
    wait_element_and_click('//*[contains(@title, "Leads")]')
    wait_element_and_click(
        '//*[@id="card_fields"]/div[2]/div[2]/div[2]' +
        '/div/div/div[3]/div/div[1]/div')
    wait_element_and_send_text(
        '//*[@id="quick_add_lead_name"]',
        random_data())
    wait_element_and_send_text(
        '//*[@id="quick_add_lead_budget"]',
        randint(100, 999))
    wait_element_and_click('//*[@id="quick_add_form_btn"]/span')


def change_contact_pipeline():
    # Change pipeline in list --> leads --> quick add
    pipeline_status = ['Initial Contact_1',
                       'Offer made_1',
                       'Negotiation_1',
                       'Closed - won_1',
                       ]
    # click on pipeline select
    wait_element_and_click('//*[@class="pipeline-select pipeline-select__button-create-new-field"]')
    # click on the New pipeline
    wait_element_and_click(
        '//*[contains(@class, "custom-scroll active")]' +
        '//*[@title = "New pipeline"]')
    # random chioce
    wait_element_and_click(
        '//*[contains(@class, "pipeline-select__item-text") ' +
        'and text() = "{}"]'.format(choice(pipeline_status)))
    time.sleep(3)
    wait_element_and_click('//*[@id="quick_add_form_btn"]/span')
    time.sleep(3)


def change_company_resp_person():
    time.sleep(2)
    users = ['Mister Amo', 'Senior Amo', 'Frau Amo', 'PanAmo', 'Am Am Crm']
    drop_down = choice(users)
    wait_element_and_click(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li')
    wait_element_and_send_text(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        drop_down)
    wait_element_and_send(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        Keys.ENTER)
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span/span')
    time.sleep(2)


def change_contact_resp_person():
    time.sleep(2)
    users = ['Mister Amo', 'Senior Amo', 'Frau Amo', 'PanAmo', 'Am Am Crm']
    drop_down = choice(users)
    wait_element_and_click(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li')
    wait_element_and_send_text(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        drop_down)
    wait_element_and_send(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        Keys.ENTER)
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span/span')
    time.sleep(2)


def click_to_lead():
    """ Click on lead tab in card and then click on a first lead"""
    wait_element_and_click(
        '//*[contains(@class, "card-fields")]//*[contains(@title, "Leads")]')
    wait_element_and_click(
        '//*[contains(@class, "card-fields")]' +
        '//*[contains(@href, "/leads/detail/")]')


def back_button():
    time.sleep(2.5)
    wait_element_and_click('//*[contains(@class, "card-fields__top-back")]')
    time.sleep(1)


def to_company():
    wait_element_and_click('//*[@id="nav_menu"]/div[1]/a/div[1]')
    wait_element_and_click(
        '//*[contains(@class,"dashboard-tile__item")]'
        '//*[contains(@class,"dashboard-tile__item-top")]'
        '//*[contains(@href,"/contacts/list/companies/")]')
    wait_element_and_click(
        '//*[contains(@href,"/companies/add/")]')


def fill_company(test_name=None, only_name=False):
    """ Fill field in company.
    Parameters:
    :test_name - name of test used as a key in MongoDB collection;
    :only_name - in some tests there is no need to fill all fields in card so
                if only_name = True then fucntion create empty lead with name.
    """
    company_name = random_data()
    wait_element_and_send_text('//*[contains(@placeholder, "Company name")]',
                               company_name)
    if not only_name:
        wait_element_and_send_text(
            '//*[@id="edit_card"]/div/div[4]/div[1]' +
            '/div[1]/div[2]/div/div[1]/input',
            random_data())
        wait_element_and_send_text(
            '//*[@id="edit_card"]/div/div[4]/div[2]' +
            '/div[1]/div[2]/div/div[1]/input',
            random_data())
        wait_element_and_send_text(
            '//*[@id="edit_card"]/div/div[4]/div[3]/div[2]/div/input',
            random_data())
        wait_element_and_send_text(
            '//*[@id="edit_card"]/div/div[4]/div[4]/div[2]/div/textarea',
            random_data())
        wait_element_and_click('//*[contains(@id, "add_tags")]')
        tag1 = random_data()
        wait_element_and_send_text(
            '//*[contains(@class, "multisuggest__input js-multisuggest-input") and @data-can-add="Y"]', tag1)
        wait_element_and_send(
            '//*[contains(@class, "multisuggest__input js-multisuggest-input") and @data-can-add="Y"]', Keys.ENTER)
        wait_element_and_send_text(
            '//*[contains(@class, "multisuggest__input js-multisuggest-input") and @data-can-add="Y"]', random_data())
        wait_element_and_send(
            '//*[contains(@class, "multisuggest__input js-multisuggest-input") and @data-can-add="Y"]', Keys.ENTER)
    # Save
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span')
    time.sleep(5)
    if test_name:
        save_data_to_mongo(test_name,
                           {'xpath': '//*[contains(@placeholder, '
                                     '"Company name")]',
                            'value': company_name})
        if not only_name:
            save_data_to_mongo(test_name,
                               {'xpath': '//*[@id="0"]/ul/li/input',
                                'value': tag1})


def to_todo():
    wait_element_and_click('//*[@id="nav_menu"]/div[1]/a/div[1]')
    wait_element_and_click(
        '//*[contains(@class,"dashboard-tile__item")]'
        '//*[contains(@class,"dashboard-tile__item-top")]'
        '//*[@href="/todo/list/?"]')
    wait_element_and_click(
        '//*[contains(text(),"New task")]')


def change_timing_todo(with_time=False):
    time_list = ['//*[contains(@data-period, "before_end_of_week")]',
                 '//*[contains(@data-period, "next_week")]',
                 '//*[contains(@data-period, "next_month")]',
                 '//*[contains(@data-period, "next_year")]',
                 ]
    wait_element_and_click(
        '//*[contains(@class, "todo-form")]' +
        '//*[contains(@class, "tasks-date__caption ")]')
    if with_time:
        driver.find_element_by_xpath('//*[contains(@class, "js-tasks-date-time-input")]').clear()
        rand_time = str(randint(0, 23)) + ':' + str(randint(0, 60))
        # Set time
        wait_element_and_send(
            '//*[contains(@class, "js-tasks-date-time-input")]',
            rand_time)
    wait_element_and_click(choice(time_list))


def comment_todo():
    """ Write to-do comment in create to-do form """
    # Write message
    wait_element_and_send(
        '//*[contains(@class, "js-control-contenteditable ' +
        'control-contenteditable card-task__actions")]/div[2]',
        random_data())
    # Choose task type
    wait_element_and_click(
        '//*[contains(@class, "card-task__type-wrapper")]')
    # Select meeting
    wait_element_and_click(
        '//*[contains(@class, "card-task__type-opened")]' +
        '//*[contains(text(), "Meeting")]')
    time.sleep(0.5)


def save_todo():
    """ Click on Set in to-do form """
    wait_element_and_click(
        '//*[contains(@class, "todo-form")]//*[contains(text(), "Set")]')
    time.sleep(5)


def change_resp_of_todo():
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@class, "card-task__actions__date-user__user")]')
    wait_element_and_click(
        '//*[contains(@class, "card-task__actions__date-user__user")]')
    time.sleep(1)
    rand_resp = choice(driver.find_elements_by_xpath(
        '//*[contains(@class, "users-select__body__item")]')[0:6])
    time.sleep(1)
    wait_element_and_click(webelement=rand_resp)


def to_calendar():
    wait_element_and_click('//*[contains(@href, "/todo/")]')


def mouse_to_element(xpath=None, elem=None):
    # not_found_error_catch = driver.find_element_by_xpath(xpath)
    try:
        if xpath:
            elem = WebDriverWait(driver, 10).until(expected_conditions.visibility_of_element_located((By.XPATH, xpath)))
        webdriver.ActionChains(driver).move_to_element(elem).perform()
    except exceptions:
        logger.exception('Заданный элемент не найден')


def mouse_to_element_with_offset(xpath, xoffset, yoffset):
    """
    This function move mouse to element with offset
    :param xpath: xpath of the element
    :type xpath: str
    :param xoffset: x offset coordinate
    :type xoffset: int
    :param yoffset: y offset coordinate
    :type yoffset: int
    """
    not_found_error_catch = driver.find_element_by_xpath(xpath)
    elem = WebDriverWait(driver, 10).until(
        expected_conditions.visibility_of_element_located(
            (By.XPATH, xpath)))
    ActionChains(driver).move_to_element_with_offset(elem, xoffset, yoffset).perform()


def mouse_to_lead():
    try:
        wait_element_and_click('//*[contains(@class, "nav__menu__item__title") '
                               'and (contains(text(), "Leads") or '
                               'contains(text(), "Сделки"))]')
        mouse_to_element('//*[contains(@class, "n-avatar")]')
        time.sleep(3)
        wait_element_and_click('//*[contains(@class, "funnel list-top-nav__text-button_submenu")]')
        time.sleep(0.5)
    except exceptions.NoSuchElementException as exp:
        assert 'Message: no such element: Unable to locate element:' in str(exp)
        logger.exception('Не нашел раздел "Сделки". Xpath не действителен')


def close_connections():
    driver.quit()


def click_to_add_todo_button():
    # Calendar --> add to-do button
    time.sleep(0.5)
    wait_element_and_click('//*[@id="todo_add_btn"]')


def fill_calendar_todo(change_resp=True):
    # Calendar --> to_do
    # Check all fields in calendar to_do
    # Click on "Today"
    # Перебираем все даты, завтра, следующая неделя, следующий месяц и год.
    # click on to-do tab
    wait_element_and_click(
        '//*[contains(@class, "todo-form")]//*[contains(@class, "card-task__date")]')
    time_list = ['//*[contains(@data-period, "before_end_of_week")]',
                 '//*[contains(@data-period, "next_week")]',
                 '//*[contains(@data-period, "next_month")]',
                 '//*[contains(@data-period, "next_year")]',
                 ]
    for date in time_list:
        time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "todo-form")]'
            '//*[contains(@class, "tasks-date__caption")]')
        wait_element_and_click(date)
    time.sleep(1)
    # Выбираем случайную дату
    wait_element_and_click(
        '//*[contains(@class, "todo-form")]'
        '//*[contains(@class, "tasks-date__caption")]')
    wait_element_and_click(choice(time_list))
    # Выбираем время
    wait_element_and_click(
        '//*[contains(@class, "todo-form")]'
        '//*[contains(@class, "tasks-date__caption")]')
    driver.find_element_by_xpath('//*[contains(@class, "js-tasks-date-time-input")]').clear()
    hour = randint(0, 12)
    minutes = randint(0, 60)
    sun = ['AM', 'PM']
    r_sun = choice(sun)
    random_time = str(hour) + ':' + str(minutes) + ' ' + r_sun
    # Save
    wait_element_and_click(
        '//*[contains(@class, "js-todo-form-suggest")]')
    # Заполняем остальное и сохраняем
    if change_resp:
        wait_element_and_send_text('//*[@id="todo_form_linked"]',
                                   random_data())
        wait_element_and_send('//*[@id="todo_form_linked"]', Keys.ESCAPE)
        users = ['//*[@id="modal_add_task_form"]/div[3]/ul/li[1]',
                 '//*[@id="modal_add_task_form"]/div[3]/ul/li[2]',
                 '//*[@id="modal_add_task_form"]/div[3]/ul/li[3]',
                 ]
        wait_element_and_click('//*[@id="modal_add_task_form"]/div[3]/button')
        wait_element_and_click(choice(users))
    else:
        pass
    wait_element_and_send_text(
        '//*[contains(@class, "control-contenteditable__area")]',
        random_data(),
        with_assert=False)
    time.sleep(2)
    # Click on edit
    wait_element_and_click(
        '//*[contains(@class, "feed-compose__actions card-task__buttons")]' +
        '//*[contains(text(), "Edit")]')
    time.sleep(4)


def to_list_settings():
    # Calendar --> tree dots in right upper corner --> "List settings"
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu") and contains(@title, "More")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item__text ") and contains(text(), "List settings")]')


def drag_and_drop(source_element, destination_element):
    ActionChains(driver).drag_and_drop(source_element,
                                       destination_element).perform()


def add_additional_columns_in_todo():
    # Leads --> tree dots --> additional columns
    # Add only first column
    try:
        time.sleep(2)
        source = driver.find_element_by_xpath(
            '//*[@id="list_column_settings_holder"]/div[1]')
        destination = driver.find_element_by_xpath(
            '//*[@id="list_head"]/div[2]/div[1]/div[1]')
        drag_and_drop(source, destination)
        time.sleep(0.5)
        source = driver.find_element_by_xpath(
            '//*[@id="list_column_settings_holder"]/div/div/span[2]')
        destination = driver.find_element_by_xpath(
            '//*[@id="list_head"]/div[2]/div[1]/div[1]')
        drag_and_drop(source, destination)
        time.sleep(0.5)
        wait_element_and_click(
            '//*[@id="column_settings__submit"]/span/span')
        time.sleep(2)
    except (common.exceptions.NoSuchElementException,
            common.exceptions.ElementNotVisibleException):
        try:
            del_additional_columns_in_todo()
            to_list_settings()
            add_additional_columns_in_todo()
        except (common.exceptions.NoSuchElementException,
                common.exceptions.ElementNotVisibleException) as exp:
            raise exp


def del_additional_columns_in_todo():
    # Calendar --> tree dots --> additional columns
    # Add only first column
    source = driver.find_element_by_xpath(
        '//*[@id="list_head"]/div[2]/div[1]/div[1]/span[2]')
    destination = driver.find_element_by_xpath('//*[@id="column_settings"]')
    drag_and_drop(source, destination)
    source = driver.find_element_by_xpath(
        '//*[@id="list_head"]/div[2]/div[1]/div[1]/span[2]')
    destination = driver.find_element_by_xpath(
        '//*[@id="list_column_settings_holder"]')
    drag_and_drop(source, destination)
    time.sleep(2)
    wait_element_and_click('//*[@id="column_settings__submit"]')
    time.sleep(3)


def sort_deadline():
    """ Change sorting in Deadline column """
    for sort in ['DESC', 'ASC']:
        # Click on deadline
        wait_element_and_click(
            '//*[contains(@class, "cell-head__title") '
            'and contains(text(), "Deadline")]')
        time.sleep(1)
        # select type of sort
        wait_element_and_click(
            '//*[contains(@class, "list-sort-dialog_visible")]'
            '//*[contains(@data-sort, "{}")]'.format(sort))
        time.sleep(2)


def change_task_status(status):
    el = driver.find_elements_by_xpath(
        '//*[contains(@id, "lead_") and contains(@type, "checkbox")]')
    time.sleep(1)
    el[0].click()
    el[1].click()
    el[2].click()
    time.sleep(1)
    if status == "open":
        time.sleep(1)
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions")]' +
            '//*[contains(@class, "open-tasks")]')
        time.sleep(1)
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]' +
            '//*[contains(text(), "Yes")]')
    elif status == "close":
        time.sleep(1)
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions")]' +
            '//*[contains(@data-type, "close")]')
    elif status == "delete":
        time.sleep(1)
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions")]' +
            '//*[contains(@class, "icon-delete-trash")]')
        time.sleep(1)
        wait_element_and_click(
            '//*[contains(@class, "modal-body__actions ")]'
            '//*[contains(text(), "Confirm")]')
    time.sleep(9)
    wait_element_and_click(
        '//*[contains(text(), "Continue with crm")]')
    time.sleep(1)


def select_complete_todo():
    wait_element_and_click(
        '//*[@id="search_input_wrapper"]/div[2]/div[2]/span')
    wait_element_and_click('//*[@id="filter_list"]/li[3]/a/span')
    time.sleep(2)


def select_manage_todo_types():
    wait_element_and_click('//*[contains(@class, "button-input-more-inner")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item__text ")' +
        ' and text()="Manage task type"]')


def add_own_types():
    try:
        wait_element_and_send_text(
            '//*[contains(@class, "js-custom-type-item")][contains(@class, "text-input")]',
            random_data())
        wait_element_and_click(
            '//*[contains(@class, "modal-body__actions")]' +
            '//*[contains(text(), "Save")]')
    except (common.exceptions.NoSuchElementException,
            common.exceptions.ElementNotVisibleException):
        try:
            del_own_types()
            add_own_types()
        except (common.exceptions.NoSuchElementException,
                common.exceptions.ElementNotVisibleException) as exp:
            raise exp


def del_own_types():
    """ Manage To-do types -> delete all custom types """
    xpath = '//*[contains(@class, ' \
            '"modal-body__inner__todo-types__item ' \
            'js-animate js-item-animate")]' \
            '//*[contains(@class, "remove")]'
    time.sleep(1)
    own_types = driver.find_elements_by_xpath(xpath)
    if len(own_types) > 0:
        for _ in own_types:
            wait_element_and_click(xpath)
            wait_element_and_click(
                '(//*[contains(@class, "button-input") and contains(text(), "Yes")])[last()]')
            time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "button-input-inner__text") ' +
            'and contains(text(), "Save")]')
        time.sleep(2)
        wait_element_and_click('//*[contains(text(), "Tasks changed success")]/..//button')
    else:
        raise Exception(
            "Custom to-do type did'n have time to load")


def click_on_day():
    time.sleep(1)
    wait_element_and_click(
        '//*[@id="list_page_holder"]/div/div/div[1]/div[1]/div[2]/a[1]')


def turn_date_page():
    time.sleep(2)
    wait_element_and_click('//*[@id="todo-calendar"]/div[1]/div[2]/button')


def today_button():
    time.sleep(1)
    wait_element_and_click('//*[@id="todo_calendar_today"]')


def click_on_week():
    time.sleep(1)
    wait_element_and_click(
        '//*[@id="list_page_holder"]/div/div/div[1]/div[1]/div[2]/a[2]')


def click_on_month():
    time.sleep(1)
    wait_element_and_click(
        '//*[@id="list_page_holder"]/div/div/div[1]/div[1]/div[2]/a[3]')


def click_on_tree_horizontal_lines():
    wait_element_and_click(
        '//*[contains(@class, "svg-icon svg-common--list-dims")]')


def to_pipeline():
    wait_element_and_click(
        '//*[contains(@class, "svg-icon svg-common--pipe-dims")]')


def select_my_todo():
    wait_element_and_click(
        '//*[@id="search_input_wrapper"]/div[2]/div[2]/span')
    time.sleep(1)
    wait_element_and_click('//*[@id="filter_list"]/li[1]/a/span')
    time.sleep(1)


def select_overdue_todo():
    wait_element_and_click(
        '//*[@id="search_input_wrapper"]/div[2]/div[2]/span')
    time.sleep(1)
    wait_element_and_click('//*[@id="filter_list"]/li[2]/a/span')
    time.sleep(1)


def select_all_todo():
    wait_element_and_click(
        '//*[@id="search_input_wrapper"]/div[2]/div[2]/span')
    time.sleep(1)
    wait_element_and_click('//*[@id="filter_list"]/li[4]/a')
    time.sleep(1)


def select_delete_filter_and_restore():
    wait_element_and_click(
        '//*[@id="search_input_wrapper"]/div[2]/div[2]/span')
    time.sleep(1)
    wait_element_and_click('//*[@id="filter_list"]/li[5]/a')
    time.sleep(1)
    wait_element_and_click('//*[@id="list_all_checker"]')
    time.sleep(1)
    wait_element_and_click('//*[@id="list_multiple_actions"]/div[1]/div')


def drag_lead_on_pipeline(dest):
    """ dest may be ''today'' or ''tomorrow'' """
    time.sleep(4)
    source_element = driver.find_element_by_xpath(
        '//*[starts-with(@id, "id_")]')
    today = driver.find_element_by_xpath(
        '//*[contains(@class, "pipeline_cell-today ")]' +
        '//*[contains(@class, "js-pipeline-sortable ui-sortable-handle")]')
    tomorrow = driver.find_element_by_xpath(
        '//*[contains(@class, "pipeline_cell-tomorrow")]' +
        '//*[contains(@class, "js-pipeline-sortable ui-sortable-handle")]')
    if dest == "today":
        drag_and_drop(source_element, today)
    elif dest == "tomorrow":
        drag_and_drop(source_element, tomorrow)


def change_lead_status(dest):
    """ Change lead status. Drag'n'Drop lead to stages panel """
    # Find source and dest
    source_address = driver.find_element_by_xpath(
        '//*[starts-with(@id, "id_")]')
    dest_address = driver.find_element_by_xpath(
        '//*[contains(@class, "footer__todo-line")]' +
        '//*[contains(@class, "{}")]'.format(dest))
    # Drag'n'drop
    drag_and_drop(source_address, dest_address)
    # After drop to delete click confrim
    if dest == "del":
        time.sleep(2)
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]' +
            '//*[contains(text(), "Yes")]')
    # After drop to done type comment and confirm
    elif dest == "done":
        time.sleep(2)
        wait_element_and_send_text(
            '//*[contains(@id, "modal_todo_result")]',
            random_data())
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]' +
            '//*[contains(@class, "modal-body__actions__save")]')
    time.sleep(2)


def api_create_tasks():
    from scripts.add_tasks import create_tasks
    current_url = driver.current_url
    subdomain = current_url.split('/')[2].split('.')[0]
    localisation = current_url.split('/')[2].split('.')[-1]
    driver.get(f'https://{subdomain}.amocrm.{localisation}/settings/profile/')
    login = driver.find_element_by_xpath('//*[@name="LOGIN"]').get_attribute('value')
    api_key = driver.find_element_by_xpath('//*[@class="js-user_profile__data__api_key"]').text
    create_tasks(login, api_key, subdomain, localisation)
    driver.get(current_url)


def show_more():
    """ Click show more in each column at To-do """
    # additional xpaths for different columns
    add_xpaths = ['//*[contains(@class, "pipeline_cell-group-expire")]',
                  '//*[contains(@class, "pipeline_cell-group-today")]',
                  '//*[contains(@class, "pipeline_cell-group-tomorrow")]',
                  '//*[contains(@class, "pipeline_cell-group-next_week")]'
                  ]
    # Get current number of elems of each column
    cur_num = []
    for xpath in add_xpaths:
        cur_num.append(len(driver.find_elements_by_xpath(
            '{}'.format(xpath) +
            '//*[contains(@class, "todo-line__item") ' +
            'and contains(@class, "js-pipeline-sortable")]')))
    if not all((num == 10 for num in cur_num[:3])):
        api_create_tasks()
        time.sleep(1)
    # Click on show more
    wait_element_and_click(
        '{}'.format(add_xpaths[3]) +
        '//*[contains(@class, "todo-line__load-more-label")]')
    # Scroll bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # count current number of tasks
    time.sleep(3)
    for i, xpath in enumerate(add_xpaths):
        new_num = len(driver.find_elements_by_xpath(
            '{}'.format(xpath) +
            '//*[contains(@class, "todo-line__item") ' +
            'and contains(@class, "js-pipeline-sortable")]'))
        assert new_num > cur_num[i], ("Number of tasks didn't change "
                                      "after showmore and scrolling")
    time.sleep(0.5)


def to_mail(mouse_over=False):
    if mouse_over:
        mouse_to_element('//*[contains(@href, "/mail/inbox/")]')
        time.sleep(3)
    else:
        wait_element_and_click('//*[contains(@href, "/mail/inbox/")]')
        mouse_to_element('//*[contains(@class, "n-avatar")]')
        # mouse_to_element('//*[contains(@class, "button-input-inner")'
        #    ' and contains(text(), "Mail")]')


def choice_first_pipeline():
    try:
        time.sleep(0.5)
        driver.find_element_by_xpath(
            '(//*[contains(@class, "aside__list-item-link js-navigate-link navigate-link-nodecor h-text-overflow")])[1]').click()
        time.sleep(0.5)
    except:
        logger.exception('Ошибка в нахождении указанной воронки')


def leads_settings():
    # Leads -> Pipeline -> Setup
    wait_element_and_click(
        '//*[contains(@class, "js-navigate-link list-top-nav__button-setup")]')
    time.sleep(1)


def unsorted_checkbox_toggler():
    wait_element_and_click('//*[contains(@for, "unsorted-checkbox-toggler")]')
    time.sleep(2)


def leads_back_button():
    """ Click on back button in DP settings """
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__body-right__top")]' +
        '//*[contains(@class, "digital-pipeline__back-button")]')
    time.sleep(5)


def unsorted_status(status):
    # Check is unsorted stage exist. Need to generate NoSuchElement Exception
    unsorted = driver.find_element_by_xpath(
        '//*[contains(@class, "pipeline_cell-unsorted")]')
    # Move mouse to title of incoming lead making item actions menu visible
    mouse_to_element(
        '//*[contains(@class, "pipeline-unsorted__item-head")]')
    time.sleep(2)
    # Move mouse to item actions menu
    mouse_to_element(
        '//*[contains(@class, "pipeline-unsorted__item-actions")]')
    time.sleep(2)
    if status == 'accept':
        wait_element_and_click(
            '//*[contains(@class, "pipeline-unsorted__item-action ' +
            'pipeline-unsorted__item-action_accept")]')
    elif status == 'cancel':
        wait_element_and_click(
            '//*[contains(@class, "pipeline-unsorted__item-action ' +
            'pipeline-unsorted__item-action_decline")]')


def leads_quick_add():
    wait_element_and_click(
        '//*[contains(@class, "pipeline_leads__quick_add_button")]')
    wait_element_and_send_text('//*[@id="fieldname"]', random_data())
    wait_element_and_send_text('//*[@id="price"]',
                               randint(100, 999))
    wait_element_and_send_text('//input[@id="1_fieldname"]',
                               random_data())
    wait_element_and_send_text('//*[contains(@placeholder, "Contact: Phone")]',
                               random_data())
    wait_element_and_send_text('//*[contains(@placeholder, "Contact: Email")]',
                               random_data())
    wait_element_and_click('//*[@id="quick_add_form_button"]')
    time.sleep(1)


def unqualified_leads():
    time.sleep(3)
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@class, "checkboxes_dropdown") and contains(text(), "Active statuses")]')
    wait_element_and_click('//*[contains(@class, "control-checkbox__helper control-checkbox__helper_minus")]')
    wait_element_and_click('//*[contains(@title, "Incoming leads")]')
    wait_element_and_click('//*[contains(@class, "button-input") and contains(text(), "Apply")]')


def unqualified_leads_status(status):
    if status == 'accept':
        time.sleep(2)
        wait_element_and_click('//*[contains(@class, "js-cell-action-accept")]')
        time.sleep(3)
    elif status == 'delete':
        time.sleep(2)
        wait_element_and_click(
            '//*[contains(@class, "js-cell-action-decline")]')
        time.sleep(3)


def pipeline_all_leads():
    time.sleep(10)
    wait_element_and_click('//*[@id="list__tabs"]/li[1]')


def fill_form(stand, count, limit=False):
    if ServerType == 'PROD_USA':
        url = 'https://forms.amocrm.com/queue/add'
    else:
        url = 'https://forms.amocrm.ru/queue/add'
    n = 0
    with open('settings.yml') as auth_pair:
        pair = yaml.load(auth_pair)
    if limit:
        form_hash = pair['auth'][ServerType][stand]['form_limit_hash']
        form_id = pair['auth'][ServerType][stand]['form_limit_id']
    else:
        form_hash = pair['auth'][ServerType][stand]['form_hash']
        form_id = pair['auth'][ServerType][stand]['form_id']
    while n <= count:
        name = random_data()
        phone = getrandbits(11)
        email = random_data() + '@example.com'
        note = random_data()
        payload = {'form_id': form_id, 'hash': form_hash,
                   'fields[name_1]': name,
                   'fields[1769713_1]': phone, 'fields[1769715_1]': email,
                   'fields[note_2]': note}
        requests.post(url, payload)
        n += 1


def to_stats():
    wait_element_and_click('//*[contains(@href, "/stats/")]')


def to_analysis_filters():
    wait_element_and_click(
        '//*[contains(@class, "icon icon-inline filter-icon")]')


def browser_back_button():
    driver.back()


def get_top_search_summary_int():
    summary = driver.find_element_by_xpath(
        '//*[contains(@class, "list-top-search__summary-text")]')
    sum_text = summary.text
    return int(sum_text.split(' ')[0])


def change_language(lang):
    wait_element_and_click('//*[contains(@class, "control--select--button ")]')
    if lang == 'ru':
        wait_element_and_click(
            '//*[@id="settings_form"]/div[3]/div/div/div[2]/div/ul/li[1]')
    elif lang == 'en':
        wait_element_and_click(
            '//*[@id="settings_form"]/div[3]/div/div/div[2]/div/ul/li[2]')
    elif lang == 'es':
        wait_element_and_click(
            '//*[@id="settings_form"]/div[3]/div/div/div[2]/div/ul/li[3]')
    # Save
    wait_element_and_click('//*[@id="save_profile_settings"]')
    time.sleep(1.5)


def to_settings():
    settings = driver.find_element_by_xpath('//*[@data-entity="settings"]')
    if settings.is_displayed():
        wait_element_and_click(webelement=settings)
    else:
        raise common.exceptions.ElementNotVisibleException


def random_data():
    return ''.join(
        choice(string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for _ in range(16))


def to_user_and_rights():
    # Settings -> Users
    wait_element_and_click('//*[contains(@href, "/settings/users/")]')


def to_extensions():
    # Settings -> Add-ons & Extensions
    wait_element_and_click('//*[contains(@href, "/settings/widgets/")]')


def to_profile():
    # Avatar -> Profile
    wait_element_and_click('//div[contains(@class, "n-avatar")]')
    wait_element_and_click('//*[contains(@class, "nav__top__userbar-icon")]')


def mouse_to_list():
    # Navigate mouse to lists
    time.sleep(2)
    mouse_to_element('//*[contains(@href, "/contacts/")]')
    time.sleep(3)


def add_list(test_name=None):
    # Mouse to lists -> Add list
    list_name = random_data()
    wait_element_and_click('//*[contains(@class, "footer-add")]')
    wait_element_and_send_text('//*[contains(@placeholder, "Enter name")]',
                               list_name)
    wait_element_and_send('//*[contains(@placeholder, "Enter name")]',
                          Keys.ENTER)
    time.sleep(2)
    if test_name:
        save_data_to_mongo(test_name, {'get_name': 'prev_name',
                                       'list': list_name})


def delete_unnecessary_lists():
    """ Delete all invalid lists """
    xpath = ('//*[contains(@class, "aside__list-item")]'
             '//*[contains(@class, "icon-pencil")]')
    while driver.find_elements_by_xpath(xpath):
        wait_element_and_click(xpath)
        time.sleep(0.5)
        wait_element_and_click('//*[contains(@data-action, "remove")]')
        time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-modal-accept")]')
        mouse_to_list()


def rename_list(test_name=None):
    """ Rename list custom (created) list in Lists
    Parameter:
    :test_name - - name of test used as a key in MongoDB collection.
    """
    # generate new list name
    new_list_name = random_data()
    xpath = ""
    # Set additional xpath (for the case of test_name use)
    if test_name:
        # Create a special additional xpath for correct list search
        data = find_data_in_mongo(test_name, {'get_name': 'prev_name'})
        xpath += '//*[text() = "{}"]'.format(data['list']) + '/parent::*'
        # Save new list name in Mongo
        save_data_to_mongo(test_name, {'get_name': 'new_name',
                                       'list': new_list_name})
    # Edit
    wait_element_and_click(xpath + '//*[contains(@class, "icon-pencil")]')
    wait_element_and_clear(xpath + '//*[contains(@placeholder, "Enter name")]')
    wait_element_and_send_text(
        xpath + '//*[contains(@placeholder, "Enter name")]',
        new_list_name)
    wait_element_and_send(
        xpath + '//*[contains(@placeholder, "Enter name")]',
        Keys.ENTER)
    time.sleep(0.5)


def lists_properties():
    # Mouse to lists -> Lists -> Tree Dots -> Lists Properties
    wait_element_and_click(
        '//*[contains(@class, "list__top__actions")]' +
        '//*[contains(@class, "button-input-more-inner")]')
    wait_element_and_click(
        '//*[contains(@class, "list__top__actions")]' +
        '//*[contains(@class, "edit_custom_fields")]')


def add_list_fields():
    """
    Mouse to lists -> Custom list -> Tree Dots ->
    -> Lists Properties -> Add fields of all types
    """
    field_types = (
        'Short text', 'Numeric', 'Toggle switch', 'Select', 'Multiselect',
        'Date', 'Url', 'Long text', 'Radiobutton', 'Short address'
    )
    for field in field_types:
        # Add field
        wait_element_and_click('//*[contains(@id, "cf_field_add")]')
        # Control panel with list of types
        wait_element_and_click('//*[contains(@class, "control--select--button")]')
        # choose field
        wait_element_and_click(f'//*[@title="{field}"]')
        # name it
        wait_element_and_send_text('//*[contains(@placeholder, "Field name")]', field)
        if field in ('Select', 'Multiselect', 'Radiobutton'):
            for i in range(5):
                wait_element_and_send_text(
                    f'//*[contains(@name, "enums[{i}][value]")]',
                    f"{field}_{i}"
                )
        # accept
        wait_element_and_click('//*[contains(@class, "button-input   js-modal-accept")]')


def add_item(test_name):
    # Mouse to lists -> Custom list -> Add Item
    wait_element_and_click(
        '//*[contains(@class, "button-input button-input_add ' +
        'js-add_element_btn button-input_blue")]')
    xpath_list = ['//*[contains(@class, "modal-body modal-body-relative")]//*[@name="name"]',
                  '//*[@class="field template-text "]//*[@placeholder="SKU"]',
                  '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "numeric") or contains(@placeholder, "Numeric")]',
                  '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "Price")]',
                  '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Short text" or @placeholder="text"]',
                  '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "Quantity")]',
                  '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Url" or @placeholder="url"]',
                  '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Long text" or @placehorlder="long text" or @placeholder="textarea"]',
                  '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Short address" or @placeholder="short address"]',
                  ]
    time.sleep(1)
    for xpath in xpath_list:
        if 'placeholder, "numeric"' in xpath or 'placeholder, "Price"' in xpath or 'placeholder, "Quantity"' in \
                xpath:
            random_number = randint(1000, 99999)
            # Save it to mongodb
            save_data_to_mongo(test_name,
                               {"xpath": xpath, "value": random_number})
            # Post same data to web element
            try:
                wait_element_and_send_text(xpath, random_number)
            except exceptions.InvalidElementStateException:
                assert 'This is bug' == 'Is it fixed?', "List form elements can't be manipulated when thiers count more then 8"
        else:
            rand_data = random_data()
            # Save it to mongodb
            save_data_to_mongo(test_name, {"xpath": xpath, "value": rand_data})
            # Post same data to web element
            try:
                wait_element_and_send_text(xpath, rand_data)
            except exceptions.InvalidElementStateException:
                assert 'This is bug' == 'Is it fixed?', "List form elements can't be manipulated when thiers count more then 8"
    wait_element_and_click(
        '//*[contains(@class, "field template-checkbox ")]//*[contains(@class, "control--select--button")]')
    wait_element_and_click('//*[contains(@class, "field template-checkbox ")]//*[contains(@title, "Yes")]')

    wait_element_and_click(
        '//*[contains(@class, "field template-select ")]//*[contains(@class, "control--select--button")]')
    wait_element_and_click(
        '//*[contains(@class, "field template-select ")]//*[contains(@title, "2")]')
    wait_element_and_click(
        '//*[contains(@class, "field template-multiselect ")]//*[contains(@class, "checkboxes_dropdown__title-selected")]')
    wait_element_and_click(
        '//*[contains(@class, "field template-multiselect ")]//*[contains(@title, "2")]')
    wait_element_and_click(
        '//*[contains(@class, "field template-radio ")]//*[contains(@class, "control--select--button")]')
    wait_element_and_click('//*[contains(@class, "field template-radio ")]//*[contains(@title, "2")]')
    wait_element_and_send(
        '//*[contains(@class, "date_field linked-form__cf empty")]',
        make_date("20.04.2019"))
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(2)


def all_leads_tab():
    # Leads -> All leads tab
    time.sleep(1)
    wait_element_and_click('//*[contains(@class, "list__tab-item")]')


def first_lead():
    # Leads -> All leads -> Horizontal lines -> First lead
    time.sleep(1)  # Don't touch this
    leads = driver.find_elements_by_xpath(
        '//*[contains(@href, "/leads/detail/")]')
    leads[0].click()
    time.sleep(1)


def pipeline_horizontal_lines():
    # Leads -> Horizontal lines
    # time.sleep(2)
    wait_element_and_click('//*[contains(@title, "List")]')
    time.sleep(0.5)


def pipeline_vertical_lines():
    # Leads -> Vertical lines
    # time.sleep(2)
    wait_element_and_click('//*[contains(@class, "list-top-nav__icon-button_pipe")]')
    time.sleep(0.5)


def edit_tabs():
    """ Click on Setup in card """
    time.sleep(2)
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item-inner") ' +
        'and contains(text(), "Setup")]')
    time.sleep(0.5)


def manage_tabs_add():
    """ Create a custom tab "list" in card """
    time.sleep(1)
    # click on "plus"
    wait_element_and_click(
        '//*[contains(@class, "card-cf__top")]' +
        '//*[contains(@data-id, "settings")]')
    # Select group
    wait_element_and_click(
        '//*[contains(@class, "control--select")]' +
        '/button[@data-value = "new_group"]')
    wait_element_and_click(
        '//*[contains(@class, "modal-body__inner")]' +
        '//*[@title = "list"]')
    # Add
    wait_element_and_click(
        '//*[contains(@class, "modal-body")]' +
        '//*[contains(@class, "button-input") and contains(text(), "Add")]')
    time.sleep(1)
    # Close
    wait_element_and_click(
        '//*[contains(@class, "card-cf__close js-card-cf-close")]')
    time.sleep(1)


def manage_tabs_delete():
    """ Delete created tab "list" in card """
    time.sleep(0.5)
    # Select list
    wait_element_and_click(
        '//*[contains(@class, "js-card-cf-tabs")]' +
        '//*[contains(text(), "list")]')
    time.sleep(0.2)
    # click on remove
    wait_element_and_click(
        '//*[contains(@class, "js-card-cf-tabs")]' +
        '//*[contains(text(),  "list")]/parent::*' +
        '//*[contains(@class, "js-tab-remove")]')
    time.sleep(0.5)
    # Yes
    wait_element_and_click(
        '//*[contains(@class, "modal-body__actions ")]'
        '//*[contains(text(), "Yes")]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "card-cf__close js-card-cf-close")]')
    time.sleep(0.5)


def manage_tabs_check():
    """ Check existinig of "list" tab and remove delete it """
    time.sleep(2)
    list_tab = driver.find_elements_by_xpath(
        '//*[contains(@class, "card-tabs__item-inner") and text() = "list"]')
    if list_tab:
        edit_tabs()
        manage_tabs_delete()


def to_customers():
    wait_element_and_click('//*[contains(@href, "/customers/")]')


def customers_horizontal_lines():
    # Customers -> Horizontal lines
    wait_element_and_click('//*[contains(@href, "/customers/list")]')


def to_last_attached_tab():
    # Tabs under pipeline in leads\customers -> Last attached
    wait_element_and_click(
        '//*[contains(@class, "card-tabs-wrapper")]' +
        '//*[contains(@title, "list") and contains(text(), "list")]')


def attach_element_and_delete():
    """ Tabs under pipeline in leads\customers->Last attached->Attach element
    """
    # Attach
    try:
        wait_element_and_click(
            '//*[contains(@class, "js-suggest_placeholder js-add_wrapper_text ' +
            'add_new_element__label")]')
    except exceptions.NoSuchElementException:
        assert 'This is bug' == 'Is it fixed?', 'There is no button to add list in card'
    time.sleep(0.5)
    # Choice element
    elem = driver.find_elements_by_xpath(
        '//*[contains(@class, "catalog-fields__text' +
        ' catalog-fields__text--name")]')
    elem[1].click()
    # Add numbers
    wait_element_and_send_text(
        '//*[contains(@class, "catalog-fields__amount-field ' +
        'js-control-allow-numeric")]',
        randint(1000, 999999))
    # Delete
    wait_element_and_click(
        '//*[contains(@class, "catalog-fields__text ' +
        'catalog-fields__text--name")]')
    time.sleep(1)
    delete = driver.find_elements_by_xpath(
        '//*[contains(@class, "linked-form__field__more")]')
    wait_element_and_click(webelement=delete[-1])
    time.sleep(1)


def to_contacts():
    # Lists -> Contacts
    try:
        url = driver.current_url
        domain = url.split('/')[2]
        driver.get(f'https://{domain}/contacts/list/contacts/')

    except exceptions:
        logger.exception('Не удалось перейти к контактам')


def to_companies():
    # Lists -> Companies
    url = driver.current_url
    domain = url.split('/')[2]
    driver.get(f'https://{domain}/contacts/list/companies/')


def first_contact():
    # Lists -> Contacts -> First contact
    time.sleep(1)  # Don't touch this
    leads = driver.find_elements_by_xpath(
        '//*[contains(@href, "/contacts/detail/")]')
    leads[0].click()
    time.sleep(1)


def to_contacts_and_companies():
    # Lists -> All Contacts and Companies
    url = driver.current_url
    domain = url.split('/')[2]
    driver.get(f'https://{domain}/contacts/list/')


def first_company():
    # Lists -> Companies -> First company
    time.sleep(1)  # Don't touch this
    leads = driver.find_elements_by_xpath(
        '//*[contains(@href, "/companies/detail/")]')
    leads[0].click()
    time.sleep(1)


def to_custom_list():
    # Lists -> Your own custom list
    mouse_to_list()
    lists_elem = driver.find_elements_by_xpath(
        '//*[contains(@href, "/catalogs/")]')
    if len(lists_elem) >= 1:
        lists_elem[0].click()
    else:
        add_list()
        to_custom_list()


def list_sort_by():
    # Lists -> Your own custom list -> Sort by SKU, Name, Quantity, Price
    cells = ['SKU', 'Name', 'Quantity', 'Price']
    for cell in cells:
        wait_element_and_click(
            '//*[contains(@class, "cell-head__title") '
            'and contains(text(), "{}")]'.format(cell))
        wait_element_and_click('//*[contains(@data-sort, "ASC")]')
        time.sleep(3)
        wait_element_and_click(
            '//*[contains(@class, "cell-head__title") ' +
            'and contains(text(), "{}")]'.format(cell))
        wait_element_and_click('//*[contains(@data-sort, "DESC")]')
        time.sleep(3)


def delete_list_element():
    # Lists -> Your own custom list -> Choice element of list -> Delete
    time.sleep(1)
    lists_elem = driver.find_elements_by_xpath('//*[contains(@id, "lead_")]')
    lists_elem[6].click()
    wait_element_and_click('//*[contains(@data-type, "delete")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)


def import_list():
    # Lists -> Your own custom list -> Tree dots -> Import
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner button-input-more-inner")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item__text") ' +
        'and text()="Import"]')
    wait_element_and_send(
        '//*[contains(@type, "file")]',
        "/home/autotester/test_data/import_example_catalogs_beta_en.csv")
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(10)
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Continue with crm")]')
    time.sleep(0.5)


def delete_list():
    # Mouse to lists -> Edit list -> delete
    wait_element_and_click('//*[contains(@data-action, "edit")]')
    wait_element_and_click('//*[contains(@data-action, "remove")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)


def new_customer():
    # Customers -> New Customer
    wait_element_and_click('//*[contains(@href, "/customers/add/")]')


def check_name(test_name):
    customer_name = find_data_in_mongo(test_name)['value']
    customer_new = driver.find_element_by_xpath(
        '//a[contains(@title, ' + customer_name + ')]' and
        '//a[contains(@class, "js-navigate-link feed-note__gray-link")]').text
    assert customer_name == customer_new


def fill_customers(test_name=False, only_name=False):
    # Customers -> New Customer -> Fill Customers
    # Name
    name_field = random_data()
    wait_element_and_send_text('//*[contains(@id, "person_n")]', name_field)
    if only_name:
        # Expected amount
        wait_element_and_send_text('//*[contains(@id, "lead_card_budget")]',
                                   randint(100, 999))
    # Gr1
    wait_element_and_click('//*[contains(@title, "gr 1")]')
    if not only_name:
        # Text, Numeric, Checkbox
        text_field = random_data()
        num_field = randint(100, 999)
        wait_element_and_send_text('//*[@id="edit_card"]/div/div[4]/div[1]/div[2]/input', text_field)
        wait_element_and_send_text('//*[@id="edit_card"]/div/div[4]/div[2]/div[2]/input', num_field)
        wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[3]/div[2]/label')
        # Select
        wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[4]/div[2]/div/button')
        wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[4]/div[2]/div/ul/li[3]')
        # Multi select (select 22)
        wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[5]/div[2]/div/div[2]/span/span')
        wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[5]/div[2]/div/div/div[1]/div[3]')
        time.sleep(1)
        # Date
        date_field = '03.01.' + str(randint(2016, 2019))
        wait_element_and_send('//*[@id="edit_card"]/div/div[4]/div[6]/div[2]//input', date_field)
        # Url
        url_field = 'http://' + random_data()
        textarea_field = random_data()
        shortaddr_field = random_data()
        wait_element_and_send_text(
            '//*[@id="edit_card"]/div/div[4]/div[7]/div[2]//input', url_field)
        # Longtext
        wait_element_and_send_text('//*[@id="edit_card"]/div/div[4]/div[8]/div[2]//textarea', textarea_field)
        # Radiobutton
        wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[9]/div[2]/label[2]')
        # Short addr
        wait_element_and_send_text('//*[@id="edit_card"]/div/div[4]/div[10]/div[2]//textarea', shortaddr_field)
    # Select expected date
    wait_element_and_click(
        '//*[contains(@class, "customers-date__caption-title")]')
    wait_element_and_send_text(
        '//*[contains(@class, "js-customers-date-date-input")]',
        make_date("31.12.2023"))
    wait_element_and_send(
        '//*[contains(@class, "js-customers-date-date-input")]',
        Keys.ENTER)
    # missclick
    wait_element_and_click('//*[contains(@class, "control-body-overlay default-overlay-visible")]')
    if not only_name:
        # Tags
        # Close calendar overlay
        # wait_element_and_click('//div[@id="control_overlay"]') calendar closes after send Keys.ENTER
        wait_element_and_click('//*[contains(@data-id, "add_tag")]')
        tag1 = random_data()
        wait_element_and_send_text(
            '//*[contains(@class, "multisuggest__input js-multisuggest-input") and @data-can-add="Y"]',
            tag1)
        wait_element_and_send(
            '//*[contains(@class, "multisuggest__input js-multisuggest-input") and @data-can-add="Y"]',
            Keys.ENTER)
    # Save
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(5)
    if test_name:
        save_data_to_mongo(test_name,
                           {'xpath': '//*[contains(@name, "name")]',
                            'value': name_field})
        if not only_name:
            save_data_to_mongo(test_name,
                               {'xpath': 'text_xpath',
                                'value': text_field})
            save_data_to_mongo(test_name,
                               {'xpath': 'num_xpath',
                                'value': num_field})
            save_data_to_mongo(test_name,
                               {'xpath': 'date_xpath',
                                'value': date_field})
            save_data_to_mongo(test_name,
                               {'xpath': 'url_xpath',
                                'value': url_field})
            save_data_to_mongo(test_name,
                               {'xpath': 'textarea_xpath',
                                'value': textarea_field})
            save_data_to_mongo(test_name,
                               {'xpath': 'shortaddr_xpath',
                                'value': shortaddr_field})
            save_data_to_mongo(test_name,
                               {'xpath': 'birthday_xpath',
                                'value': shortaddr_field})
            save_data_to_mongo(test_name,
                               {'xpath': '//*[@id="0"]/ul/li/input',
                                'value': tag1})


def create_note_with_jpg():
    # Note with jpg file
    wait_element_and_send_text_elem(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        random_data())
    mouse_to_element(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div['
        '1]/div')
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@class, "tips-item js-tips-item js-switcher-note")]')

    wait_element_and_send('//*[contains(@id, "note-edit-attach-filenew")]',
                          "/home/autotester/test_data/1.jpg")
    wait_element_and_click(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[2]/div[2]/div/button[1]')
    time.sleep(4)


def create_note_with_txt():
    # Note with txt file
    wait_element_and_send_text_elem(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        random_data())
    mouse_to_element(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div['
        '1]/div')
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@class, "tips-item js-tips-item js-switcher-note")]')

    wait_element_and_send('//*[contains(@id, "note-edit-attach-filenew")]',
                          "/home/autotester/test_data/example.txt")
    wait_element_and_click(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/' +
        'div/div[2]/div[2]/div/button[1]')
    time.sleep(3)


def download_note_jpg():
    # Note -> Download jpg
    # time.sleep(2)
    try:
        mouse_to_element('//*[contains(@class, "feed-note__media-preview")]')
        wait_element_and_click('//*[contains(@class, "js-new-window")]')
        # mouse_to_element('//*[contains(@class, "feed-note__media-preview")]')
        time.sleep(5)
    except exceptions:
        logger.exception('Не удалось скачать картинку')


def preview_note_jpg():
    # Note -> Download jpg
    wait_element_and_click('//*[contains(@class, "feed-note__media-preview")]')
    refresh_page()


def create_contact_in_customers(test_name=False):
    # Customers -> Create Contact
    wait_element_and_click('//*[@id="new_contact_n"]')
    contact_name = random_data()
    wait_element_and_send_text('//*[@id="new_contact_n"]', contact_name)
    company_name = random_data()
    wait_element_and_send_text('//*[@id="contact_company_input"]',
                               company_name)
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[1]/div[1]' +
        '/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[2]/div[1]' +
        '/div[2]/div/div[1]/input',
        random_data() + '@exmaple.com')
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[3]/div[2]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[4]/div[1]/div[2]/input',
        random_data())
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(5)
    if test_name:
        save_data_to_mongo(test_name,
                           {'xpath': '//*[@id="new_contact_n"]',
                            'value': contact_name})
        save_data_to_mongo(test_name,
                           {'xpath': '//*[@id="contact_company_input"]',
                            'value': company_name})


def create_contact_in_customers_with_fields(test_name=False):
    wait_element_and_click('//*[@id="new_contact_n"]')
    contact_name = random_data()
    wait_element_and_send_text('//*[@id="new_contact_n"]', contact_name)
    company_name = random_data()
    wait_element_and_send_text('//*[@id="contact_company_input"]',
                               company_name)
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[1]/div[1]' +
        '/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[2]/div[1]' +
        '/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[3]/div[2]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[4]/div[1]/div[2]/input',
        random_data())

    text_field = random_data()
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[5]/div[2]/input', text_field)
    num_field = randint(100, 999)
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[6]/div[2]/input', num_field)
    # Checkbox
    wait_element_and_click(
        '//*[@id="new_contact"]/div[2]/div[2]/div[7]/div[2]/label')
    # Select
    wait_element_and_click(
        '//*[@id="new_contact"]/div[2]/div[2]/div[8]/div[2]/div/button')
    wait_element_and_click(
        '//*[@id="new_contact"]/div[2]/div[2]/div[8]/div[2]/div/ul/li[3]')
    # Multiselect
    wait_element_and_click(
        '//*[contains(@class, "expanded")]' +
        '//*[contains(@class, "linked-form__field-multiselect")]' +
        '//*[@class = "linked-form__field__value "]')
    wait_element_and_click(
        '//*[contains(@class, "expanded")]//*[contains(@title, "22_contact")]')
    # Date
    date_field = '03.01.' + str(randint(2016, 2019))
    wait_element_and_send(
        '//*[@id="new_contact"]/div[2]/div[2]/div[10]/div[2]/span/input',
        date_field)
    # Url
    url_field = 'http://' + random_data()
    textarea_field = random_data()
    shortaddr_field = random_data()
    addr_field = random_data()
    birthday_field = '03.01.' + str(randint(2016, 2019))
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[11]/div[2]/div/input',
        url_field)
    # Textarea
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[12]/div[2]/div/textarea',
        textarea_field)
    # Radiobutton
    wait_element_and_click(
        '//*[@id="new_contact"]/div[2]/div[2]/div[13]/div[2]/label[2]/div')
    # Short addr
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[14]/div[2]/div/textarea',
        shortaddr_field)
    # Addr
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[2]/div[15]/div[2]/div/div[1]/input',
        addr_field)
    wait_element_and_send(
        '//*[@id="new_contact"]/div[2]/div[2]/div[15]/div[2]/div/div[1]/input',
        Keys.PAGE_DOWN)
    # Birthday
    wait_element_and_send(
        '//*[@id="new_contact"]/div[2]/div[2]/div[16]/div[2]/span/input',
        birthday_field)
    # Save
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(2)
    if test_name:
        save_data_to_mongo(test_name,
                           {
                               'contact_name_xpath': '//*['
                                                     '@id="new_contact_n"]',
                               'value': contact_name})
        save_data_to_mongo(test_name,
                           {'xpath': '//*[@id="contact_company_input"]',
                            'value': company_name})
        save_data_to_mongo(test_name,
                           {'xpath': 'text_xpath',
                            'value': text_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'num_xpath',
                            'value': num_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'date_xpath',
                            'value': date_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'url_xpath',
                            'value': url_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'textarea_xpath',
                            'value': textarea_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'shortaddr_xpath',
                            'value': shortaddr_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'addr_xpath',
                            'value': addr_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'birthday_xpath',
                            'value': birthday_field})


def fill_contact_company_with_fields(test_name=False):
    time.sleep(1)
    wait_element_and_click('//*[@id="card_tabs"]/div[3]/span')
    wait_element_and_click('//*[@id="new_company_n"]')
    time.sleep(1)
    company_name = random_data()
    wait_element_and_send_text('//*[@id="new_company_n"]', company_name)
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div/div[1]/div[1]/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div/div[2]/div[1]/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div/div[3]/div[2]/div/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div/div[4]/div[2]/div/textarea',
        random_data())
    text_field = random_data()
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div[1]/div[5]/div[2]/input', text_field)
    num_field = randint(100, 999)
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div[1]/div[6]/div[2]/input', num_field)
    # Checkbox
    wait_element_and_click(
        '//*[@id="new_company"]/div[2]/div[1]/div[7]/div[2]/label')
    # Select
    wait_element_and_click(
        '//*[@id="new_company"]/div[2]/div[1]/div[8]/div[2]/div/button/span')
    wait_element_and_click(
        '//*[@id="new_company"]/div[2]/div[1]/div[8]/div[2]/div/ul/li[3]')
    # Multiselect
    wait_element_and_click(
        '//*[@id="new_company"]/div[2]/div[1]/div[9]/div[2]' +
        '/div/div[2]/span[1]/span/div')
    wait_element_and_click(
        '//*[@id="new_company"]/div[2]/div[1]/div[9]/div[2]' +
        '/div/div[1]/div/div[3]/label/div[2]')
    # Date
    date_field = '03.01.' + str(randint(2016, 2019))
    wait_element_and_send(
        '//*[@id="new_company"]/div[2]/div[1]/div[10]/div[2]/span/input',
        date_field)
    # Url
    url_field = 'http://' + random_data()
    textarea_field = random_data()
    shortaddr_field = random_data()
    addr_field = random_data()
    birthday_field = '03.01.' + str(randint(2016, 2019))
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div[1]/div[11]/div[2]/div/input',
        url_field)
    # Textarea
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div[1]/div[12]/div[2]/div/textarea',
        textarea_field)
    # Radiobutton
    wait_element_and_click(
        '//*[@id="new_company"]/div[2]/div[1]/div[13]/div[2]/label[2]')
    # Short addr
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div[1]/div[14]/div[2]/div/textarea',
        shortaddr_field)
    # Addr
    wait_element_and_send_text(
        '//*[@id="new_company"]/div[2]/div[1]/div[15]/div[2]/div/div[1]/input',
        addr_field)
    wait_element_and_send(
        '//*[@id="new_company"]/div[2]/div[1]/div[15]/div[2]/div/div[1]/input',
        Keys.PAGE_DOWN)
    # Birthday
    wait_element_and_send(
        '//*[@id="new_company"]/div[2]/div[1]/div[16]/div[2]/span/input',
        birthday_field)
    # Save
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(2)
    if test_name:
        save_data_to_mongo(test_name,
                           {
                               'company_name_xpath': '//*['
                                                     '@id="new_company_n"]',
                               'value': company_name})
        save_data_to_mongo(test_name,
                           {'xpath': 'text_xpath',
                            'value': text_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'num_xpath',
                            'value': num_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'date_xpath',
                            'value': date_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'url_xpath',
                            'value': url_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'textarea_xpath',
                            'value': textarea_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'shortaddr_xpath',
                            'value': shortaddr_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'addr_xpath',
                            'value': addr_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'birthday_xpath',
                            'value': birthday_field})


def create_contact_in_company():
    # Company -> Create Contact
    wait_element_and_click('//*[@id="new_contact_n"]')
    wait_element_and_send_text('//*[@id="new_contact_n"]', random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[1]/div[1]/div[1]' +
        '/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[1]/div[2]/div[1]' +
        '/div[2]/div/div[1]/input',
        random_data())
    wait_element_and_send_text(
        '//*[@id="new_contact"]/div[2]/div[1]/div[3]/div[2]/input',
        random_data())
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(2)


def made_main_contact():
    # One of contacts made main
    wait_element_and_click('//*[@id="contacts_list"]/li[2]')
    time.sleep(1)
    menu = driver.find_elements_by_xpath(
        '//*[contains(@class, "linked-form__field__more  js-tip-holder")]')
    menu[1].click()
    time.sleep(1)
    main = driver.find_elements_by_xpath(
        '//*[contains(@class, "tips-item js-tips-item ' +
        'js-linked-entity-set_main")]')
    main[1].click()
    wait_element_and_click('//*[contains(@class, "body__actions__save")]')
    time.sleep(1)


def add_purchase():
    # Customers -> Customer -> Purchases -> Add purchase
    # To Purchases
    wait_element_and_click('//*[contains(@title, "Purchases")]')
    # Add
    wait_element_and_click(
        '//*[contains(@class, "js-suggest_placeholder ' +
        'add_new_element__label")]')
    # Sales Value
    wait_element_and_send(
        '//*[@class="make-purchase"]//*[contains(@class, "js-control-pretty-price")]',
        randint(10000, 999999))
    # Date of purchase
    day = randint(10, 27)
    month = randint(10, 12)
    year = randint(2019, 2023)
    random_date = str(month) + str(day) + str(year)
    time.sleep(1)
    wait_element_and_send_text('//*[contains(@name, "comment")]', random_date)
    # Save
    wait_element_and_click(
        '//*[@id="make-purchase-save"]')
    time.sleep(1)


def edit_customers_comment():
    wait_element_and_click('//*[@title="Purchases"]')
    wait_element_and_send_text('//*[contains(@name, "comment")]',
                               random_data())
    wait_element_and_click(
        '//*[contains(@class, "card-top-save-button ' +
        'card-top-name__right__save")]')


def delete_purchase():
    # Customers -> Customer -> Purchases -> Delete purchases
    wait_element_and_click('//*[contains(@class, "transaction__inner")]')
    wait_element_and_click('//*[contains(@class, "transaction-delete")]')
    wait_element_and_click('//*[contains(@class, "body__actions__save")]')
    time.sleep(0.5)


def bought_customers():
    wait_element_and_click(
        '//*[contains(@class, "customers-date__caption-title")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    ' +
        'js-purchase-button customers-date__purchase-button enabled")]')
    elem = driver.find_elements_by_xpath(
        '//*[contains(@class, "js-control-pretty-price ' +
        'js-form-changes-skip  text-input")]')
    elem[1].send_keys(randint(1, 3333))
    wait_element_and_click('//*[contains(@class, "make-purchase-save")]')


def first_customer():
    # Customers -> First customer
    time.sleep(2)  # Don't touch this
    customers = driver.find_elements_by_xpath(
        '//*[contains(@href, "/customers/detail/")]')
    customers[0].click()
    time.sleep(1)


def unlink_in_customer():
    # Customers -> First customer -> Unlink contact or company
    time.sleep(1)  # Don't touch this
    # Go to Main
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item") and @title="Main"]')
    edit = driver.find_elements_by_xpath(
        '//*[contains(@class, "icon icon-inline icon-dots-2")]')
    edit[0].click()
    unlink = driver.find_elements_by_xpath(
        '//*[contains(@class, "tips-item ' +
        'js-tips-item js-linked-entity-unlink")]')
    unlink[0].click()
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(1)


def change_customers_resp_person():
    # Customers -> Resp person
    users = ['Mister Amo', 'Senior Amo', 'Frau Amo', 'PanAmo', 'Am Am Crm']
    drop_down = choice(users)
    wait_element_and_click(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li')
    wait_element_and_send_text(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        drop_down)
    wait_element_and_send(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        Keys.ENTER)
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(0.5)


def add_fields_in_customers():
    # Customers -> Tree dots near name -> Customer fields -> Add Field
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item-inner") ' +
        'and contains(@title, "Setup")]')
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@class, "card-cf-top")]//*[@title = "gr 1"]')
    time.sleep(1)
    # Just add new field
    add_field_buttons = driver.find_elements_by_xpath(
        '//*[contains(@class, "cf-field-add js-card-cf-add-field")]')
    add_field_buttons[1].click()
    wait_element_and_send_text(
        '//*[contains(@class, "cf-field-input text-input")]', random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input   js-modal-accept")]')
    time.sleep(0.5)
    # Close
    wait_element_and_click(
        '//*[contains(@class, "card-cf__close js-card-cf-close")]')


def check_field_in_customers():
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item-inner") ' +
        'and contains(@title, "gr 1")]')
    wait_element_and_send_text(
        '(//*[contains(@class, "card-entity-form__fields no-main-group")]//*[@placeholder="..."])[last()]',
        random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input    button-input_add")]')
    time.sleep(1)


def delete_custom_fields():
    # Customers -> Tree dots near name -> Customer fields -> Delete field
    time.sleep(2)
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item-inner")' +
        ' and contains(@title, "Setup")]')
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@class, "card-cf-top")]//*[@title = "gr 1"]')
    time.sleep(1)
    # Delete created fields
    fields = driver.find_elements_by_xpath(
        '//*[contains(@class, "cf-group-wrapper js-cf-group-wrapper") ' +
        'and not(contains(@data-id, "default"))]' +
        '//*[contains(@class, "cf-field-wrapper sortable")]' +
        '//descendant::*[contains(@class, "cf-field-view__name")' +
        ' and not(contains(text(), "text")) and not(contains(text(),' +
        ' "numeric")) and not(contains(text(), "checkbox")) ' +
        'and not(contains(text(), "date")) and not(contains(text(), ' +
        '"select")) and not(contains(text(), "url")) and ' +
        'not(contains(text(), "radiobutton")) ' +
        'and not(contains(text(), "Short")) and not(contains(text(), ' +
        '"Position")) and not(contains(text(), "IM")) and not(' +
        'contains(text(), "short"))]')
    for field in fields:
        field.click()
        wait_element_and_click(
            '//*[contains(@class, "cf-field-edit__remove js-modal-trash")]')
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-modal-accept")]')
        time.sleep(2)
    wait_element_and_click(
        '//*[contains(@class, "card-cf__close")]')


def customer_list_settings():
    # Customers -> List -> List settings
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu ")][@title="More"]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item__icon ' +
        'svg-icon svg-common--settings-key-dims")]')
    time.sleep(0.5)


def sort_customers():
    # Customers -> List -> Sort
    cells = ['Name', 'Expected purchase amount', 'Next purchase']
    for cell in cells:
        wait_element_and_click(
            '//*[contains(@class, "cell-head__title") and text()="{}"]'.format(
                cell))
        wait_element_and_click('//*[contains(@data-sort, "ASC")]')
        time.sleep(2)
        wait_element_and_click(
            '//*[contains(@class, "cell-head__title") and text()="{}"]'.format(
                cell))
        wait_element_and_click('//*[contains(@data-sort, "DESC")]')
        time.sleep(0.5)


def to_customers_import():
    # Customers -> List -> Import
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu ")][@title="More"]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item ' +
        ' element__ js-list-import")]')


def import_customers():
    # Customers -> Tree dots -> Import
    wait_element_and_send(
        '//*[contains(@type, "file")]',
        "/home/autotester/test_data/import_example_customers_beta_en.csv")
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(10)
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Continue with crm")]')
    time.sleep(0.5)


def customers_pipeline():
    # Customers -> Vertical lines
    time.sleep(0.5)
    wait_element_and_click('//*[contains(@href, "/customers/pipeline")]')
    time.sleep(0.5)


def drag_leads_in_customers():
    # Customers -> Pipeline -> Drag user from Rec.
    # Purchased to Expected Purch with iteration on all columns
    source = driver.find_elements_by_xpath(
        '//*[contains(@class, "pipeline_leads__lead-title")]')
    source_element_xpath = '//*[contains(text(), "{0}")]'.format(source[0].text)
    columns = ['//*[contains(@title, "Переговоры")]//ancestor::'
               '*[contains(@class, "pipeline_cell-head")]//following-sibling::'
               '*[contains(@class, "pipeline_items__list")]',
               '//*[contains(@title, "Принимают решение")]//ancestor::'
               '*[contains(@class, "pipeline_cell-head")]//following-sibling::'
               '*[contains(@class, "pipeline_items__list")]',
               ]
    for col in columns:
        colums = driver.find_element_by_xpath(col)
        source_element = driver.find_element_by_xpath(source_element_xpath)
        drag_and_drop(source_element, colums)
        time.sleep(0.5)
    time.sleep(1)


def drag_lead_in_customers_limited(test_name):
    # Customers -> Pipeline -> Trying to drag user from Rec.
    # Purchased to Expected Purch with iteration on all columns
    # if don't perform -> raise exception
    source_element = find_lead_element_in_customers()
    drag_and_drop(source_element, driver.find_element_by_xpath(
        '//*[@id="pipeline_holder"]/div/div/div[2]/div[2]'))
    save_data_to_mongo(test_name, {'element_id': source_element.text})
    second_lead = find_lead_element_in_customers().text
    if find_data_in_mongo(test_name, {'element_id': second_lead}):
        raise common.exceptions.TimeoutException
    else:
        pass


def find_lead_element_in_customers():
    # Customers -> Pipeline -> Find Lead WebElement
    source = driver.find_elements_by_xpath(
        '//*[contains(@class, "pipeline_leads__lead-title")]')
    source_element = source[0]
    return source_element


def leads_customers_to_purchase():
    # Customers -> Pipeline -> Drag user to purchase
    source = driver.find_elements_by_xpath(
        '//*[contains(@class, "pipeline_leads__lead-title")]')
    source_element = source[-1]
    dest = driver.find_element_by_xpath(
        '//*[contains(@data-action, "purchase")]')
    drag_and_drop(source_element, dest)
    time.sleep(0.5)
    wait_element_and_clear(
        '//*[contains(@class, "js-control-pretty-price ' +
        'js-form-changes-skip  text-input")]')
    wait_element_and_send_text(
        '//*[contains(@class, "js-control-pretty-price ' +
        'js-form-changes-skip  text-input")]',
        randint(100, 999))
    wait_element_and_click('//*[contains(@class, "customers-date")]')
    wait_element_and_click(
        '//*[contains(@class, "customers-date__months")]' +
        '//*[contains(@class, "control--select--button") ]')
    wait_element_and_click('//*[@title = "December 2020"]')
    wait_element_and_click('//*[@id="control_overlay"]')
    wait_element_and_click('//*[contains(@class, "js-make-purchase-save")]')
    time.sleep(0.5)


def leads_customers_close():
    # Customers -> Pipeline -> Drag user to close
    source = driver.find_elements_by_xpath(
        '//*[contains(@class, "pipeline_leads__lead-title")]')
    source_element = source[-1]
    dest = driver.find_element_by_xpath('//*[contains(@data-action, "close")]')
    drag_and_drop(source_element, dest)
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)


def leads_customers_delete():
    # Customers -> Pipeline -> Drag user to delete
    time.sleep(1)
    source = driver.find_elements_by_xpath(
        '//*[contains(@class, "pipeline_leads__lead-title")]')
    source_element = source[-1]
    dest = driver.find_element_by_xpath(
        '//*[contains(@data-action, "delete")]')
    drag_and_drop(source_element, dest)
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)


def all_leads():
    # Mouse to Leads -> All leads
    wait_element_and_click('//*[contains(@href, "/leads/list/")]')


def new_lead():
    # Mouse to Leads -> All leads -> + New Lead
    wait_element_and_click('//*[contains(@href, "/leads/add/")]')


def check_number_of_fields_in_leads():
    """ Check number n of leads in lead card and
    if n>12 delete non-standart fields
    """
    fields_xpath = ('//*[contains(@class, "cf-section")]'
                    '//*[contains(@class, "cf-field-wrapper sortable")]')
    for _ in driver.find_elements_by_xpath(fields_xpath)[11:]:
        fields = driver.find_elements_by_xpath(fields_xpath)
        # Click on last field
        wait_element_and_click(webelement=fields[-1])
        time.sleep(0.5)
        # Click on trash
        wait_element_and_click('//*[contains(@class, "modal-trash")]')
        # Click on modal "Yes"
        wait_element_and_click(
            '//*[contains(@class, "modal-body")]' +
            '//*[contains(text(), "Yes")]')
        time.sleep(0.5)


def add_fields_in_leads(test_name, init_mongo=True):
    # Leads -> Setup -> Gr1 -> Add field
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item-inner")' +
        ' and contains(@title, "Setup")]')
    wait_element_and_click(
        '//*[contains(@class, "card-cf__top js-card-cf-top")]' +
        '//*[@title =  "gr 1"]')
    time.sleep(1)
    check_number_of_fields_in_leads()
    # Just add new field
    add_field_buttons = driver.find_elements_by_xpath(
        '//*[contains(@class, "cf-field-add js-card-cf-add-field")]')
    add_field_buttons[1].click()
    field_1 = random_data()
    wait_element_and_send_text(
        '//*[contains(@class, "cf-field-input text-input")]', field_1)
    wait_element_and_click(
        '//*[contains(@class, "button-input   js-modal-accept")]')
    time.sleep(0.5)
    # Add new field, select "optional" and save
    add_field_buttons[1].click()
    field_2 = random_data()
    wait_element_and_send_text(
        '//*[contains(@class, "cf-field-input text-input")]', field_2)
    wait_element_and_click(
        '//*[contains(@class, "control--select--button-inner")' +
        ' and text()="Optional"]')
    wait_element_and_click(
        '//*[contains(@class, "cf-field-edit_")]' +
        '//*[contains(@class, "control--select--list")]/li[2]')
    wait_element_and_click(
        '//*[contains(@class, "button-input   js-modal-accept")]')
    time.sleep(0.5)
    # Close
    wait_element_and_click(
        '//*[contains(@class, "card-cf__close js-card-cf-close")]')
    # save fields name to mongo
    data = {'field_1': field_1, 'field_2': field_2}
    if init_mongo:
        save_data_to_mongo(test_name, data)
    else:
        update_data_in_mongo(test_name, data)


def check_req_field_in_leads(test_name):
    # Lead -> gr1 -> fill not req field and save -> must be error
    # -> fill req field and then not req -> save
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item-inner")' +
        ' and contains(@title, "gr 1")]')
    data = find_data_in_mongo(test_name)
    wait_element_and_send_text(
        '//*[contains(text(), "{}")]'.format(data['field_1']) +
        '/parent::*/following-sibling::*//input',
        random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input    button-input_add")]')
    # Check error ( save must be error so we click on cancel button)
    assert driver.find_element_by_xpath(
        '//*[contains(@class, "validation-button-cap")]')
    # After save must be error so we click on cancel button
    wait_element_and_send_text(
        '//*[contains(text(), "{}")]'.format(data['field_2']) +
        '/parent::*/following-sibling::*//input',
        random_data())
    time.sleep(2)
    wait_element_and_click(
        '//*[contains(@id, "card_fields")]'
        '//*[contains(@class, "card-fields__button-block")]'
        '//*[contains(text(), "Save")]')
    time.sleep(1)


def delete_fields_in_leads(test_name):
    # Leads -> Setup -> Gr1 -> Delete
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item-inner")' +
        ' and contains(@title, "Setup")]')
    wait_element_and_click(
        '//*[contains(@class, "card-cf__top js-card-cf-top")]' +
        '//*[@title =  "gr 1"]')
    time.sleep(1)
    # Delete created fields
    data = find_data_in_mongo(test_name)
    for field in ['field_1', 'field_2']:
        wait_element_and_click(
            '//*[contains(@class, "cf-field-view__name")'
            ' and contains(text(), "{}")]'.format(data[field]))
        wait_element_and_click(
            '//*[contains(@value, "{}")]/ancestor::*'.format(data[field]) +
            '[contains(@class, "cf-field-wrapper__body edit-mode")]'
            '//*[contains(@class, "cf-field-edit__remove")]')
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]'
            '//*[contains(text(), "Yes")]')
        time.sleep(4)


def check_main_fields_in_card(field_type):
    """ Check card fields in main tab and delete invalid fields
    Parameters:
    :parameter field_type - str, type of card fields need to check
    """
    assert field_type in ('leads', 'contacts', 'companies'), \
        "Wrong field_type value! Use 'leads' or 'contacts'"
    wait_element_and_click(
        '//*[contains(@class, "card-tabs__item-inner") and @title="Setup"]')
    fields_xpath = (
            '//*[contains(@class, "cf-section") and '
            + 'contains(@data-type, "{}")]'.format(field_type)
            + '//*[contains(@data-id, "default")]'
            + '//*[contains(@class, "cf-field-view__name")]')
    time.sleep(0.5)
    if field_type == 'leads':
        valid_fields = ['sales value']
    elif field_type in ('contacts', 'companies'):
        valid_fields = ('url',
                        'checkbox',
                        'numeric',
                        'phone',
                        'position',
                        'email',
                        'short address',
                        'select',
                        'add field',
                        'text',
                        'textarea',
                        'radiobutton',
                        'address',
                        'date',
                        'birthday',
                        'im',
                        'address',
                        'multiselect',
                        'web',
                        'contact name',
                        'company name',
                        'user terms',
                        )
    fields = driver.find_elements_by_xpath(fields_xpath)
    for field in fields:
        field_text = field.text.strip().lower()
        if field_text not in valid_fields:
            wait_element_and_click(
                '//*[contains(@class, "card-cf__inner")]'
                '//*[contains(text(), "{}")]'.format(field_text))
            wait_element_and_click(
                '//*[contains(@data-type, "{}")]'.format(field_type)
                + '//*[contains(@class, "cf-field-edit__remove")]')
            wait_element_and_click(
                '//*[contains(@class, "modal-body__inner")]'
                '//*[contains(@class, "modal-body__actions__save")]')
            time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "card-cf__close")]')


def leads_list_settings():
    # Mouse to leads -> Leads -> Tree Dots -> Lists settings
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner button-input-more-inner")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item__icon' +
        ' svg-icon svg-common--settings-key-dims")]')


def sort_leads():
    # Leads -> List -> All leads -> Sort
    cells = ['Last Modified', 'Lead title', 'Sale,']
    for cell in cells:
        wait_element_and_click(
            '//*[contains(@class, "cell-head__title") and contains(text(), '
            '"{}")]'.format(
                cell))
        wait_element_and_click('//*[contains(@data-sort, "ASC")]')
        time.sleep(2)
        wait_element_and_click(
            '//*[contains(@class, "cell-head__title") and contains(text(), '
            '"{}")]'.format(
                cell))
        wait_element_and_click('//*[contains(@data-sort, "DESC")]')
        time.sleep(2)


def select_three_leads():
    # Leads -> List -> All leads -> Select three leads
    time.sleep(1)
    lead = driver.find_elements_by_xpath(
        '//*[contains(@id, "lead_") and @type="checkbox"] | //*[contains(@class, "control-checkbox pipeline_leads__lead-checkbox  ")]')
    lead[6].click()
    lead[7].click()
    lead[8].click()
    time.sleep(1)


def create_customers(session, n):
    arr = []
    for _ in range(n):
        name = random_data()
        next_date = datetime.datetime.now().timestamp()
        arr.append({'name': name, 'next_date': next_date})
    url = f'https://{session.subdomain}.amocrm.{session.domain}/api/v2/customers'
    session.session.post(url, json={'add': arr})


def import_leads():
    # Leads -> Tree dots -> Import
    wait_element_and_send(
        '//*[contains(@type, "file")]',
        "/home/autotester/test_data/import_example_leads_beta_en.csv")
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(5)
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept ' +
        'js-button-with-loader modal-body__actions__save' +
        ' js-processing-cont-to-work")]')
    time.sleep(0.5)


def export_leads():
    # Leads -> Tree dots -> Export
    wait_element_and_click('//*[contains(@href, "/ajax/leads/export/")]')
    time.sleep(1)
    wait_element_and_click('//*[contains(@class, "modal-body__close")]')
    time.sleep(0.5)


def to_export():
    """ To export menu """
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "list__top__actions")]//*[contains(@class, "button-input  button-input-with-menu")]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item__icon' +
        ' svg-icon svg-common--download-dims")]')


def lead_to_dlw(dest):
    """ Leads -> Pipeline -> Drag user to delete or lost or won """
    source = driver.find_elements_by_xpath(
        '//*[contains(@class, "pipeline_leads__lead-title")]')
    source_element = source[-1]
    if dest == 'delete':
        destination = driver.find_element_by_xpath(
            '//*[contains(@data-status-id, "delete")]')
    elif dest == 'lost':
        destination = driver.find_element_by_xpath(
            '//*[contains(@data-status-id, "143")]')
    elif dest == 'lost_reason':
        destination = driver.find_element_by_xpath(
            '//*[contains(@data-status-id, "143")]')
    elif dest == 'won':
        destination = driver.find_element_by_xpath(
            '//*[contains(@data-status-id, "142")]')
    drag_and_drop(source_element, destination)
    time.sleep(0.5)
    if dest != 'lost_reason':
        confirm = driver.find_elements_by_xpath(
            '//*[contains(@class, "button-input    js-modal-accept")]')
        if confirm:
            wait_element_and_click(
                '//*[contains(@class, "button-input    js-modal-accept")]')
        time.sleep(1)


def leads_add_pipeline():
    """ Mouse to leads -> Add new pipeline """
    wait_element_and_click('//*[contains(@title, "Add pipeline")]')
    wait_element_and_send_text(
        '//*[contains(@placeholder, "New pipeline name")]', random_data())
    wait_element_and_click('//*[contains(@data-action, "add")]')
    time.sleep(0.5)


def leads_pipeline_settings():
    """ Leads -> Tree dots near name -> Leads fields -> Pipeline settings """
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and text()="Setup pipeline"]')
    time.sleep(0.5)


def change_lead_resp_person():
    """ Lead -> Change Resp person to random """
    users = ['Mister Amo', 'Senior Amo', 'Frau Amo', 'PanAmo']
    drop_down = choice(users)
    wait_element_and_click(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li')
    wait_element_and_send_text(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        drop_down)
    wait_element_and_send(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        Keys.ENTER)
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(2)


def new_contact():
    """ Mouse to Lists -> Contacts -> + Add Contact """
    wait_element_and_click('//*[contains(@href, "/contacts/add/")]')


def new_company():
    """ Mouse to Lists -> Company -> + Add Company """
    wait_element_and_click('//*[contains(@href, "/companies/add/")]')


def favorite_note():
    """ Favorite note """
    mouse_to_element(
        '//*[contains(@class, "feed-note  feed-note-with-context")]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "feed-note__context__item pinner' +
        ' js-note-pinner")]')
    time.sleep(0.5)


def change_note_content():
    """ Change note content """
    wait_element_and_click(
        '//*[contains(@class, "feed-note  feed-note-with-context")]')
    wait_element_and_send_text(
        '//*[contains(@class, "feed-note__textarea custom-scroll' +
        ' textarea-autosize")]',
        random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input   js-note-submit ' +
        'feed-note__button")]')
    time.sleep(1)


def take_screenshot(test_name):
    """ Take screenshot. Call it when test failed """
    screenshots_basedir = '/var/www/selenium/screenshots/'
    dt_now = datetime.datetime.now()
    screenshot_basename = '{:%d_%m_%Y_%H_%M_%S}_{}.png'.format(dt_now, test_name)
    dir_name = '{:%d_%m_%Y}'.format(dt_now)
    screenshots_dir = os.path.join(screenshots_basedir, dir_name)
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    driver.save_screenshot(
        os.path.join(screenshots_dir, screenshot_basename))
    command = '/usr/sbin/ifconfig -a | awk \'$1=="inet"{print $2}\' | grep "10.13"'
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = process.communicate()
    ip = out.split(b'\n')[0].decode("utf-8")
    print(f'screenshot: http://{ip}/{dir_name}/{screenshot_basename}')


def sort_contacts():
    """ Contacts -> List -> Sort """
    wait_element_and_click(
        '//*[contains(@class, "cell-head__title") and contains(text(), "Name")]')
    wait_element_and_click('//*[contains(@data-sort, "ASC")]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "cell-head__title") and text()="Name"]')
    wait_element_and_click('//*[contains(@data-sort, "DESC")]')
    time.sleep(0.5)


def all_list_settings():
    """ List -> Contacts and Companies -> List settings """
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu ")][@title="More"]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item__icon ' +
        'svg-icon svg-common--settings-key-dims")]')


def to_all_export():
    """ Export in contacts and companies """
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu ")][@title="More"]')
    list_settings = driver.find_elements_by_xpath(
        '//*[contains(@class, "content__top__action__btn-more")]//*[contains(@class, "button-input__context-menu__item__text")]')
    list_settings[2].click()


def to_all_import():
    """ Import in contacts and companies """
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu ")][@title="More"]')
    time.sleep(1)
    list_settings = driver.find_elements_by_xpath(
        '//*[contains(@class, "content__top__action__btn-more")]//*[contains(@class, "button-input__context-menu__item__text")]')
    list_settings[3].click()


def export_contacts():
    """ Contacts -> Tree dots -> Export """
    wait_element_and_click('//*[contains(@href, "/ajax/contacts/export/")]')
    wait_element_and_click('//*[contains(@class, "modal-body__close")]')


def create_mail_template(with_attach=False):
    """ Mail -> Settings -> Add template """
    time.sleep(3)
    # Go to settings
    wait_element_and_click('//*[contains(@href, "/mail/settings/")]')
    time.sleep(1)
    wait_element_and_click(
        '//*[contains(@id, "mail-templates__add-template")]')
    time.sleep(1)
    wait_element_and_send_text('//*[contains(@placeholder, "New template")]',
                               random_data())
    time.sleep(1)
    wait_element_and_send_text('//*[contains(@placeholder, "Subject")]',
                               random_data())
    time.sleep(1)
    wait_element_and_send_text('//*[contains(@id, "template-content")]',
                               random_data())
    time.sleep(1)
    if with_attach:
        wait_element_and_send('//*[contains(@type, "file")]',
                              "/home/autotester/test_data/1.jpg")
    time.sleep(1)
    wait_element_and_click('//*[contains(@class, "js-modal-accept")]')
    time.sleep(4)
    wait_element_and_click(
        '//*[contains(@class, "mail-action__top-controls")]')
    time.sleep(1)
    refresh_page()


def mail_multi(do_type, is_limit=None):
    """ Mail -> Choice first mail -> Do shit """
    time.sleep(1)
    if is_limit:
        choice_first_mail()
    else:
        choice_first_mail(0, do_type)
    time.sleep(5)
    if do_type == "readed":
        # Unlink first mail
        choice_first_mail()
        # select unread message
        wait_element_and_click(
            '//*[contains(@class, "list-row_unreaded")]'
            '//descendant::*[contains(@type, "checkbox")]')
        wait_element_and_click('//*[contains(@data-type, "multi_read")]')
        time.sleep(0.5)
    elif do_type == "delete":
        wait_element_and_click('//*[contains(@data-type, "delete_thread")]')
        time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "modal-body__actions__save")]'
            '//descendant::*[contains(text(), "Confirm")]')
        time.sleep(0.5)
    elif do_type == "reply":
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions__item__icon ' +
            'icon icon-mail-reply")]')
        # Template
        wait_element_and_click('//*[contains(@class, "control--select--'
                               'button")]//descendant::*[contains(text(), "Without template")]')
        wait_element_and_click('//*[contains(@class, "control--select--list'
                               '--item-inner") and (contains(@title, "шаблон не удалять") or '
                               'contains(@title, "donotdelete"))]')
        # From
        wait_element_and_click(
            '//*[contains(@class, "control--select modal_' +
            'write-mail__mailboxes-select")]')
        wait_element_and_click('//*[contains(@class, "custom-scroll control--select--'
                               'list-opened")]//descendant::*[contains(@class, "control--select--list'
                               '--item-inner") and contains(@title, "boss.selenium@mail.ru")]')
        # {{contact.name}}
        # {{profile.name}}
        # {{profile.phone}}
        action_tags = driver.find_elements_by_xpath('//*[@class="mail-action__tag"]')
        for tag in action_tags:
            tag.click()
            time.sleep(0.5)
        # Contant
        wait_element_and_send_text('//*[contains(@id, "template-content")]',
                                   random_data())
        wait_element_and_click(
            '//*[contains(@class, "js-modal-accept js-button-with-loader")]'
            '//descendant::*[contains(text(), "Send")]')
        time.sleep(7)
    elif do_type == "mailing":
        first_mail = driver.find_elements_by_xpath(
            '//*[contains(@id, "lead_")]')
        for i in range(7, 12):
            first_mail[i].click()
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions__item__icon icon '
            'icon-mailing")]')
        time.sleep(1)
        wait_element_and_click(
            '//*[contains(@class, "js-modal-accept js-button-with-loader'
            ' button-input_blue")]')
        time.sleep(10)
    elif do_type == "add_contacts":
        wait_element_and_click('//*[contains(@data-type, "add_contacts")]')
        wait_element_and_click(
            '//*[contains(@class, "js-modal-accept js-button-with-loader") and @title="Create contacts"]')
        time.sleep(10)
        # To contact and create customer
        fi_contact = driver.find_elements_by_xpath(
            '//*[contains(@href, "/contacts/detail/")]')
        fi_contact[0].click()
        wait_element_and_click('//*[contains(@class, "js-note-mail-message")]')
        wait_element_and_click(
            '//*[contains(@class, "button-input-wrapper  ' +
            'button-input-more mail_thread__create-more")]')
        wait_element_and_click(
            '//*[contains(@class, "mail_thread__create_customer")]')
        wait_element_and_click(
            '//*[contains(@class, "js-modal-accept js-button-with-loader") and @title="Create customer"]')
        # Unlink and create lead
        wait_element_and_click(
            '//*[contains(@class, "thread__lead-more-button")]')
        wait_element_and_click(
            '//*[contains(@class, "tips-item js-tips-item ' +
            'js-linked-entity-unlink")]')
        wait_element_and_click(
            '//*[contains(@class, "mail_thread__create_lead")]')
        wait_element_and_click(
            '//*[contains(@class, "js-modal-accept js-button-with-loader")]')
        wait_element_and_click(
            '//*[contains(@class, "thread__lead-more-button")]')
        wait_element_and_click(
            '//*[contains(@class, "tips-item js-tips-item ' +
            'js-linked-entity-unlink")]')
        # Close
        wait_element_and_click('//*[contains(@class, "modal-body__close")]')
        time.sleep(1)
        browser_back_button()
        time.sleep(1)
    elif do_type == "add_leads":
        # Get id of checked mail
        mail_id = get_mail_id()
        # Click add leads
        wait_element_and_click('//*[contains(@data-type, "add_leads")]')
        wait_element_and_click(
            '//*[contains(@class, "js-modal-accept js-button-with-loader")'
            ' and contains(@title, "Create lead")]')
        time.sleep(6)
        lead = driver.find_elements_by_xpath(
            '//*[contains(@data-id, "{}")]'
            '//*[contains(@href, "/leads/detail/")]'.format(mail_id))
        lead[0].click()
        # Find mail (not template)
        time.sleep(2)
        expand = driver.find_elements_by_xpath(
            '//*[contains(@class, "feed-note__blue-link js-grouped-expand")]')
        if expand:
            feed_note_expand()
        mail = driver.find_elements_by_xpath(
            '//*[contains(@class, "js-note-mail-message")]')
        assert len(mail) != 0, 'No mails found in feed'
        time.sleep(0.5)
        lead = driver.find_element_by_xpath(
            '//*[contains(@class, "js-navigate-link feed-note__gray-link")]')
        assert lead, 'No Lead created in feed'
        browser_back_button()
        refresh_page()
        # Unlink and create lead
        wait_element_and_click(
            '//*[contains(@data-id, "{}")]'
            '//*[contains(@href, "/mail/thread/")]'.format(mail_id))
        wait_element_and_click(
            '//*[contains(@class, "button-input-more mail_thread__create-more")]')
        wait_element_and_click(
            '//*[contains(@class, "button-input__context-menu__'
            'item__icon icon icon-inline icon-unlink")]')
        time.sleep(2)
        # Close
        browser_back_button()
        refresh_page()
    elif do_type == "add_customers":
        # Get id of checked mail
        mail_id = get_mail_id()
        wait_element_and_click('//*[contains(@data-type, "add_customers")]')
        wait_element_and_click(
            '//*[contains(@class, "js-modal-accept js-button-with-loader")'
            ' and contains(@title, "Create customer")]')
        time.sleep(5)
        fir_contact = driver.find_elements_by_xpath(
            '//*[contains(@data-id, "{}")]'
            '//*[contains(@href, "/customers/detail/")]'.format(mail_id))
        fir_contact[0].click()
        # Find mail (not template)
        time.sleep(2)
        expand = driver.find_elements_by_xpath(
            '//*[contains(@class, "feed-note__blue-link js-grouped-expand")]')
        if expand:
            feed_note_expand()
        time.sleep(1)
        mail = driver.find_elements_by_xpath(
            '//*[contains(@class, "js-note-mail-message")]')
        assert len(mail) != 0, 'No mails found in feed'
        time.sleep(0.5)
        lead = driver.find_element_by_xpath(
            '//*[contains(@class, "js-navigate-link feed-note__gray-link")]')
        assert lead, 'No Lead created in feed'
        lead_text = lead.text
        browser_back_button()
        refresh_page()
        # Reply from mail
        wait_element_and_click(
            '//*[contains(@data-id, "{}")]'
            '//*[contains(@href, "/mail/thread/")]'.format(mail_id))
        time.sleep(2)
        # Click reply
        wait_element_and_click(
            '//*[contains(@class, "compose-mail-header__field '
            'compose-mail-header__field_to js-compose-mail-to_field-container")]')
        wait_element_and_send_text_elem(
            '//*[contains(@class, "ql-editor")]', random_data())
        time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "js-note-edit-cancel feed-note__button_cancel")]')
        time.sleep(1)
        # Unlink customer
        wait_element_and_click(
            '//*[contains(@class, "button-input-more-inner")]')
        wait_element_and_click(
            '//*[contains(@class, "icon-unlink")]')
        time.sleep(2)
        # Close
        browser_back_button()
        refresh_page()


def get_mail_id():
    """
    This function returns checked mail's id
    return str
    """
    checkboxes = driver.find_elements_by_xpath(
        '//*[contains(@class, "list-row js-list-row")]'
        '//*[contains(@type, "checkbox")]')
    for checkbox in checkboxes:
        if checkbox.is_selected():
            return checkbox.get_attribute('value')


def choice_first_mail(i=0, do_type=None):
    # Mail -> Choice first mail
    time.sleep(3)
    first_mail = driver.find_elements_by_xpath(
        '//*[@id = "list_holder" ]//*[contains(@id, "lead_")]')
    assert len(
        first_mail) > i, 'No mail with multiaction required available on ' \
                         'first page'
    first_mail[i].click()
    time.sleep(1)
    if do_type == 'readed':
        pass
    elif do_type:
        element = driver.find_elements_by_xpath(
            '//*[contains(@class, "{0}") or contains(@data-type, '
            '"{0}")]'.format(
                do_type))
        if element:
            pass
        else:
            first_mail[i].click()
            time.sleep(1)
            choice_first_mail(i + 1, do_type)


def to_customers_pipeline():
    # Customers -> pipeline settings
    wait_element_and_click(
        '//*[contains(@href, "/settings/pipeline/customers")]')


def pipeline_add_stage():
    # Customers -> add new stage
    wait_element_and_click(
        '//*[contains(@class, "svg-digital_pipeline--add_status-dims")]')
    time.sleep(2)
    wait_element_and_click(
        '//*[contains(@class, "pipeline_cell-head pipeline_cell-head-new")]')
    wait_element_and_send_text(
        '//*[contains(@name, "status_name")]', "100 days")


def delete_customers_period():
    """ Delete custom period in customers DP """
    xpath = '//*[@title = "100 days"]'
    if driver.find_elements_by_xpath(xpath):
        for _ in driver.find_elements_by_xpath(xpath):
            source = driver.find_element_by_xpath(xpath)
            dest_trash = driver.find_element_by_xpath(
                '//*[contains(@class, "icon icon-trash")]')
            ActionChains(driver).click_and_hold(source).move_to_element_and_click(
                dest_trash).release(on_element=dest_trash).perform()
            wait_element_and_click(
                '//*[contains(@class, "modal-body")]' +
                '//*[contains(@class, "modal-body__actions__save")]')
            time.sleep(1)
            wait_element_and_click(
                '//*[contains(@class, "list__top__actions")]' +
                '//*[contains(text(), "Save")]')
            time.sleep(2)
        assert len(driver.find_elements_by_xpath(
            '//*[@title = "100 days"]')) == 0
    else:
        raise MyException("Can't find custom period. Check xpath")


def auto_action():
    wait_element_and_click(
        dp_cell_xpath(2, 2))


def dp_cell_xpath(row: int, column: int):
    """ This function return dp cell xpath
    Parameters:
    :row - number of cell row
    :column - numer of cell column
    :customer - return specifically cell xpath for customers DP
    """
    cell_xpath = ('//*[contains(@class, "digital-pipeline__statuses-ro")]'
                  '[{0}]/div[{1}]'.format(row, column))
    return cell_xpath


def add_automatic_actions_todo(empty=False):
    """ Create automatic action "to-do" in DP
    Parameters:
    :empty - create to-do action without filling fields if True
    """
    # Cell click
    wait_element_and_click(dp_cell_xpath(2, 1))
    time.sleep(1)
    # Add to-do
    wait_element_and_click(
        '//button[@data-action="create_task"]')
    if not empty:
        wait_element_and_click(
            '//*[contains(@class, "digital-pipeline__delay-title-container")]')
        wait_element_and_click(
            '//*[contains(@data-option, "When a chat message is received")]')
        wait_element_and_click(
            '//*[contains(@class, "deadline_select__caption")]')
        wait_element_and_send_text('//*[contains(@class, "js-deadline-'
                                   'input js-control-allow-numeric '
                                   'text-input") and contains(@name, '
                                   '"deadline-days")]', randint(1, 365))
        wait_element_and_send_text('//*[contains(@class, "js-deadline-'
                                   'input js-control-allow-numeric '
                                   'text-input") and contains(@name, '
                                   '"deadline-hours")]', randint(1, 24))
        wait_element_and_send_text('//*[contains(@class, "js-deadline-'
                                   'input js-control-allow-numeric '
                                   'text-input") and contains(@name, '
                                   '"deadline-minutes")]', randint(1, 60))
        wait_element_and_click('//*[contains(@class, "button-input-inner__'
                               'text") and contains(text(), "OK")]')
        wait_element_and_click(
            '//*[contains(@class, "control--select--button")]')
        wait_element_and_click('//*[contains(@data-value, "46")]')
        todo = driver.find_elements_by_xpath(
            '//*[contains(@class, "control--select--button")]')
        todo[2].click()
        wait_element_and_click('//*[contains(@title, "Meeting")]')
        wait_element_and_send_text(
            '//*[contains(@class, "text-input text-input-textarea")' +
            ' and @placeholder = "Add comment"]',
            random_data())
    wait_element_and_click('//*[contains(@class, "js-trigger-save")]')
    time.sleep(1)


def add_automatic_actions_lead():
    """ Customers -> Add automatic actions -> Lead """
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(1, 2))
    # Select "Create a lead"
    wait_element_and_click('//*[contains(@class, "button-add")]' +
                           '//*[text() = "Create a lead"]')
    # Execute action
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__delay-title-container")]')
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__edit-item-title") ' +
        'and text()="When a call is received"]')
    # Make random choice in "Create lead with:" tab
    wait_element_and_click(
        '//*[contains(@class, "checkboxes_dropdown__title_wrapper")]')
    time.sleep(0.5)
    create_lead_with_var = driver.find_elements_by_xpath(
        '//*[contains(@class, "control-checkbox checkboxes_dropdown__label")]')
    ActionChains(driver). \
        move_to_element(choice(create_lead_with_var)). \
        click(). \
        send_keys(Keys.ESCAPE). \
        perform()
    # Set lead's creator as responsible user
    wait_element_and_click(
        '//*[contains(@class, "task-edit__body__form__element")]' +
        '//*[contains( @data-before, "For")]')
    wait_element_and_click(
        '//*[contains(@class, "control--select--list--item") ' +
        'and @data-value="creator"]')
    # Change pipeline stage
    wait_element_and_click(
        '//*[contains(@class, "pipeline-select-wrapper ' +
        'pipeline-select-wrapper_plain folded  js-control-pipeline-select")]')
    pipelines = ['Первичный контакт', 'Переговоры', 'Принимают решение',
                 'Согласование договора', 'Успешно реализовано']
    elem = driver.find_element_by_xpath(
        '//*[contains(@class, "pipeline-select__item-text") ' +
        'and text()="{}"]'.format(choice(pipelines)))
    wait_element_and_click(webelement=elem)
    # Done click
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def add_automatic_actions_customer():
    # Customers -> Add automatic actions -> Customer
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(2, 2))
    # Select "Create customer"
    wait_element_and_click('//*[contains(@class, "button-add")]' +
                           '//*[text() = "Create customer"]')
    # execute actiom
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__delay-title-container")]')
    execute_data_names = ['mail_in',
                          'call_in',
                          'chat',
                          'lead_responsible_changed', ]
    wait_element_and_click(
        '//*[contains(@data-name, "{}")]'.format(choice(execute_data_names)))
    # name of a customer
    wait_element_and_click(
        '//*[contains(@class, "control--select--button-inner") ' +
        'and text()="Automatically generate"]')
    names_of_customers = ['lead', 'contact', 'company']
    wait_element_and_click(
        '//*[contains(@class, "control--select--list--item    ") ' +
        'and @data-value="{}"]'.format(choice(names_of_customers)))
    # periodicity of purchase
    wait_element_and_click(
        '//*[contains(@class, "control--select--button") ' +
        'and @data-value = "1"]')
    periodicity_of_purchase = [1, 7, 30, 90, 365]
    wait_element_and_click(
        '//*[contains(@class, "control--select--list--item") ' +
        'and @data-value="{}"]'.format(choice(periodicity_of_purchase)))
    # change responsible user
    wait_element_and_click(
        '//*[contains(@class, "control--select--button") ' +
        'and @data-value = "current"]')
    responsible_users = ['Current responsible user',
                         "Lead's creator",
                         "Am Am Crm",
                         "Frau Amo",
                         "Leo",
                         "Mister Amo", ]
    wait_element_and_click(
        '//*[contains(@title, "{}")]'.format(choice(responsible_users)))
    # соответствие полей (4 из 6)
    # Add 3 fields
    for _ in range(3):
        wait_element_and_click('//*[text() = "More"]')
        time.sleep(0.1)
    # Search buttons in "Lead field" column
    lead_fields = driver.find_elements_by_xpath(
        '//*[contains(@class, "control--select--button  ")]' +
        '//*[contains(text(),"Lead field")]')
    # Search buttons in "Customer field" column
    customer_fields = driver.find_elements_by_xpath(
        '//*[contains(@class, "control--select--button  ")]' +
        '//*[contains(text(),"Customer field")]')
    for lead, customer in zip(lead_fields, customer_fields):
        wait_element_and_click(webelement=lead)
        wait_element_and_click(webelement=customer)
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def add_automatic_actions_email(customers=False):
    # Customers -> Add automatic actions -> Email
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(1, 3))
    # Send an email
    wait_element_and_click('//*[contains(@class, "button-add")]' +
                           '//*[text() = "Send an email"]')
    time.sleep(0.5)
    # Add condition
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__edit-process-container")]'
        '//*[contains(@class, "digital-pipeline__add-new-condition")]')
    if customers:
        wait_element_and_click('//*[@data-name = "Expected purchase amount"]')
        time.sleep(0.5)
        sales_input = driver.find_elements_by_xpath(
            '//*[contains(@class, "digital-pipeline__edit-process-container")]'
            '//*[contains(@class, "digital_pipeline__condition_control_pric")]'
            '/input[1]')
    else:
        wait_element_and_click('//*[@data-name = "Sale"]')
        time.sleep(0.5)
        sales_input = driver.find_elements_by_xpath(
            '//*[contains(@class, "js-control-pretty-price ' +
            'js-form-changes-skip digital_pipeline__condition_input ")]')
    for sale in sales_input:
        sale.send_keys(randint(0, 10000))
    # execute action
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__delay-title-container")]')
    wait_element_and_send_text(
        '//*[contains(@class, "date_field js-tasks-date-date-input")]',
        '{0}.{1}.{2}'.format(randint(1, 30), randint(1, 12),
                             randint(2018, 2025)))
    wait_element_and_send_text(
        '//*[contains(@class, "text-input control--suggest--input")]',
        '{0}:{1}'.format(randint(0, 24), randint(0, 60)))
    wait_element_and_click(
        '//*[text() = "Exact time"]')
    time.sleep(7)
    # Select the e-mail template
    wait_element_and_click(
        '//*[contains(@class, "control--select--button-inner") ' +
        'and text() = "Select the e-mail template"]')
    wait_element_and_click(
        '//*[@title ="ttt444"]')
    # Sender
    wait_element_and_click(
        '//*[contains(@class, "control--select--button") ' +
        'and @data-value="responsible"]')
    sender = driver.find_element_by_xpath(
        '//*[contains(@title, "Corporate mailbox")]')
    ActionChains(driver).move_to_element(sender).click().perform()
    # Mailbox
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "control--select--button-inner") ' +
        'and text()="E-mail"]')
    wait_element_and_click(
        '//*[contains(@title, "aivashneva.amocrm@mail.ru")]')
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def add_automatic_actions_salesbot():
    # Customers -> Add automatic actions -> Salesbot
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(1, 4))
    # Click Salesbot
    wait_element_and_click('//*[contains(@class, "button-add")]' +
                           '//*[text() = "Salesbot"]')
    # execute action
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__delay-title-container")]')
    execute_data_names = ['mail_in', 'call_in', 'chat',
                          'responsible_changed']
    wait_element_and_click(
        '//*[contains(@data-name, "{}")]'.format(choice(execute_data_names)))
    # Active days ->  Choose two days
    wait_element_and_click('//*[starts-with(span, "Active")]')
    # Select three different events.
    for day in sample(['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', ], 2):
        wait_element_and_click('//*[@name = "{}"]'.format(day))
        time.sleep(0.5)
    # click OK button
    wait_element_and_click(
        '//*[contains(@class, "js-trigger-save__' +
        'working-hours button-input_blue")]')
    # Leave the messages unread checkbox click
    wait_element_and_click(
        '//*[contains(@class, "unread-settings__toggler")]' +
        '//div[@class = "switcher_wrapper"]')
    # Choose bot
    wait_element_and_click(
        '//*[contains(@class, "control--select--button")]')
    wait_element_and_click(
        '//*[contains(@class, "control--select--list--item-inner") '
        'and contains(@title, "Salesbot")]')
    # Manege bot settings

    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def add_automatic_actions_data_to_analytics():
    # Customers -> Add automatic actions -> Add data to analytics
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(2, 3))
    wait_element_and_click('//*[contains(@class, "button-add")]' +
                           '//*[text() = "Add"]')
    # execute action
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__delay-title-container")]')
    execute_data_names = ['mail_in', 'call_in', 'chat',
                          'lead_responsible_changed']
    wait_element_and_click(
        '//*[contains(@data-name, "{}")]'.format(choice(execute_data_names)))
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def add_automatic_actions_hook():
    # Customers -> Add automatic actions -> Webhook
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(1, 5))
    # Send a webhook
    wait_element_and_click('//*[contains(@class, "button-add")]' +
                           '//*[text() = "Send a webhook"]')
    # execute action
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__delay-title-container")]')
    execute_data_names = ['mail_in', 'call_in', 'chat',
                          '_responsible_changed']
    wait_element_and_click(
        '//*[contains(@data-name, "{}")]'.format(choice(execute_data_names)))
    # URL
    wait_element_and_send_text(
        '//*[contains(@class, "digital-pipelines__webhooks form-group__control text-input")]',
        'http://stagetestform.jimdo.com')
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def add_automatic_actions_change_lead_stage():
    # Customers -> Add automatic actions ->  Change lead stage
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(3, 3))
    wait_element_and_click('//*[contains(@class, "button-add")]' +
                           '//*[text() = "Change lead stage"]')
    # execute action
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__delay-title-container")]')
    execute_data_names = ['mail_in', 'call_in', 'chat',
                          'lead_responsible_changed']
    wait_element_and_click(
        '//*[contains(@data-name, "{}")]'.format(choice(execute_data_names)))
    # Pipeline
    wait_element_and_click(
        '//*[contains(@class, "pipeline-select-wrapper ' +
        'pipeline-select-wrapper_plain folded  js-control-pipeline-select ")]')
    time.sleep(0.5)
    pipelines = ['Первичный контакт', 'Переговоры', 'Принимают решение',
                 'Согласование договора', 'Успешно реализовано']
    pipeline = driver.find_element_by_xpath(
        '//*[contains(@class, "pipeline-select__item-text") ' +
        'and text()="{}"]'.format(
            choice(pipelines)))
    ActionChains(driver).move_to_element(pipeline).click().perform()
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def add_automatic_actions_tags():
    # Customers -> Add automatic actions -> Tags
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(2, 4))
    wait_element_and_click('//*[contains(@class, "button-add")]' +
                           '//*[text() = "Edit tags"]')
    # execute action
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__delay-title-container")]')
    execute_data_names = ['mail_in', 'call_in', 'chat',
                          'lead_responsible_changed']
    wait_element_and_click(
        '//*[contains(@data-name, "{}")]'.format(choice(execute_data_names)))
    # remove tags
    wait_element_and_click(
        '//*[contains(@class, "control--select--button-inner") ' +
        'and text()="Add tags"]')
    wait_element_and_click('//*[@title = "Remove tags"]')
    # Chosse tags from list
    wait_element_and_click('//*[contains(@data-id, "tag")]')
    for _ in range(2):
        wait_element_and_click(
            '//*[contains(@class, "fast-tags-suggest")]' +
            '//*[contains(@class, "tag")]')
    # Click aside
    wait_element_and_click(
        '//*[contains(@class, "digital_pipeline__action-conditions_title")]')
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def add_automatic_actions_change_responsible():
    """
    This functions add dp autoaction Change responsible user
    """
    # Customers -> Add automatic actions -> Tags
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(3, 4))
    wait_element_and_click('//*[@data-action="change_responsible"]')
    # Execute action
    wait_element_and_click('//*[contains(@class, "digital-pipeline__'
                           'delay-title-container")]')
    actions = driver.find_elements_by_xpath('//*[contains(@class, '
                                            '"digital-pipeline__edit-item-title")]')
    wait_element_and_click(webelement=choice(actions))
    try:
        time.sleep(1)
        if driver.find_element_by_xpath('//*[contains(@class, "digital-pipelines__edit-url")]'):
            wait_element_and_send_text('//*[contains(@class, "digital-pipelines__edit-url")]', "http://www.amocrm.ru")
            wait_element_and_click(
                '//*[contains(@class, "digital-pipeline__edit-event-bubble_site-edit")]//*[contains(@class, "button-input-inner__text") and contains(text(), "Done")]')
    except:
        pass
    # Choose user
    wait_element_and_click('//*[contains(@class, "control--select--button")]')
    users = driver.find_elements_by_xpath('//*[contains(@class, "control'
                                          '--select--list--item-inner")]')
    wait_element_and_click(webelement=choice(users))
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(3)


def add_automatic_actions_change_field():
    """
    This function add dp autoaction Change field
    """
    driver.execute_script("window.scrollTo(0, 0);")
    # Cell click
    wait_element_and_click(dp_cell_xpath(3, 5))
    wait_element_and_click('//*[@data-action="change_field_value"]')
    # Execute action
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__edit-bubble")]//*[contains(@class, "digital-pipeline__add-new-condition")]')
    wait_element_and_click('//*[contains(@class, "digital-pipeline__condition-select-item")]//*[text()="Tags"]')
    wait_element_and_click('//*[contains(@class, "digital-pipeline__condition_tags-container")]')
    time.sleep(0.5)
    tags = driver.find_elements_by_xpath('//*[contains(@class, "js-multisuggest-item")]/*[contains(@class, "tag")]')
    wait_element_and_click(webelement=choice(tags))
    # Missclick
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__edit-bubble")]//*[contains(@class, "digital_pipeline__action-conditions_title")]')
    # Check execute
    wait_element_and_click('//*[contains(@class, "digital-pipeline__edit-delay-new-process")]')
    time.sleep(0.5)
    executes = driver.find_elements_by_xpath('//*[contains(@class, "digital-pipeline__edit-item_choose-delay")]')
    wait_element_and_click(webelement=choice(executes))
    # Website
    try:
        time.sleep(1)
        if driver.find_element_by_xpath('//*[contains(@class, "digital-pipelines__edit-url")]'):
            wait_element_and_send_text('//*[contains(@class, "digital-pipelines__edit-url")]', "http://www.amocrm.ru")
            wait_element_and_click(
                '//*[contains(@class, "digital-pipeline__edit-event-bubble_site-edit")]//*[contains(@class, "button-input-inner__text") and contains(text(), "Done")]')
    except:
        pass
    # Add field
    wait_element_and_click('//*[text()="Field is not selected"]')
    time.sleep(0.2)
    wait_element_and_click('//*[@data-name="Short text"]')
    wait_element_and_send_text('//*[contains(@class, "digital-pipeline__condition_input-text")]',
                               random_data())
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(3)


def open_forms():
    # Unsorted -> click on forms
    wait_element_and_click('//*[contains(@class, "dp-source__caption")]')
    wait_element_and_click('//*[contains(@id, "reset_cf_settings")]')


def sort_leads_in_pipeline():
    # Leads -> pipeline -> tree dots -> sorting by
    time.sleep(1)
    path_to_shit = ['//*[contains(@data-sort-by, "last_event")]',
                    '//*[contains(@data-sort-by, "date_create")]',
                    '//*[contains(@data-sort-by, "name")]',
                    '//*[contains(@data-sort-by, "price")]',
                    ]
    for path_ in path_to_shit:
        wait_element_and_click(
            '//*[contains(@class, "button-input  button-input-with-menu")]')
        time.sleep(1)
        wait_element_and_click(path_)
        time.sleep(0.5)


def save_dp():
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__save-button")]')
    time.sleep(4)


def add_mailchimp():
    """ Customers -> DP Settings -> New Action -> Mailchimp """
    main_tab = driver.current_window_handle
    wait_element_and_click(
        '//*[@data-handler-code = "mailchimp"]' +
        '//*[contains(@class, "button-add")]')
    time.sleep(2)
    driver.switch_to.window(main_tab)
    time.sleep(0.5)


def add_facebook():
    """ Customers -> DP Settings -> New Action -> Facebook """
    main_tab = driver.current_window_handle
    wait_element_and_click(
        '//*[@data-handler-code = "facebook"]' +
        '//*[contains(@class, "button-add")]')
    time.sleep(2)
    driver.switch_to.window(main_tab)
    time.sleep(0.5)


def add_adwords():
    """ Customers -> DP Settings -> New Action -> Adwords """
    main_tab = driver.current_window_handle
    wait_element_and_click(
        '//*[@data-handler-code = "adwords"]' +
        '//*[contains(@class, "button-add")]')
    time.sleep(2)
    driver.switch_to.window(main_tab)
    time.sleep(0.5)


def choice_free_user_in_chat():
    mouse_to_element(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div['
        '1]/div')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "tips-item js-tips-item js-switcher-chat")]')
    wait_element_and_click('//*[contains(@id, "feed_compose_user")]')
    wait_element_and_send_text(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        random_data() + '@example.com')


def write_chat_message():
    wait_element_and_click(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]')
    wait_element_and_send_text_elem(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        random_data())
    wait_element_and_send(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        Keys.ENTER)
    wait_element_and_send(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        random_data())
    wait_element_and_send(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        Keys.ENTER)
    wait_element_and_send(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        Keys.ENTER)
    wait_element_and_send(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input   js-note-submit ' +
        'feed-note__button")]')


def write_chat_message_with_jpg():
    wait_element_and_click(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]')
    wait_element_and_send_text_elem(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        random_data())
    wait_element_and_send(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        Keys.ENTER)
    wait_element_and_send(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        random_data())
    wait_element_and_send(
        '//*[@id="card_holder"]/div[3]/div/div[2]/div[2]/div/div[1]/div[2]',
        Keys.ENTER)
    wait_element_and_send('//*[contains(@id, "note-edit-attach-filenew")]',
                          "/home/autotester/test_data/1.jpg")


def feed_compose_user():
    wait_element_and_click('//*[contains(@id, "feed_compose_user")]')


def feed_compose_show_all():
    wait_element_and_click('//*[contains(@id, "show_all")]')


def choice_user_in_chat():
    users = ["Frau Amo", "Am Am Crm", "Mister Amo", "Senior Amo", "PanAmo"]
    wait_element_and_send_text(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        choice(users))


def feed_write_to_all():
    wait_element_and_click(
        '//*[contains(@class, "users-select__head-allgroup")]')


def write_chat_message_with_txt():
    # Note with txt file
    wait_element_and_send_text_elem(
        '//*[contains(@data-hint, "Type here")]',
        random_data())
    wait_element_and_send('//*[contains(@id, "note-edit-attach-filenew")]',
                          "/home/autotester/test_data/example.txt")


def download_note_txt():
    # Note -> Download txt
    wait_element_and_click('//*[contains(@href, "_example.txt")]')


def choice_reply_user():
    users = driver.find_elements_by_xpath(
        '//*[contains(@class, "feed-note__amojo-user ' +
        'js-amojo-recipient js-amojo-reply")]')
    users[2].click()


def open_participants():
    wait_element_and_click('//*[contains(@class, "js-toggle")]')


def delete_user_from_chat():
    wait_element_and_click(
        '//*[contains(@class, "subscriber__remove js-subscriber-remove")]')


def open_notify_center():
    """ Function, than open notification center """
    wait_element_and_click(
        '//*[contains(@class, "nav__notifications__icon icon-notifications")]')


def search_rand_user_in_notify_center():
    """ Take random user form list and search it in notification center """
    users_list = ["Frau Amo", "Am Am Crm", "Mister Amo", "Senior Amo"]
    wait_element_and_send_text('//*[contains(@id, "search-input")]',
                               choice(users_list))
    time.sleep(1)


def select_user_in_notify_center():
    """ Select first user in NC after search """
    wait_element_and_click(
        '//*[contains(@id, "inbox-container")]' +
        '//*[contains(@class, "notification-inner__title_message_title")]')
    time.sleep(0.5)


def write_msg_to_user_in_notify_center():
    """ Select first user in notification center, and
    write to it some random message
    """
    wait_element_and_send_text(
        '//*[contains(@class, "feed-compose__message-area custom-scroll")]',
        random_data())
    wait_element_and_send(
        '//*[contains(@class, "feed-compose__message-area custom-scroll")]',
        Keys.ENTER)
    wait_element_and_send(
        '//*[contains(@class, "feed-compose__message-area custom-scroll")]',
        random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input   ' +
        'js-note-submit feed-note__button")]')
    time.sleep(0.5)


def write_msg_to_user_in_notify_center_with_file(attached_file):
    """ Write message to user in notification center with image
    for text file as attach
    """
    wait_element_and_click('//*[contains(@class, "feed-compose__inner")]')
    wait_element_and_send_text(
        '//*[contains(@class, "feed-compose__message-area custom-scroll")]',
        random_data())
    time.sleep(0.5)
    if attached_file == "txt":
        wait_element_and_send('//*[contains(@type, "file")]',
                              "/home/autotester/test_data/example.txt")
    elif attached_file == "jpg":
        wait_element_and_send('//*[contains(@type, "file")]',
                              "/home/autotester/test_data/1.jpg")
    time.sleep(0.5)


def create_group_chats(test_name):
    """ Create a new group chats in amojo:
    name of chat, add few users and group
    """
    wait_element_and_click('//*[contains(@class, "button-input  button-input-with-menu")]')
    wait_element_and_click('//*[contains(@class, "button-input__context-menu__item__text")]')
    # Add few users
    wait_element_and_click(
        '//*[contains(@class, "multisuggest__suggest-item js-multisuggest-item true")][text()="Mister Amo"]')
    wait_element_and_click(
        '//*[contains(@class, "multisuggest__suggest-item js-multisuggest-item true")][text()="Senior Amo"]')
    # Add Group
    wait_element_and_click(
        '//*[contains(@class, "users-select__head-allgroup")]')
    # Name of chat
    chat_name = random_data()
    save_data_to_mongo(test_name, {'amojo_chat': 'name', 'value': chat_name})
    wait_element_and_click(
        '//*[contains(@class, "chat-inbox__header__name-group_chat' +
        ' chat-inbox__header__name-chat")]')
    wait_element_and_send_text(
        '//*[contains(@class, "text-input group-chat__title ' +
        'group-chat__title-create  expanded")]',
        chat_name)
    # Save
    wait_element_and_click(
        '//*[contains(@class, "button-input    ' +
        'js-chat-submit feed-note__button")]')


def write_group_chat_message(with_jpg=False):
    """ Write message in group chat """
    # Bug: unable to find element with placeholder "Type here". Maybe it's not translated.
    wait_element_and_send('//*[contains(@data-hint, "Type here")]',
                          (random_data(), Keys.ENTER, random_data(), Keys.ENTER, random_data()))

    if with_jpg:
        wait_element_and_send(
            '//*[contains(@class, "amojo")]//*[contains(@type, "file")]',
            "/home/autotester/test_data/1.jpg")
    else:
        wait_element_and_click(
            '//*[contains(@class, "button-input   ' +
            'js-note-submit feed-note__button")]')


def choice_amojo_user_to_write():
    """ In amojo choice random user, in message box, to write """
    wait_element_and_click(
        '//*[contains(@class, "feed-compose-user js-feed-users")]')
    users_list = ["Frau Amo", "Am Am Crm", "Mister Amo", "Senior Amo"]
    wait_element_and_send(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        choice(users_list))
    wait_element_and_send(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        Keys.ENTER)


def all_mails():
    wait_element_and_click('//*[contains(@id, "list_all_checker")]')


def to_list_for_search_test():
    """ Move to list that created for search test """
    url = driver.current_url
    domain = url.split('/')[2]
    driver.get(f'https://{domain}/catalogs/2665')


def save_data_to_mongo(collection_name, dataset):
    """ Save data to MongoDB.
    Dataset is simple json. Example of valid dataset:
    {"test_name": "test_amojo", "function_name": "create_chat"}
    """
    client = MongoClient('mongo', 27017)
    db = client['selenium_tests']
    db[collection_name].insert_one(dataset)
    client.close()


def drop_collection_from_mongo(collection_name):
    """ Drop data from MongoDB. """
    client = MongoClient('mongo', 27017)
    db = client['selenium_tests']
    db[collection_name].drop()
    client.close()


def find_data_in_mongo(collection_name, data=None):
    """ Find data in MongoDB and return result
    if it not empty
    """
    client = MongoClient('mongo', 27017)
    db = client['selenium_tests']
    if data:
        result = db[collection_name].find_one(data)
    else:
        result = db[collection_name].find_one()
    client.close()
    if result:
        return result
    else:
        return None


def search_element(test_name):
    """ Search element in list and check if its present in results """
    data = find_data_in_mongo(test_name)
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]', data['value'])
    time.sleep(3)
    check_text_of_element('(//*[contains(text(), "{}")])[last()]'.format(data['value']),
                          data['value'])


def check_text_of_element(xpath, value):
    """ Check if in given xpath present given value """
    time.sleep(2)
    try:
        el = driver.find_element_by_xpath(xpath)
        assert el.text == str(value)
    except exceptions.NoSuchElementException:
        wait_element_and_click('(//*[contains(@class, "pagination-pages")]//a)[last()]')
        time.sleep(2)
        el = driver.find_element_by_xpath(xpath)
        assert el.text == str(value)


def search_clear_button():
    """ Clear search string """
    mouse_to_element('//*[contains(@placeholder, "Search and filter")]')
    time.sleep(1)
    wait_element_and_click('//*[@id="search_clear_button"]')


def click_on_search_and_filter():
    wait_element_and_click('//*[contains(@placeholder, "Search and filter")]')


def search_filter_to_today():
    wait_element_and_click(
        '(//*[contains(@class, "date_filter__period custom_select__selected")])[1]')
    wait_element_and_click(
        '//*[@data-period="today" or @data-period="1"]')


def post_data_to_search_filters(test_name, xpath, dest_xpath):
    """ test_name -- Name of test,
    xpath -- Xpath of element witch value you need,
    dest_xpath -- xpath of element to what you want post it
    """
    click_on_search_and_filter()
    element_value = find_data_in_mongo(test_name, {"xpath": xpath})
    wait_element_and_click(dest_xpath)
    wait_element_and_send_text(dest_xpath, element_value['value'])
    time.sleep(0.5)


def save_search_filters():
    wait_element_and_click(
        '//*[contains(@class, "filter__params_manage__apply")]')
    time.sleep(1)


def check_search_in_lists():
    # SKU
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[@class="field template-text "]//*[@placeholder="SKU"]',
                                '//*[contains(@placeholder, "SKU")]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Quantity
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "Quantity")]',
                                '//*[contains(@placeholder, "Quantity")]')
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "Quantity")]',
                                '//*[contains(@placeholder, "Quantity")]/../input[2]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Price
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "Price")]',
                                '//*[contains(@placeholder, "Price")]')
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "Price")]',
                                '//*[contains(@placeholder, "Price")]/../input[2]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Text
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Short text" or @placeholder="text"]',
                                '//*[contains(@placeholder, "text")]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Numeric
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "numeric") or contains(@placeholder, "Numeric")]',
                                '//*[contains(@placeholder, "numeric")]')
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "numeric") or contains(@placeholder, "Numeric")]',
                                '//*[contains(@placeholder, "numeric")]/../input[2]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Checkbox
    click_on_search_and_filter()
    wait_element_and_click('//*[@id="filter_fields"]/div[7]/div/div/button')
    wait_element_and_click('//*[@id="filter_fields"]/div[7]/div/div/ul/li[3]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Select
    click_on_search_and_filter()
    wait_element_and_click('//*[@id="filter_fields"]/div[8]/div/div/button')
    wait_element_and_click('//*[@id="filter_fields"]/div[8]/div/div/ul/li[4]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Multiselect
    click_on_search_and_filter()
    wait_element_and_click(
        '//*[contains(@class, "checkboxes_dropdown__title_wrapper ")]')
    wait_element_and_click(
        '(//label[contains(@class, "control-checkbox checkboxes_dropdown__label control-checkbox_small")])[3]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Date
    click_on_search_and_filter()
    wait_element_and_send('//*[@id="filter_fields"]/div[10]/div/span/input[3]',
                          '20042019')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # URL
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Url" or @placeholder="url"]',
                                '//*[contains(@placeholder, "url")]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Textarea
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Long text" or @placehorlder="long text" or @placeholder="textarea"]',
                                '//*[contains(@placeholder, "textarea")]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Radiobutton
    click_on_search_and_filter()
    wait_element_and_click('//*[@id="filter_fields"]/div[13]/div/div/button')
    wait_element_and_click('//*[@id="filter_fields"]/div[13]/div/div/ul/li[4]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Short addr
    post_data_to_search_filters("test_search_created_element_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Short address" or @placeholder="short address"]',
                                '//*[contains(@placeholder, "short address")]')
    save_search_filters()
    data = find_data_in_mongo("test_search_created_element_in_list")
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()


def check_combined_search_in_list():
    # SKU
    post_data_to_search_filters("test_combined_search_in_list",
                                '//*[@class="field template-text "]//*[@placeholder="SKU"]',
                                '//*[contains(@placeholder, "SKU")]')
    # Quantity
    post_data_to_search_filters("test_combined_search_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "Quantity")]',
                                '//*[contains(@placeholder, "Quantity")]')
    # Price
    post_data_to_search_filters("test_combined_search_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "Price")]',
                                '//*[contains(@placeholder, "Price")]')
    # Text
    post_data_to_search_filters("test_combined_search_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Short text" or @placeholder="text"]',
                                '//*[contains(@placeholder, "text")]')
    # Numeric
    post_data_to_search_filters("test_combined_search_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[contains(@placeholder, "numeric") or contains(@placeholder, "Numeric")]',
                                '//*[contains(@placeholder, "numeric")]')
    # Checkbox
    wait_element_and_click('//*[@id="filter_fields"]/div[7]/div/div/button')
    wait_element_and_click('//*[@id="filter_fields"]/div[7]/div/div/ul/li[3]')
    # Select
    wait_element_and_click('//*[@id="filter_fields"]/div[8]/div/div/button')
    wait_element_and_click('//*[@id="filter_fields"]/div[8]/div/div/ul/li[4]')
    # Multiselect
    wait_element_and_click(
        '//*[@id="filter_fields"]/div[9]/div/div/div[2]/span[1]')
    wait_element_and_click(
        '//*[@id="filter_fields"]/div[9]/div/div/div[1]/div/div[4]/label')
    # Date
    wait_element_and_send('//*[@id="filter_fields"]/div[10]/div/span/input[3]',
                          make_date('20.04.2019'))
    # URL
    post_data_to_search_filters("test_combined_search_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Url" or @placeholder="url"]',
                                '//*[contains(@placeholder, "url")]')
    # Textarea
    post_data_to_search_filters("test_combined_search_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Long text" or @placehorlder="long text" or @placeholder="textarea"]',
                                '//*[contains(@placeholder, "textarea")]')
    # Radiobutton
    wait_element_and_click('//*[@id="filter_fields"]/div[13]/div/div/button')
    wait_element_and_click('//*[@id="filter_fields"]/div[13]/div/div/ul/li[4]')
    # Short addr
    post_data_to_search_filters("test_combined_search_in_list",
                                '//*[contains(@class, "modal-body modal-body-relative")]//*[@placeholder="Short address" or @placeholder="short address"]',
                                '//*[contains(@placeholder, "short address")]')
    save_search_filters()
    data = find_data_in_mongo("test_combined_search_in_list")
    check_text_of_element('//*[contains(text(), "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()


def check_search_presets():
    presets_path = ['//*[contains(@title, "Modified past 3 days")]',
                    '//*[contains(@title, "Created past 3 days")]',
                    ]
    for preset in presets_path:
        click_on_search_and_filter()
        wait_element_and_click(preset)
        time.sleep(0.5)
        search_clear_button()
        time.sleep(0.5)


def change_list_item(test_name):
    time.sleep(1)
    old_name = find_data_in_mongo(test_name)
    check_text_of_element(
        '//*[contains(@title, "{}")]'.format(old_name['value']),
        old_name['value'])
    # Change item name
    wait_element_and_click(
        '//*[contains(@title, "{}")]'.format(old_name['value']))
    new_name = random_data()
    save_data_to_mongo(test_name, {"get_name": "new_name", "value": new_name})
    wait_element_and_send_text(
        '//*[contains(@class, "modal-body modal-body-relative")]//*[@name="name"]', new_name)
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)
    # Check new name in result
    check_text_of_element('//*[contains(@title, "{}")]'.format(new_name),
                          new_name)


def search_changed_list_item(test_name):
    old_name = find_data_in_mongo(test_name)
    new_name = find_data_in_mongo(test_name, {"get_name": "new_name"})
    # Search by old name
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]', old_name['value'])
    # Throw assert if new name equal to old name
    el = driver.find_element_by_xpath(
        '//*[contains(@title, "{}")]'.format(new_name['value']))
    assert el.text != str(old_name['value'])
    search_clear_button()
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]', new_name['value'])
    # Throw assert if new name not equal to new name
    time.sleep(1)
    check_text_of_element(
        '//*[contains(@title, "{}")]'.format(new_name['value']),
        new_name['value'])


def search_new_amojo_chat(test_name):
    """ Search new amojo chat and open it """
    new_chat_name = find_data_in_mongo(test_name, {"amojo_chat": "name"})
    wait_element_and_send_text('//*[contains(@id, "search-input")]',
                               new_chat_name['value'])
    time.sleep(0.75)
    wait_element_and_click(
        '//*[contains(@class, "notification-inner__title_message")]')


def fill_group(test_name=False):
    wait_element_and_click('//*[contains(@title, "gr 1")]')
    # Short text, Numeric, Checkbox
    text_field = random_data()
    num_field = randint(100, 999)
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[5]/div[1]/div[2]/input', text_field)
    wait_element_and_send_text('//*[@id="edit_card"]/div/div[5]/div[2]/div[2]/input', num_field)
    wait_element_and_click(
        '//*[@id="edit_card"]/div/div[5]/div[3]/div[2]/label/div')
    # Select
    wait_element_and_click(
        '//*[@id="edit_card"]/div/div[5]/div[4]/div[2]/div/button/span')
    wait_element_and_click(
        '//*[@id="edit_card"]/div/div[5]/div[4]/div[2]/div/ul/li[3]')
    # Multi select
    wait_element_and_click('//*[@id="edit_card"]/div/div[5]/div[5]/div[2]/div')
    # Pick "22_contacts"
    wait_element_and_click('//*[@id="edit_card"]/div/div[5]/div[5]/div[2]/div/div[1]/div/div[3]')
    # Date
    date_field = '03.01.' + str(randint(2016, 2019))
    wait_element_and_send(
        '//*[@id="edit_card"]/div/div[5]/div[6]/div[2]/span/input',
        date_field)
    # URL
    url_field = 'http://' + random_data()
    textarea_field = random_data()
    shortaddr_field = random_data()
    addr_field = random_data()
    birthday_field = '03.01.' + str(randint(2016, 2019))
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[5]/div[7]/div[2]/div/input', url_field)
    # Long text
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[5]/div[8]/div[2]/div/textarea',
        textarea_field)
    # Radiobutton
    wait_element_and_click(
        '//*[@id="edit_card"]/div/div[5]/div[9]/div[2]/label[2]')
    # Short addr
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[5]/div[10]/div[2]/div/textarea',
        shortaddr_field)
    # Addr
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[5]/div[11]/div[2]/div/div[1]/input',
        addr_field)
    # Birthday
    wait_element_and_send(
        '//*[@id="edit_card"]/div/div[5]/div[12]/div[2]/span/input',
        birthday_field)

    # New fields
    taxid_field_name = random_data()
    taxid_field_itin = random_n_digits(10)
    taxid_field_iec = random_n_digits(10)
    legal_name_field = random_data()
    datetime_field = '03.01.' + str(randint(2016, 2019)) + ' 13:48'
    # Tax ID
    wait_element_and_send('//*[@id="edit_card"]/div/div[5]/div[13]/div/div[2]/div/div[1]//input', taxid_field_name)
    wait_element_and_send('//*[@id="edit_card"]/div/div[5]/div[13]/div/div[2]/div/div[2]//input', taxid_field_itin)
    wait_element_and_send('//*[@id="edit_card"]/div/div[5]/div[13]/div/div[2]/div/div[3]//input', taxid_field_iec)
    # Legal name
    wait_element_and_send('//*[@id="edit_card"]/div/div[5]/div[14]/div/div[2]/div/div/div/input', legal_name_field)
    # Datetime
    wait_element_and_click('//*[@id="edit_card"]/div/div[5]/div[15]/div[2]/span/input')
    wait_element_and_send('//*[@id="edit_card"]/div/div[5]/div[15]/div[2]/span/input', datetime_field)
    # Save
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(3)
    # Save all data to mongo
    if test_name:
        save_data_to_mongo(test_name,
                           {'xpath': 'text_xpath',
                            'value': text_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'num_xpath',
                            'value': num_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'date_xpath',
                            'value': date_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'url_xpath',
                            'value': url_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'textarea_xpath',
                            'value': textarea_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'shortaddr_xpath',
                            'value': shortaddr_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'addr_xpath',
                            'value': addr_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'birthday_xpath',
                            'value': birthday_field})


def quick_add_in_card():
    """ Use lead quick add in card holder """
    # select lead tab
    wait_element_and_click(
        '//*[contains(@class, "card-holder")]//*[@title = "Leads"]')
    # click on a quick add
    wait_element_and_click(
        '//*[contains(@class, "pipeline_leads__quick_add_button_inner")]')
    # Type lead name and save
    lead_name = random_data()
    wait_element_and_send_text('//*[@id="quick_add_lead_name"]', lead_name)
    wait_element_and_click('//*[@id="quick_add_form_btn"]')
    time.sleep(0.5)


def search_company_name(test_name):
    """ Search company and check if its present in results """
    company_name = find_data_in_mongo(
        test_name, {'company_name_xpath': '//*[@id="new_company_n"]'})
    data = find_data_in_mongo(test_name)
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]',
        company_name['value'])
    time.sleep(1)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])


def search_filter_change_pipeline():
    wait_element_and_click(
        '//*[@data-tmpl="statuses"]')
    wait_element_and_click('//*[contains(@title, "Первичный контакт")]')
    click_on_search_and_filter()  # For close active stages


def search_filter_change_next_purchase():
    wait_element_and_click(
        '//*[@data-before="Next purchase"]')
    wait_element_and_click('//*[contains(@title, "Next quarter")]')


def search_filter_change_user():
    wait_element_and_click(
        '//*[contains(@class, "multisuggest ' +
        'users_select-select_one  js-multisuggest js-can-add ")]')
    wait_element_and_send_text(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        "search")
    wait_element_and_send(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        Keys.ARROW_DOWN)
    wait_element_and_send(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        Keys.ENTER)
    wait_element_and_send(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        Keys.ESCAPE)


def search_filter_todos_to_today():
    wait_element_and_click('//*[contains(@data-before, "Tasks: ") or contains(@data-before, "To-dos:")]')
    wait_element_and_click(
        '//*[contains(@class, "control--select--list--item-inner")' +
        ' and text()="Due today"]')


def is_element_present(test_name):
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])


def check_search_filters(test_name, source_xpath, dest_xpath):
    post_data_to_search_filters(test_name, source_xpath, dest_xpath)
    # For date we used to push "Done" button before accept
    if source_xpath in ('date_xpath', 'birthday_xpath'):
        time.sleep(1)
        done_buttons = driver.find_elements_by_xpath(
            '(//*[contains(@type, "button") and contains(@class, ' +
            '"button-input date_filter__done-btn js-date-done")])[last()]')
        for done_button in done_buttons:
            if done_button.is_displayed():
                time.sleep(0.5)
                ActionChains(driver).move_to_element(
                    done_button).click().perform()
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()


def save_own_search_preset():
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@title, "Save")]')
    # Type name
    wait_element_and_send_text('//*[@id="filter_list"]/li[last()-1]' +
                               '//*[contains(@placeholder, "Enter name")]',
                               random_data())
    # Accept
    accpet_list = driver.find_elements_by_xpath(
        '//*[contains(@class, "icon icon-accept-green")]')
    wait_element_and_click(webelement=accpet_list[-1])


def check_contacts_search_presets():
    presets_path = ['//*[contains(@title, "Contacts without")]',
                    '//*[contains(@title, "Contacts with Overdue")]',
                    '//*[contains(@title, "No leads linked")]',
                    '//*[contains(@title, "Deleted")]',
                    ]
    for preset in presets_path:
        click_on_search_and_filter()
        wait_element_and_click(preset)
        time.sleep(1)
        search_clear_button()
        time.sleep(0.5)


def delete_contact():
    # Contact -> tree dots -> Delete contact / company
    wait_element_and_click(
        '//*[contains(@class, "card-fields__top-name-more")]')
    wait_element_and_click('//*[contains(@id, "card_delete")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(1)


def choice_deleted_search_preset():
    # Lists -> Contacts -> Search and filters -> Deleted
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@title, "Deleted")]')


def get_id_of_element_from_href(xpath):
    el = driver.find_element_by_xpath(xpath)
    href_el = el.get_attribute('href')
    id_elem = href_el.split('/')[-1]
    return id_elem


def restor_contact(test_name):
    data = find_data_in_mongo(test_name)
    element_id = get_id_of_element_from_href(
        '//*[contains(@title, "{}")]'.format(data['value']))
    wait_element_and_click('//*[contains(@value, "{}")]'.format(element_id))
    wait_element_and_click('//*[contains(@data-type, "restore")]')
    time.sleep(1)


def change_contact_name(test_name):
    new_name = random_data()
    wait_element_and_send('//*[@name="contact[FN]" or @id="person_n"]', Keys.CONTROL + Keys.BACKSPACE)
    wait_element_and_send_text('//*[@name="contact[N]" or @id="person_n"]', new_name)
    save_data_to_mongo(test_name, {"get_name": "new_name", "value": new_name})
    wait_element_and_click(
        '//*[contains(@id, "save_and_close_contacts_link")]')
    time.sleep(0.5)


def check_old_contact_is_not_present(test_name):
    """ Raise exception if element is found """
    old_name = find_data_in_mongo(test_name)
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]', old_name['value'])
    time.sleep(1)
    try:
        driver.find_element_by_xpath(
            '//*[contains(@title, "{}")]'.format(old_name['value']))
    except common.exceptions.NoSuchElementException:
        pass
    else:
        raise MyException("Element found")


def check_old_company_is_not_present(test_name):
    """ Raise exception if element is found """
    company_name = find_data_in_mongo(
        test_name, {'company_name_xpath': '//*[@id="new_company_n"]'})
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]',
        company_name['value'])
    time.sleep(1)
    try:
        driver.find_element_by_xpath(
            '//*[contains(@title, "{}")]'.format(company_name['value']))
    except common.exceptions.NoSuchElementException:
        pass
    else:
        raise MyException("Element found")


def check_new_contact_name(test_name):
    new_name = find_data_in_mongo(test_name, {"get_name": "new_name"})
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]', new_name['value'])
    time.sleep(0.5)
    check_text_of_element(
        '//*[contains(@title, "{}")]'.format(new_name['value']),
        new_name['value'])


def check_search(test_name, for_contact_company=True):
    # Text
    check_search_filters(test_name, 'text_xpath',
                         '//*[contains(@placeholder, "Short text")]')
    # Numeric
    check_search_filters(test_name, 'num_xpath',
                         '//*[contains(@placeholder, "Numeric")]')
    # Checkbox -> Yes
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@data-before, "Toggle switch")]')
    wait_element_and_click('//*[contains(@data-value, "Y")]')
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Select
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@data-before, "Select")]')
    wait_element_and_click('//*[contains(@title, "2")]')
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Multiselect
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@data-title-before, "Multiselect")]')
    wait_element_and_click('//*[contains(@title, "22")]')
    ActionChains(driver).send_keys(Keys.ESCAPE)
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Date
    check_search_filters(test_name, 'date_xpath',
                         '//*[@placeholder="Date"]')
    # URL
    check_search_filters(test_name, 'url_xpath',
                         '//*[contains(@placeholder, "Url")]')
    # Long text
    check_search_filters(test_name, 'textarea_xpath',
                         '//*[contains(@placeholder, "Long text")]')
    # Radiobutton
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@data-before, "Radiobutton")]')
    wait_element_and_click('//*[contains(@title, "222")]')
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Short address
    check_search_filters(test_name, 'shortaddr_xpath',
                         '//*[contains(@placeholder, "Short address")]')
    if for_contact_company:
        # Addr 1
        check_search_filters(test_name, 'addr_xpath',
                             '//*[contains(@placeholder, "Address line 1")]')
        # Birthday
        click_on_search_and_filter()
        wait_element_and_click('//*[contains(@placeholder, "Birthday")]')
        check_search_filters(test_name, 'birthday_xpath',
                             '//*[contains(@placeholder, "Birthday")]')
    # Tag
    click_on_search_and_filter()
    tag_name = find_data_in_mongo(test_name,
                                  {'xpath': '//*[@id="0"]/ul/li/input'})
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input',
        tag_name['value'])
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ARROW_UP)
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ENTER)
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ESCAPE)
    wait_element_and_click(
        '//*[contains(@title, "{}")]'.format(tag_name['value']))
    time.sleep(0.5)
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Manage tags
    time.sleep(1)
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@class, "js-tags-lib__manage")]')
    wait_element_and_send('//*[contains(@placeholder, "Find or add a tag")]',
                          tag_name['value'])
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, ' +
        '"js-tags-lib__item-delete tags-lib__item-delete")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    wait_element_and_click(
        '//*[contains(@class, "switcher_wrapper controls-switcher-blue")]')
    wait_element_and_click(
        '//*[contains(@class, "switcher_wrapper controls-switcher-blue")]')
    wait_element_and_click('//*[contains(@class, "icon icon-modal-close")]')


def check_combined_search(test_name, for_contact_company=True, leads=False):
    # Text
    post_data_to_search_filters(test_name, 'text_xpath',
                                '//*[contains(@placeholder, "text") or contains(@placeholder, "Text")]')
    # Numeric
    post_data_to_search_filters(test_name, 'num_xpath',
                                '//*[contains(@placeholder, "numeric") or contains(@placeholder, "Numeric")]')
    # Checkbox -> Yes
    wait_element_and_click('//*[contains(@data-before, "Toggle switch")]')
    wait_element_and_click('//*[contains(@data-value, "Y")]')
    save_search_filters()
    # Select
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@data-before, "select") or contains(@data-before, "Select")]')
    wait_element_and_click(
        '//*[contains(@title, "2_leads") or contains(@title, "2_contacts") or contains(@title, "2_customers") or contains(@title, "2_companies")]')
    # Multiselect
    wait_element_and_click(
        '//*[contains(@data-title-before, "multiselect") or contains(@data-title-before, "Multiselect")]')
    wait_element_and_click(
        '//*[contains(@title, "22_leads") or contains(@title, "22_contacts") or contains(@title, "22_customers") or contains(@title, "22_companies")]')
    wait_element_and_click('//*[contains(@class, "filter-search__left")]')
    # URL
    post_data_to_search_filters(test_name, 'url_xpath',
                                '//*[contains(@placeholder, "url") or contains(@placeholder, "Url")]')
    # Long text
    post_data_to_search_filters(test_name, 'textarea_xpath',
                                '//*[contains(@placeholder, "long text") or contains(@placeholder, "Long text")]')
    # Date
    post_data_to_search_filters(test_name, 'date_xpath',
                                '//*[@placeholder="Date"]')
    save_search_filters()
    # Radiobutton
    click_on_search_and_filter()
    wait_element_and_click('//*[contains(@data-before, "radiobutton") or contains(@data-before, "Radiobutton")]')
    wait_element_and_click(
        '//*[contains(@title, "222_leads") or contains(@title, "222_contacts") or contains(@title, "222_customers") or contains(@title, "222_companies")]')
    # Short address
    post_data_to_search_filters(test_name, 'shortaddr_xpath',
                                '//*[contains(@placeholder, "short address") or contains(@placeholder, "Short address")]')
    if for_contact_company:
        if leads:
            pass
        # Addr 1
        else:
            post_data_to_search_filters(
                test_name,
                'addr_xpath',
                '//*[contains(@placeholder, "Address line 1")]')
            # Birthday
            post_data_to_search_filters(
                test_name,
                'birthday_xpath',
                '//*[contains(@placeholder, "Birthday")]')
    elif leads:
        post_data_to_search_filters(
            test_name,
            'addr_xpath',
            '//*[contains(@placeholder, "Address line 1")]')
        post_data_to_search_filters(
            test_name,
            'addr2_xpath',
            '//*[contains(@placeholder, "Address line 2")]')
        wait_element_and_send('//*[contains(@placeholder, "Address line 2")]',
                              Keys.PAGE_DOWN)
        time.sleep(3)
        post_data_to_search_filters(test_name, 'state_xpath',
                                    '//*[contains(@placeholder, "State")]')
        # Birthday
        wait_element_and_click('//*[contains(@placeholder, "Birthday")]')
        check_search_filters(test_name, 'birthday_xpath',
                             '//*[contains(@placeholder, "Birthday")]')

    # Tag
    time.sleep(0.5)
    tag_name = find_data_in_mongo(test_name,
                                  {'xpath': '//*[@id="0"]/ul/li/input'})
    click_on_search_and_filter()
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input',
        tag_name['value'])
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ARROW_UP)
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ENTER)
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ESCAPE)
    wait_element_and_click('//*[contains(@title, "{}")]'.format(tag_name['value']))
    save_search_filters()
    time.sleep(1)
    data = find_data_in_mongo(test_name)
    try:
        check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                              data['value'])
    except exceptions.NoSuchElementException:
        assert 'This is bug' == 'Is it fixed?', "Search give no result"


def search_contact_company_name(test_name):
    """ Search company and check if its present in results """
    company_name = find_data_in_mongo(
        test_name, {'xpath': '//*[@id="contact_company_input"]'})
    data = find_data_in_mongo(test_name)
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]',
        company_name['value'])
    time.sleep(1)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])


def check_customers_search_presets():
    presets_path = ['//*[contains(@title, "My customers")]',
                    '//*[contains(@title, "Closed customers")]',
                    '//*[contains(@title, "Customers without")]',
                    '//*[contains(@title, "Customers with Overdue")]',
                    ]
    for preset in presets_path:
        click_on_search_and_filter()
        wait_element_and_click(preset)
        time.sleep(2)
        search_clear_button()
        time.sleep(2)


def fill_lead_group(test_name=False):
    wait_element_and_click('//*[contains(@title, "gr 1")]')
    time.sleep(1)
    # Text, Numeric, Checkbox
    text_field = random_data()
    num_field = randint(100, 999)
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[1]/div[2]/input', text_field)
    wait_element_and_send_text('//*[@id="edit_card"]/div/div[4]/div[2]/div[2]/input', num_field)
    wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[3]/div[2]/label')
    # Select
    wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[4]/div[2]/div/button')
    wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[4]/div[2]/div/ul/li[3]')
    # Multiselect
    wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[5]/div[2]/div')
    wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[5]/div[2]/div/div[1]/div/div[3]/label')
    # Date
    date_field = '03.01.' + str(randint(2016, 2019))
    wait_element_and_send(
        '//*[@id="edit_card"]/div/div[4]/div[6]/div[2]//input',
        date_field)
    # URL
    url_field = 'http://' + random_data()
    textarea_field = random_data()
    shortaddr_field = random_data()
    birthday_field = '03.01.' + str(randint(2016, 2019))
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[7]/div[2]//input', url_field)
    # Textarea
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[8]/div[2]//textarea',
        textarea_field)
    # Radiobutton
    wait_element_and_click(
        '//*[@id="edit_card"]/div/div[4]/div[9]/div[2]/label[2]')
    # Short addr
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[10]/div[2]//textarea',
        shortaddr_field)
    # Addr
    addr_field = random_data()
    addr_field2 = random_data()
    city = random_data()
    state = random_data()
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[11]/div[2]/div/div[1]/input',
        addr_field)
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[11]/div[2]/div/div[2]/input',
        addr_field2)
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[11]/div[2]/div/div[3]/input',
        city)
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[11]/div[2]/div/div[4]/input',
        state)
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[11]/div[2]/div/div[5]/input',
        random_data())
    wait_element_and_click(
        '//*[@id="edit_card"]/div/div[4]/div[11]/div[2]/div/div[6]/div/button')
    wait_element_and_click(
        '//*[@id="edit_card"]/div/div[4]/div[11]/' +
        'div[2]/div/div[6]/div/ul/li[8]/span')
    # Birthday
    wait_element_and_send(
        '//*[@id="edit_card"]/div/div[4]/div[12]/div[2]//input',
        birthday_field)

    # New fields
    taxid_field_name = random_data()
    taxid_field_itin = random_n_digits(10)
    taxid_field_iec = random_n_digits(10)
    legal_name_field = random_data()
    datetime_field = '03.01.' + str(randint(2016, 2019)) + ' 13:48'
    # Tax ID
    wait_element_and_send('//*[@id="edit_card"]/div/div[4]/div[13]/div[1]/div[2]/div/div[1]//input', taxid_field_name)
    wait_element_and_send('//*[@id="edit_card"]/div/div[4]/div[13]/div[1]/div[2]/div/div[2]//input', taxid_field_itin)
    wait_element_and_send('//*[@id="edit_card"]/div/div[4]/div[13]/div[1]/div[2]/div/div[3]//input', taxid_field_iec)
    # Legal name
    wait_element_and_send('//*[@id="edit_card"]/div/div[4]/div[14]/div/div[2]/div/div/div/input', legal_name_field)
    # Datetime
    wait_element_and_click('//*[@id="edit_card"]/div/div[4]/div[15]/div[2]/span/input')
    wait_element_and_send('//*[@id="edit_card"]/div/div[4]/div[15]/div[2]/span/input', datetime_field)

    # Save
    wait_element_and_click('//*[contains(@class, "card-top-save-button")]')
    time.sleep(3)
    # Save all data to mongo
    if test_name:
        save_data_to_mongo(test_name,
                           {'xpath': 'text_xpath',
                            'value': text_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'num_xpath',
                            'value': num_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'date_xpath',
                            'value': date_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'url_xpath',
                            'value': url_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'textarea_xpath',
                            'value': textarea_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'shortaddr_xpath',
                            'value': shortaddr_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'addr_xpath',
                            'value': addr_field})
        save_data_to_mongo(test_name,
                           {'xpath': 'addr2_xpath',
                            'value': addr_field2})
        save_data_to_mongo(test_name,
                           {'xpath': 'sity_xpath',
                            'value': city})
        save_data_to_mongo(test_name,
                           {'xpath': 'state_xpath',
                            'value': state})
        save_data_to_mongo(test_name,
                           {'xpath': 'birthday_xpath',
                            'value': birthday_field})


def check_leads_search_presets():
    presets_path = ['//*[contains(@title, "My leads")]',
                    '//*[contains(@title, "Won leads")]',
                    '//*[contains(@title, "Lost leads")]',
                    '//*[contains(@title, "Leads without")]',
                    '//*[contains(@title, "Leads with Overdue")]',
                    '//*[contains(@title, "Deleted")]',
                    ]
    for preset in presets_path:
        click_on_search_and_filter()
        wait_element_and_click(preset)
        time.sleep(2)
        search_clear_button()
        time.sleep(1)


def search_contact_name(test_name):
    """ Search contact and check if its present in results """
    contact_name = find_data_in_mongo(
        test_name, {'contact_name_xpath': '//*[@id="new_contact_n"]'})
    data = find_data_in_mongo(test_name)
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Search and filter")]',
        contact_name['value'])
    time.sleep(1)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])


def to_properties_of_a_linked_element(element_type):
    """ Contact or company filter """
    if element_type == "contact":
        wait_element_and_click('//*[@id="filter_form"]/div[1]/div[2]/h3/span')
    else:
        wait_element_and_click('//*[@id="filter_form"]/div[1]/div[3]/h3/span')


def lead_linked_elements_search(test_name, element_type):
    # Text
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    if element_type == 'company':
        linked_element = 'Properties of a linked company'
    else:
        linked_element = 'Properties of a linked contact'
    check_search_filters(test_name, 'text_xpath',
                         '//span[text()="{}"]/../..//*[@placeholder="Short text"]'.format(linked_element))

    # Numeric
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    check_search_filters(test_name, 'num_xpath',
                         '//span[text()="{}"]/../..//*[@placeholder="Numeric"]'.format(linked_element))
    # Checkbox -> Yes
    if element_type == "contact":
        click_on_search_and_filter()
        to_properties_of_a_linked_element(element_type)
        wait_element_and_click(
            '//span[text()="{}"]/../..//*[contains(@data-before, "Toggle switch")]'.format(linked_element))
        wait_element_and_click(
            '//span[text()="{}"]/../..//*[contains(@data-before, "Toggle switch")]/../ul/li[@data-value="Y"]'.format(
                linked_element))
        save_search_filters()
        data = find_data_in_mongo(test_name)
        check_text_of_element(
            '//*[contains(@title, "{}")]'.format(data['value']), data['value'])
        search_clear_button()
    # Select
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    wait_element_and_click('//span[text()="{}"]/../..//*[contains(@data-before, "Select")]'.format(linked_element))
    wait_element_and_click(
        '//span[text()="{}"]/../..//*[contains(@data-before, "Select")]/../ul/li[4]'.format(linked_element))
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Multiselect
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    wait_element_and_click(
        '//span[text()="{}"]/../..//*[contains(@data-title-before, "Multiselect")]'.format(linked_element))
    wait_element_and_click(
        '//span[text()="{}"]/../..//*[contains(@data-title-before, "Multiselect")]/../../../../div[1]/div/div[4]/label'.format(
            linked_element))
    ActionChains(driver).send_keys(Keys.ESCAPE)
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Date
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    wait_element_and_click('//span[text()="{}"]/../..//*[@placeholder="Date"]'.format(linked_element))
    check_search_filters(test_name, 'date_xpath',
                         '//span[text()="{}"]/../..//*[@placeholder="Date"]'.format(linked_element))
    # URL
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    check_search_filters(test_name, 'url_xpath',
                         '//span[text()="{}"]/../..//*[@placeholder="Url"]'.format(linked_element))
    # Textarea
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    check_search_filters(test_name, 'textarea_xpath',
                         '//span[text()="{}"]/../..//*[@placeholder="Long text"]'.format(linked_element))
    # Radiobutton
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    wait_element_and_click('//span[text()="{}"]/../..//*[contains(@data-before, "Radiobutton")]'.format(linked_element))
    wait_element_and_click(
        '//span[text()="{}"]/../..//*[contains(@data-before, "Radiobutton")]/../ul/li[4]'.format(linked_element))
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()
    # Short address
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    check_search_filters(test_name, 'shortaddr_xpath',
                         '//span[text()="{}"]/../..//*[@placeholder="Short address"]'.format(linked_element))
    # Addr 1
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    check_search_filters(test_name, 'addr_xpath',
                         '//span[text()="{}"]/../..//*[contains(@placeholder, "Address line 1")]'.format(
                             linked_element))
    # Birthday
    if element_type == "contact":
        click_on_search_and_filter()
        to_properties_of_a_linked_element(element_type)
        wait_element_and_click(
            '//span[text()="{}"]/../..//*[contains(@placeholder, "Birthday")]'.format(linked_element))
        check_search_filters(
            test_name,
            'birthday_xpath',
            '//span[text()="{}"]/../..//*[contains(@placeholder, "Birthday")]'.format(linked_element))
    # Tag
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    tag_name = find_data_in_mongo(test_name,
                                  {'xpath': '//*[@id="0"]/ul/li/input'})
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input',
        tag_name['value'])
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ARROW_UP)
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ENTER)
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ESCAPE)
    # wait_element_and_click('//*[contains(@title, "{}}")]'.format(tag_name['value']))
    time.sleep(0.5)
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])
    search_clear_button()


def lead_linked_elements_combined_search(test_name, element_type):
    if element_type == 'company':
        linked_element = 'Properties of a linked company'
    else:
        linked_element = 'Properties of a linked contact'

    # Text
    click_on_search_and_filter()
    to_properties_of_a_linked_element(element_type)
    post_data_to_search_filters(test_name, 'text_xpath',
                                '//span[text()="{}"]/../..//*[@placeholder="Short text"]'.format(linked_element))
    # Numeric
    post_data_to_search_filters(test_name, 'num_xpath',
                                '//span[text()="{}"]/../..//*[@placeholder="Numeric"]'.format(linked_element))
    # Checkbox -> Yes
    if element_type == "contact":
        wait_element_and_click(
            '//span[text()="{}"]/../..//*[contains(@data-before, "Toggle switch")]'.format(linked_element))
        wait_element_and_click(
            '//span[text()="{}"]/../..//*[contains(@data-before, "Toggle switch")]/../ul/li[@data-value="Y"]'.format(
                linked_element))
    # Select
    wait_element_and_click('//span[text()="{}"]/../..//*[contains(@data-before, "Select")]'.format(linked_element))
    wait_element_and_click(
        '//span[text()="{}"]/../..//*[contains(@data-before, "Select")]/../ul/li[4]'.format(linked_element))
    # Multiselect
    wait_element_and_click(
        '//span[text()="{}"]/../..//*[contains(@data-title-before, "Multiselect")]'.format(linked_element))
    wait_element_and_click(
        '//span[text()="{}"]/../..//*[contains(@data-title-before, "Multiselect")]/../../../../div[1]/div/div[4]/label'.format(
            linked_element))
    # Missclick
    wait_element_and_click('//*[@class="filter-search__left"]')
    # Date
    wait_element_and_click('//span[text()="{}"]/../..//*[@placeholder="Date"]'.format(linked_element))
    post_data_to_search_filters(test_name,
                                'date_xpath',
                                '//span[text()="{}"]/../..//*[@placeholder="Date"]'.format(linked_element))
    # URL
    post_data_to_search_filters(test_name, 'url_xpath',
                                '//span[text()="{}"]/../..//*[@placeholder="Url"]'.format(linked_element))
    # Textarea
    post_data_to_search_filters(test_name,
                                'textarea_xpath',
                                '//span[text()="{}"]/../..//*[@placeholder="Long text"]'.format(linked_element))
    # Radiobutton
    wait_element_and_click('//span[text()="{}"]/../..//*[contains(@data-before, "Radiobutton")]'.format(linked_element))
    wait_element_and_click(
        '//span[text()="{}"]/../..//*[contains(@data-before, "Radiobutton")]/../ul/li[4]'.format(linked_element))
    # Short address
    post_data_to_search_filters(test_name,
                                'shortaddr_xpath',
                                '//span[text()="{}"]/../..//*[@placeholder="Short address"]'.format(linked_element))
    # Addr 1
    post_data_to_search_filters(test_name,
                                'addr_xpath',
                                '//span[text()="{}"]/../..//*[contains(@placeholder, "Address line 1")]'.format(
                                    linked_element))
    # Birthday
    if element_type == "contact":
        wait_element_and_click()
        post_data_to_search_filters(test_name,
                                    'birthday_xpath',
                                    '//span[text()="{}"]/../..//*[contains(@placeholder, "Birthday")]'.format(
                                        linked_element))
    # Tag
    time.sleep(1)
    tag_name = find_data_in_mongo(test_name,
                                  {'xpath': '//*[@id="0"]/ul/li/input'})
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input',
        tag_name['value'])
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ARROW_UP)
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ENTER)
    wait_element_and_send(
        '//*[@id="filter-search__tags-lib"]/div/ul[1]/li/input', Keys.ESCAPE)
    time.sleep(0.5)
    # wait_element_and_click('//*[contains(@title, "{}}")]'.format(tag_name['value']))
    save_search_filters()
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])


def logout():
    wait_element_and_click('//*[contains(@class, "n-avatar")]')
    wait_element_and_click('//*[contains(@href, "/?logout=yes")]')


def login_on_spot(stand, account=False):
    with open('settings.yml') as auth_pair:
        pair = yaml.load(auth_pair)
    if account:
        login = pair['auth'][ServerType][stand][account]
        password = pair['auth'][ServerType][stand]['password']
    else:
        login = pair['auth'][ServerType][stand]['login']
        password = pair['auth'][ServerType][stand]['password']
    wait_element_and_send_text('//*[contains(@id, "session_end_login")]', login)
    wait_element_and_send_text('//*[contains(@id, "password")]', password)
    wait_element_and_click('//*[contains(@class, "auth_form__submit")]')


def create_dublicate_contact(test_name):
    contact_name = random_data()
    wait_element_and_send_text('.//*[@id="person_n"]', contact_name)
    work_phone = find_data_in_mongo(test_name, {'xpath': 'work_phone'})
    work_email = find_data_in_mongo(test_name, {'xpath': 'work_email'})
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[1]/div[1]/div[2]/div/div['
        '1]/input',
        work_phone['value'])
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[2]/div[1]/div[2]/div/div['
        '1]/input',
        work_email['value'])
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[3]/div[2]/input', random_data())
    wait_element_and_send_text(
        '//*[@id="edit_card"]/div/div[4]/div[4]/div[1]/div[2]/input',
        random_data())
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span')
    time.sleep(0.5)


def use_duplicate_in_card():
    try:
        wait_element_and_click('//*[contains(@title, "Duplicate?")]')
    except exceptions.NoSuchElementException:
        assert 'Duplicate did' == 'not displayed', "Duplicate in card did not displayed"
    # responsible user
    wait_element_and_click(
        '//*[contains(@class, "card-merge__pane-field js-card-main-fields ' +
        'card-merge__pane-field_responsible  js-card-merge-field")]')
    # first contact
    wait_element_and_click(
        '//*[contains(@class, "card-merge__pane-field ' +
        'card-merge__pane-field_status  js-card-merge-field")]')
    # merge
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-merge-save")]')
    time.sleep(1)


def to_find_duplicates():
    """ Leads -> lists -> menu -> find duplicates """
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu")][@title="More"]')
    time.sleep(0.5)
    wait_element_and_click('//*[contains(@class, "button-input__context-menu__item__icon'
                           ' svg-icon svg-common--merge-dims")]')


def merge_duplicates():
    wait_element_and_click('//*[contains(@class, "js-merge-start")]')
    time.sleep(1)


def unsorted_leads_multi(doing):
    lists_elem = driver.find_elements_by_xpath('//*[contains(@id, "lead_")]')
    lists_elem[6].click()
    lists_elem[7].click()
    lists_elem[8].click()
    if doing == "accept":
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions__item__icon' +
            ' icon icon-checkmark-green")]')
    else:
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions__item__icon ' +
            'icon icon-unsorted-decline")]')
    time.sleep(5)


def reg_new_account(test_name, stand, account=False):
    """ Login as a user and add new account """
    if ServerType == 'PROD_USA':
        url = "https://www.amocrm.com"
    else:
        url = "https://www.amocrm.ru"
    driver.get(url)
    with open('settings.yml') as auth_pair:
        pair = yaml.load(auth_pair)
    if account:
        login = pair['auth'][ServerType][stand][account]
        password = pair['auth'][ServerType][stand]['password']
    else:
        login = pair['auth'][ServerType][stand]['login']
        password = pair['auth'][ServerType][stand]['password']
    wait_element_and_click('//*[@id="page_header__auth_button"]/div')
    wait_element_and_send_text('//*[@id="auth-email login"]', login)
    wait_element_and_send_text('//*[@id="auth-password Password"]', password)
    wait_element_and_click('//*[contains(@id, "form_auth__button_submit")]')
    wait_element_and_click(
        '//*[contains(@class, "js-user-select-current ' +
        'user-select__user-current")]')
    # Scroll to logout to avoid missclicking on the banner
    time.sleep(0.5)
    log_out_button = driver.find_element_by_xpath(
        '//*[contains(@class, "icon-log-out")]')
    driver.execute_script(
        "return arguments[0].scrollIntoView();", log_out_button)
    wait_element_and_click('//*[contains(@class, "button_create-new")]')
    account_name = find_data_in_mongo(test_name)
    # Scroll bottom to text under "create acc" button
    # to avoid missclicking on the banner
    wait_element_and_click('//*[contains(@class, "acc_afteracc")]')
    # Add account name and save
    wait_element_and_click('//*[contains(@id, "new_acc_form_init")]')
    wait_element_and_send_text('//*[contains(@name, "account_name")]',
                               account_name['value'])
    wait_element_and_click('//*[contains(@id, "submit_new_acc_form")]')
    time.sleep(0.5)


def reg_new_user(test_name):
    """ Register as a new user """
    # go to trial
    wait_element_and_click(
        '//*[contains(@class, "page_header__auth__trial_link")]')
    time.sleep(1)
    # fill name.
    name = random_data()
    wait_element_and_send_text(
        '//*[contains(@class, "try_now_person")]',
        name)
    # fill email
    wait_element_and_send_text(
        '//*[contains(@class, "try_now_mail")]',
        name + '@example.com')
    # fill telephone
    wait_element_and_send(
        '//*[contains(@class, "new_try_now__input") and @id= "phone"]',
        '89000000000')
    # Submit
    wait_element_and_click(
        '//*[@id = "try_now__button_submit"]//*[ text() = "Старт"]')
    time.sleep(5)
    # Save name and subdomen in MongoDB
    save_data_to_mongo(test_name,
                       {'subdomain': get_subdomain(),
                        'name': name})


def welcome_form():
    new_pass = random_data()
    wait_element_and_click(
        '//*[@id="welcome-form__field--password"]/span')
    # Password comparison check
    wait_element_and_send_text(
        '//*[contains(@id, "welcome-form_password_new")]', new_pass)
    wait_element_and_send_text(
        '//*[contains(@id, "welcome-form_password_confirm")]', random_data())
    assert driver.find_element_by_xpath(
        '//*[contains(@class, "button-input    welcome-form__button '
        'welcome-form__button--save welcome-form--toggle '
        'button-input-disabled")]'), ('Button is enable, but passwords are not the same')
    wait_element_and_send_text(
        '//*[contains(@id, "welcome-form_password_new")]', new_pass)
    wait_element_and_send_text(
        '//*[contains(@id, "welcome-form_password_confirm")]', new_pass)
    wait_element_and_click(
        '//*[contains(@id, "welcome-form_save")]')


def fill_tour():
    # Company name
    wait_element_and_send_text(
        '//*[contains(@id, "qualify-form_company_name")]', random_data())
    # Industry -> IT
    wait_element_and_click(
        '//*[@id="qualification_form"]/div[1]/div[2]/div[2]/div/button')
    wait_element_and_click(
        '//*[@id="qualification_form"]/div[1]/div[2]/div[2]/div/ul/li[4]')
    # Your role in company
    wait_element_and_click(
        '//*[@id="qualification_form"]/div[1]/div[3]/div[2]/div/button')
    wait_element_and_click(
        '//*[@id="qualification_form"]/div[1]/div[3]/div[2]/div/ul/li[6]')
    # Employers in company
    wait_element_and_send_text(
        '//*[contains(@id, "qualify-form_employees_count")]', randint(1, 100))
    # CRM Users
    wait_element_and_send_text(
        '//*[contains(@id, "qualify-form_crm_users_count")]', randint(1, 100))
    # Exp with CRM
    wait_element_and_click(
        '//*[@id="qualification_form"]/div[1]/div[6]/div[2]/div/button')
    wait_element_and_click(
        '//*[@id="qualification_form"]/div[1]/div[6]/div[2]/div/ul/li[3]')
    # Marketing departament
    wait_element_and_click(
        '//*[@id="qualification_form"]/div[1]/div[7]/div[2]/div/button')
    wait_element_and_click(
        '//*[@id="qualification_form"]/div[1]/div[7]/div[2]/div/ul/li[2]')
    wait_element_and_click('//*[contains(@id, "qualify-form_submit")]')
    time.sleep(1)


def end_tour():
    """ End beginning tour """
    for _ in range(4):
        time.sleep(4)
        wait_element_and_click('//*[text() = "Далее"]')
    time.sleep(5)


def add_colleagues():
    wait_element_and_send_text('//*[contains(@name, "add_multiple_input_1")]',
                               random_data() + '@example.com')
    wait_element_and_send_text('//*[contains(@name, "add_multiple_input_2")]',
                               random_data() + '@example.com')
    wait_element_and_send_text('//*[contains(@name, "add_multiple_input_3")]',
                               random_data() + '@example.com')
    wait_element_and_click(
        '//*[contains(@class, "users-add-multiple-modal")]'
        '//*[contains(@class, "modal-body__actions__save button-input_blue")]')
    time.sleep(15)


def fill_first_lead():
    wait_element_and_send('//*[contains(@id, "quick_add_lead_name")]',
                          random_data())
    wait_element_and_send_text('//*[contains(@id, "quick_add_lead_budget")]',
                               randint(100, 999))
    wait_element_and_send_text(
        '//*[contains(@id, "quick_lead_contact_search")]', random_data())
    wait_element_and_send_text('//*[contains(@id, "quick_add_lead_phone")]',
                               random_data())
    wait_element_and_send_text('//*[contains(@id, "quick_add_lead_email")]',
                               random_data() + '@example.com')
    wait_element_and_click('//*[contains(@id, "quick_add_form_btn")]')
    time.sleep(5)


def drag_first_lead_to_pipeline():
    time.sleep(5)
    source = driver.find_element_by_xpath(
        '//*[contains(@class, "pipeline__body")]' +
        '//*[contains(@class, "pipeline_leads__top-block")]')
    dest = driver.find_element_by_xpath(
        '//*[contains(@class, "welcome-tour__step__lead_placeholder")]')
    drag_and_drop(source, dest)
    time.sleep(3)


def first_pipeline_statuses():
    wait_element_and_click(
        '//*[contains(@class, "button-delete remove-status-variant")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept ' +
        'js-button-with-loader modal-body__actions__save ")]')
    wait_element_and_click('//*[contains(@id, "add-status-field")]')
    wait_element_and_send_text('//*[contains(@data-id, "new_4")]',
                               random_data())
    wait_element_and_click('//*[contains(@id, "save_statuses_settings")]')
    time.sleep(2)


def connect_first_form():
    wait_element_and_click('//*[contains(@class, "dp-source__caption")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    ' +
        'button-cancel js-settings-cf-reset")]')


def account_to_teststand(test_name, stand, new_user=False):
    stand_dict = {
        's1': '//*[@id="page_holder"]/div/form[1]' +
              '/table/tbody/tr[1]/td/div[2]/textarea',
        's2': '//*[@id="page_holder"]/div/form[2]' +
              '/table/tbody/tr[1]/td/div[2]/textarea',
        's3': '//*[@id="page_holder"]/div/form[3]' +
              '/table/tbody/tr[1]/td/div[2]/textarea',
    }
    button_index = {'s1': 0, 's2': 1, 's3': 2}
    wait_element_and_send(stand_dict[stand], Keys.ENTER)
    if new_user:
        data = find_data_in_mongo(test_name)
        subdomain = data['subdomain']
    else:
        subdomain = random_data()
        save_data_to_mongo(test_name,
                           {'subdomain': 'account_name', 'value': subdomain})
    wait_element_and_send(stand_dict[stand], subdomain)
    done = driver.find_elements_by_xpath(
        '//*[contains(@id, "switch_redesign")]')
    done[button_index[stand]].click()
    driver.close()


def login_in_staging_switcher():
    global driver
    # Chrome options
    chrome_options = webdriver.ChromeOptions()
    # Enable notifications
    pref = {"profile.default_content_setting_values.notifications": 1}
    chrome_options.add_experimental_option("prefs", pref)
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(
        '/usr/local/selenium_drivers/chromedriver',
        chrome_options=chrome_options)
    driver.get(
        "https://www.dev.amocrm.com/_system/account/staging.php?lang=ru"
        "&redirect=Y")
    keys = read_secret_keys_file()
    login = keys['switcher_login']
    password = keys['switcher_password']
    wait_element_and_send_text('//*[contains(@id, "name")]', login)
    wait_element_and_send_text('//*[contains(@id, "password")]', password)
    wait_element_and_click('//*[contains(@class, "auth_form__submit")]')
    time.sleep(2)
    driver.get(
        "https://www.dev.amocrm.com/_system/account/staging.php?lang=ru"
        "&redirect=Y")


def execute_switch_to_stage():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    keys = read_secret_keys_file()
    server_addr = keys['server']
    login = keys['server_login']
    passwd = keys['server_password']
    try:
        client.connect(server_addr, port=22, username=login, password=passwd)
        client.exec_command(
            'sudo /root/scripts/switch_to_stage.sh 2>&1 |' +
            ' sudo tee -a /var/log/amocrm/switch_to_stage.log')
    except:
        raise
    client.close()


def read_secret_keys_file():
    with open('secret_keys.json') as secret_keys:
        keys = json.load(secret_keys)
    return keys


def manage_tags():
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu")' +
        ' and contains(@tabindex, "-1")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input__context-menu__item__icon' +
        ' svg-icon svg-common--tag-dims ")]')


def manage_tags_add_new_tag(test_name):
    new_tag = random_data()
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Find or add a tag")]', new_tag)
    wait_element_and_click('//*[contains(@class, "new-tag")]')
    time.sleep(1)
    save_data_to_mongo(test_name, {'name': 'new_tag', 'value': new_tag})


def manage_tags_search_tag(test_name):
    tag = find_data_in_mongo(test_name, {'name': 'new_tag'})
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Find or add a tag")]', tag['value'])
    time.sleep(1)


def manage_tags_delete_tag():
    wait_element_and_click(
        '//*[contains(@class, "js-tags-lib__item-delete' +
        ' tags-lib__item-delete")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept' +
        ' js-button-with-loader modal-body__actions__save ")]')
    time.sleep(0.5)
    wait_element_and_click('//*[contains(@class, "icon icon-modal-close")]')


def export_from_card():
    wait_element_and_click(
        '//*[contains(@class, "button-input  button-input-with-menu")' +
        ' and contains(@tabindex, "-1")]')
    wait_element_and_click('//*[contains(@href, "/export/")]')


def edit_first_customer_name():
    mouse_to_element('//*[contains(@data-field-id, "name")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    wait_element_and_send_text(
        '//*[contains(@class, "linked-form__cf text-input")]', random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')


def edit_first_customer_amount(click_aside=False):
    """ Edit expected amount for first customer in list.
    Parameters:
    :click_aside - bool, with this parameter driver click aside
                   after insert new sum.
    """
    mouse_to_element('//*[contains(@data-field-id, "next_price")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    wait_element_and_send_text(
        '//*[contains(@class, "linked-form__cf text-input")]',
        randint(100, 999))
    if click_aside:
        wait_element_and_click('//*[contains(@id, "page_holder")]')
        confirm_save_changes()
    else:
        wait_element_and_click(
            '//*[contains(@class, "cell-edit__buttons")]' +
            '//*[contains(text(), "Save")]')


def edit_first_customer_next_purchase(bought=False):
    """ Edit expected amount for first customer in list.
    Parameters:
    :bought - bool, with this parameter driver click on Bought
              and specify the sum of purchase and the date (period) of the next
              purchase.
    """
    mouse_to_element('//*[contains(@data-field-id, "next_date")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    if bought:
        # Click on bought
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-purchase-button ' +
            'customers-date__purchase-button")]')
        wait_element_and_send_text(
            '//*[contains(@class, "js-control-pretty-price ' +
            'js-form-changes-skip  text-input")]',
            randint(100, 999))
        wait_element_and_click(
            '//*[contains(@class, "make-purchase__save")]')
    else:
        # Click on calendar and type new date
        new_date = '0{}.0{}.'.format(randint(1, 9), randint(1, 9)) + str(
            randint(2018, 2020))
        wait_element_and_send_text(
            '//*[contains(@id, "task_edit_date")]',
            new_date)
        wait_element_and_click('//*[contains(@id, "page_holder")]')
        # Save
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-modal-accept")]')


def deattach_first_lead_main_contact():
    """ Deattach main contact if first row in the list """
    mouse_to_element(
        '//*[contains(@class, "pager-list-item__1")]' +
        '//*[contains(@class, "list-row__cell-main_contact")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    # Select deattach
    wait_element_and_click(
        '//*[contains(@title, "Detach")]')
    time.sleep(0.2)
    wait_element_and_click(
        '//*[contains(@class, "modal-body")]//*[contains(text(), "Yes")]')
    time.sleep(1)


def detach_first_lead_company():
    """ Detach company if first row in the list """
    mouse_to_element(
        '//*[contains(@class, "pager-list-item__1")]' +
        '//*[contains(@class, "list-row__cell-company_name")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    # Select detach
    try:
        wait_element_and_click(
            '//*[contains(@title, "Detach")]')
        time.sleep(0.2)
    except common.exceptions.NoSuchElementException:
        wait_element_and_send('//*[@name="company_name"]', random_data())
        wait_element_and_click('//*[contains(@class, "button-input    js-modal-accept")]')
        time.sleep(2)
        mouse_to_element(
            '//*[contains(@class, "pager-list-item__1")]' +
            '//*[contains(@class, "list-row__cell-company_name")]')
        wait_element_and_click('//*[contains(@title, "Edit")]')
        wait_element_and_click(
            '//*[contains(@title, "Detach")]')
        time.sleep(0.2)
    wait_element_and_click(
        '//*[contains(@class, "modal-body")]//*[contains(text(), "Yes")]')
    time.sleep(1)


def first_lead_main_contact_cleaner():
    """ Check main conact field in lead lists and clean it """
    contact_name_xpath = ('//*[contains(@class, "pager-list-item__1")]'
                          '//*[contains(@class,'
                          ' "list-row__cell-main_contact")]'
                          '//a')
    if driver.find_elements_by_xpath(contact_name_xpath):
        deattach_first_lead_main_contact()


def first_lead_company_cleaner():
    """ Check conact field in lead lists and clean it """
    contact_name_xpath = ('//*[contains(@class, "pager-list-item__1")]'
                          '//*[contains(@class,'
                          ' "list-row__cell-company_name")]'
                          '//a')
    if driver.find_elements_by_xpath(contact_name_xpath):
        detach_first_lead_company()


def edit_first_lead(param, click_aside=False):
    """ Edit main contact name for first customer in list.
    Parameters:
    :param - str, may be 'lead_title', 'company', 'contact' for different
             cases of edit
    :click_aside - bool, with this parameter driver click aside
             after insert new name.
    :to_empty - bool, in the case of empty field, use another xpath to find
             input area
    """
    # Select xpath part
    if param == 'lead_title':
        xpath_part = 'list-row__cell-template-name'
    elif param == 'company':
        xpath_part = 'list-row__cell-company_name'
    elif param == 'contact':
        xpath_part = 'list-row__cell-main_contact'
    elif param == 'contacts_company':
        xpath_part = 'list-row__cell-contact_company_name'
    # Begin edit
    time.sleep(1)
    mouse_to_element(
        '//*[contains(@class, "pager-list-item__1")]' +
        '//*[contains(@class, "{}")]'.format(xpath_part))
    wait_element_and_click('//*[contains(@title, "Edit")]')
    name = random_data()
    if driver.find_elements_by_xpath('//*[contains(@class, "linked-form__cf linked-form__ajax-input")]'):
        # in the case of empty field
        wait_element_and_send_text(
            '//*[contains(@class, "linked-form__cf") and contains(@class, "text-input")]', name, use_send_keys=True)
    else:
        # in the case of non-empty field
        wait_element_and_send_text('//*[contains(@class, "linked-form__cf")]', name, use_send_keys=True)
    if click_aside:
        wait_element_and_click('//*[contains(@id, "page_holder")]')
        confirm_save_changes()
    else:
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(2)
    titles = driver.find_elements_by_xpath(
        '//*[contains(@class, "pager-list-item__1")]' +
        '//*[contains(@class, "{}")]//a'.format(xpath_part))
    titles = [title.text for title in titles]
    assert name in titles, f'{name} is not saved'


def edit_first_lead_respuser(first_user=False, company=False):
    """ Change responsible user for first lead
    Parameters:
    :first_user - bool, select fisrt user if True
    """
    mouse_to_element(
        '//*[contains(@class, "pager-list-item__1")]' +
        '//*[contains(@class, "list-row__cell-manager")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    users = ["Mister Amo", "Senior Amo", "Frau Amo"]
    if first_user:
        wait_element_and_click(
            '//*[contains(@class, "users-select-row")]' +
            '//*[contains(text(), "edit_on_place")]')
    else:
        wait_element_and_click(
            '//*[contains(@class, "users-select-row")]' +
            '//*[contains(text(), "{}")]'.format(choice(users)))
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)
    if not company:
        wait_element_and_click(
            '//*[contains(@class, "modal-body")]//*[contains(text(), "Yes")]')
    time.sleep(6)


def edit_first_lead_near_todo_add():
    mouse_to_element(
        '//*[contains(@class, "list-row__cell js-list-row__cell' +
        ' list-row__cell-template-nearest_task ' +
        'list-row__cell-date_of_nearest_task")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    # Date
    wait_element_and_click(
        '//*[contains(@class, "tasks-date__caption")]')
    time_list = ['//*[contains(@data-period, "before_end_of_week")]',
                 '//*[contains(@data-period, "next_week")]',
                 '//*[contains(@data-period, "next_month")]',
                 '//*[contains(@data-period, "next_year")]',
                 ]
    wait_element_and_click(choice(time_list))
    # User
    if not driver.find_elements_by_xpath('//*[contains(@class, "feed-compose-user js-feed-users")]'):
        assert 'This is bug' == 'Is it fixed?', 'Todo form is closing when you choose date period'
    # wait_element_and_click('//*[@id="cell-edit-body-overlay"]')
    wait_element_and_click(
        '//*[contains(@class, "feed-compose-user js-feed-users")]')
    users = ["Mister Amo", "Senior Amo", "Frau Amo"]
    wait_element_and_send_text(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        choice(users))
    wait_element_and_send(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        Keys.ENTER)
    # Task type
    wait_element_and_click(
        '//*[contains(@class, "card-task__type-wrapper")]')
    # Select Meeting
    wait_element_and_click(
        '//*[contains(@class, "card-task__types-item")]' +
        '//*[contains(text(), "Meeting")]')
    # Add comment
    wait_element_and_send_text(
        '//*[contains(@class, "js-control-contenteditable ' +
        'control-contenteditable card-task__actions")]/div[2]',
        random_data(),
        with_assert=False)
    wait_element_and_click(
        '//*[contains(@class, "js-task-submit feed-note__button")]')
    time.sleep(2)


def edit_first_lead_near_todo_close():
    mouse_to_element(
        '//*[contains(@class, "list-row__cell js-list-row__cell ' +
        'list-row__cell-template-nearest_task ' +
        'list-row__cell-date_of_nearest_task")]')
    wait_element_and_click('//*[contains(@title, "Close task")]')
    # Add result
    wait_element_and_send_text(
        '//*[contains(@class, "card-task__result-wrapper__inner__textarea' +
        ' js-task-result-textarea")]',
        random_data())
    # Meeting checkbox click
    wait_element_and_click('//*[contains(@name, "clone_task")]')
    # Date
    wait_element_and_click(
        '//*[contains(@class, "card-task__clone__dates__preset '
        'card-task__clone__dates__preset_selected js-clone-task-preset")]')
    new_date = '0{}.0{}.'.format(randint(1, 9), randint(1, 9)) + str(
        randint(2018, 2020))
    wait_element_and_send(
        '//*[contains(@class, "tasks-date__controls-date-input")]',
        new_date)
    wait_element_and_click('//*[@id="cell-edit-body-overlay"]')
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner")]' +
        '//*[contains(text(), "Complete")]')
    time.sleep(2)


def edit_first_lead_stage():
    """ Edit stage in first lead in the row """
    mouse_to_element(
        '//*[contains(@class, "pager-list-item__1")]' +
        '//*[contains(@class, "ist-row__cell-template-status")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    # Click on a pipeline
    wait_element_and_click(
        '//*[contains(@class, "cell-edit cell-edit-status")]'
        '//descendant::*[contains(@class, '
        '"pipeline-select-wrapper__inner__container")]')
    # Select random stage
    stages = ['Первичный контакт',
              'Переговоры',
              'Принимают решение',
              'Согласование договора',
              ]
    stage = driver.find_elements_by_xpath(
        '//*[contains(@class, "pipeline-select-wrapper")]' +
        '//*[contains(text(), "{}")]'.format(choice(stages)))
    wait_element_and_click(webelement=stage[-1])
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner ")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(1)


def edit_first_lead_sale():
    mouse_to_element(
        '//*[contains(@class, "list-row__cell js-list-row__cell ' +
        'list-row__cell-template-budget list-row__cell-budget")]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    wait_element_and_send_text(
        '//*[contains(@class, "js-control-pretty-price ' +
        'js-form-changes-skip linked-form__cf text-input")]',
        randint(1, 999))
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)


def edit_item():
    # Mouse to lists -> Custom list -> Add Item
    wait_element_and_click(
        '//*[contains(@class, "list-row__cell js-list-row__cell ' +
        'list-row__cell-template-name list-row__cell-name ")]')
    xpath_list = ['//*[@class="field template-name "]//*[@placeholder="Name"]',
                  '//*[@class="field template-text "]//*[@placeholder="SKU"]',
                  '//*[@class="field template-numeric "]//*[@placeholder="Quantity"]',
                  '//*[@class="field template-numeric "]//*[@placeholder="Price"]',
                  ]
    for xpath in xpath_list:
        random_number = randint(1000, 99999)
        wait_element_and_send_text(xpath, random_number)
    dropdown = driver.find_elements_by_xpath(
        '//*[contains(@class, "control--select--button")]')
    dropdown[7].click()
    yes = driver.find_elements_by_xpath('//*[contains(@title, "Yes")]')
    yes[1].click()

    wait_element_and_send(
        '//*[contains(@class, "date_field linked-form__cf")]',
        "20042019")
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)


def select_first_calendar_todo():
    """ Select first calendar to-do """
    wait_element_and_click(
        '//*[contains(@class, "item-id")]'
        '//*[contains(@class, "ist-row__cell-template-task_date")]')


def complite_calendar_todo(skip=True):
    """ Complete to-do """
    if skip:
        wait_element_and_click(
            '//*[contains(@class, "button-input") '
            'and contains(text(), "Complete to-do")]')
    else:
        wait_element_and_send(
            '//*[contains(@class, "card-task__result-wrapper__inner__textarea'
            ' js-task-result-textarea")]',
            random_data())
        wait_element_and_click(
            '//*[contains(@class, "button-input") '
            'and contains(text(), "Complete to-do")]')
    time.sleep(2)


def delete_first_delete_calendar_todo():
    """ Go to 'DAY' tab in calendar and delete first to-do """
    # go to DAY
    wait_element_and_click('//*[contains(@href, "/todo/calendar/day/")]')
    # Click on first calanedar
    wait_element_and_click(
        '//*[contains(@class, "fc-day-grid")]' +
        '//*[contains(@class, "fc-event-container")]')
    time.sleep(1)
    # Click on to-do tab
    wait_element_and_click(
        '//*[contains(@class, "card-task__result-wrapper__inner")]')
    # Clcik on trash icon
    wait_element_and_click(
        '//button[contains(@class, "feed-note__button_remove")]')
    wait_element_and_click(
        '//*[contains(@class, "modal-body__actions ")]'
        '//*[contains(text(), "Yes")]')
    time.sleep(1)


def edit_first_phone():
    mouse_to_element(
        '//*[contains(@class, "list-row__cell ' +
        'js-list-row__cell list-row__cell-template-custom")][1]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    wait_element_and_send_text(
        '//*[contains(@class, "control-phone__formatted")]', random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(1)


def edit_first_email():
    time.sleep(0.5)
    mouse_to_element(
        '//*[contains(@class, "list-row__cell ' +
        'js-list-row__cell list-row__cell-template-custom")][2]')
    wait_element_and_click('//*[contains(@title, "Edit")]')
    wait_element_and_send_text(
        '//*[contains(@class, "linked-form__field__value")]//input',
        random_data())
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')
    time.sleep(0.5)


def search_amojo_admin_user_in_notify_center():
    """ Take random user form list and search it in notification center """
    wait_element_and_send_text('//*[contains(@id, "search-input")]', "Admin")
    time.sleep(1)


def change_resp_person_limit_users():
    time.sleep(2)
    users = ['Admin', 'User 1', 'User 3']
    drop_down = choice(users)
    wait_element_and_click(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li')
    wait_element_and_send_text(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        drop_down)
    wait_element_and_send(
        '//*[@id="lead_main_user-users_select_holder"]/ul/li[2]/input',
        Keys.ENTER)
    time.sleep(1)
    wait_element_and_click('//*[@id="save_and_close_contacts_link"]/span/span')


def check_lead_for_limited(test_name):
    data = find_data_in_mongo(test_name)
    check_text_of_element('//*[contains(@title, "{}")]'.format(data['value']),
                          data['value'])


def customers_multi():
    lead = driver.find_elements_by_xpath('//*[contains(@id, "lead_")]')
    lead[6].click()
    lead[7].click()
    wait_element_and_click(
        '//*[@id="list_multiple_actions"]/div[1]/div[1]/span[1]')
    wait_element_and_click(
        '//*[contains(@id, "reassign-users_select_holder")]')
    wait_element_and_click(
        '//*[contains(@class, "multisuggest__suggest-item ' +
        'js-multisuggest-item true")]')
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept")]')


def to_list_in_card():
    wait_element_and_click('//*[contains(@title, "list")]')
    wait_element_and_click(
        '//*[contains(@class, "js-suggest_placeholder ' +
        'js-add_wrapper_text add_new_element__label")]')


def setup_leads_scoring():
    wait_element_and_click(
        '//*[contains(@class, "dp-sources__scoring-settings-button ' +
        'js-scoring-modal")]')
    time.sleep(0.5)


def leads_switch_scoring():
    # search  switcher and  auotimatic determine her status
    time.sleep(3)
    switch = driver.find_element_by_xpath('//*[contains(@id,"scoring_settings")]'
                                          '//*[contains(@class,"switcher__checkbox")]')
    if not switch.is_selected():
        wait_element_and_click('//*[contains(@for, "scoring_switcher")]')
        wait_element_and_click('//*[contains(@id, "scoring_save")]')


def leads_fill_scoring():
    wait_element_and_send_text('//*[contains(@id, "scoring_scale_max_input")]',
                               "100992")
    wait_element_and_send_text('//*[contains(@id, "scoring_scale_max_input")]',
                               "100")
    time.sleep(2)
    wait_element_and_click(
        '//*[contains(@class, "control--select--button-inner") ' +
        'and text()="Field is not selected"]')
    wait_element_and_click('//*[@id="new_score_item"]/div[2]/ul/li[2]/span')
    delete = driver.find_elements_by_xpath(
        '//*[contains(@class, "scoring_settings__score_remove-text")]')
    delete[1].click()
    wait_element_and_click('//*[contains(@id, "scoring_save")]')
    time.sleep(3)


def leads_pipeline_to_setup():
    # Leads pipeline setup
    time.sleep(2)
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and text()="Setup pipeline"]')


def to_setups_pipelines_list():
    # List of pipelines
    wait_element_and_click(
        '//*[contains(@class, "list__top__preset ' +
        'digital-pipeline__preset digital-pipeline__preset_leads-dp")]')


def new_pipeline_rename():
    # Find new (last) pipeline and rename
    wait_element_and_click('//*[@id="aside__list-wrapper"]/ul/li[last()]/span')
    wait_element_and_send_text(
        '//*[@id="aside__list-wrapper"]/ul/li[last()]/input[2]', random_data())
    wait_element_and_click(
        '//*[contains(@class, "icon icon-accept-green '
        'h-abs-position-center")]')


def new_pipeline_replace_on_top():
    # Edit pipeline -> drag -> drop on top
    time.sleep(5)
    wait_element_and_click('//*[@id="aside__list-wrapper"]/ul/li[last()]/span')
    source_element = driver.find_element_by_xpath(
        '//*[@id="aside__list-wrapper"]/ul/li[last()]/span[2]')
    destination_element = driver.find_element_by_xpath(
        '//*[@id="aside__list-wrapper"]/ul/li[1]')
    drag_and_drop(source_element, destination_element)
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "icon icon-accept-green '
        'h-abs-position-center")]')


def choose_main_pipeline():
    # Leads -> first (main)
    # Lists -> Contacts
    url = driver.current_url
    domain = url.split('/')[2]
    driver.get(f'https://{domain}/leads/pipeline/')


def to_multiple_action():
    # Leads -> first (main) pipeline ->
    # ->control button (three dots) -> Multiple actions
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner button-input-more-inner")]')
    wait_element_and_click(
        '(//*[contains(@class, "button-input__context-menu__item__icon ' +
        'svg-icon svg-common--multiactions-dims ")])[2]')


def choose_leads(n=2):
    time.sleep(0.5)
    leads_ckeckboxes = driver.find_elements_by_xpath(
        '//*[contains(@class, "pipeline_status pipeline_cell  '
        'pipeline_cell-quick_add")]//*[contains(@class, '
        '"control-checkbox pipeline_leads__lead-checkbox")]')
    for leads_checkbox in leads_ckeckboxes[:n]:
        leads_checkbox.click()


def multiactions(param):
    if param == 'reassign':
        # Reassign -> Choose another user -> Save -> Yes -> continue with crm
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions__item__icon' +
            ' icon icon-reassign")]')  # Reassign
        # Name click
        wait_element_and_click(
            '//*[contains(@class, "multisuggest users_select-select_one' +
            ' modal-reassign__users-select js-multisuggest js-can-add ")]')
        name_list = driver.find_elements_by_xpath(
            '//*[contains(@class, "multisuggest__suggest-item js-multisuggest-item")]')
        # Move to random name and click on it
        element = choice(name_list)
        ActionChains(driver).move_to_element(element).perform()
        time.sleep(1)
        element.click()
        wait_element_and_click(
            '//*[contains(@class, "button-input-inner__text")' +
            ' and contains(text(), "Save")]')
        wait_element_and_click(
            '//*[contains(@class, "button-input-inner__text")' +
            ' and contains(text(), "Yes")]')
        time.sleep(5)
        wait_element_and_click(
            '//*[contains(@title, "Changing the responsible user")]')
    elif param == 'add_task':
        # 2. Add tasks
        # Reassign -> Add to-do -> Save -> Yes -> continue with crm
        wait_element_and_click(
            '//*[contains(@class, "icon icon-clock-blue")]')  # Add to-do
        # Change time
        time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "tasks-date__caption-date")]')
        wait_element_and_click(
            '//*[contains(@class, "tasks-date__list custom-scroll")]'
            '//*[contains(@data-period, "next_week")]')
        # Reassign
        time.sleep(0.5)
        wait_element_and_click('//*[@id="modal_add_task_form"]/div[2]/button')
        manager_lists = ["Frau Amo", "Leo", "PanAmo", "Am Am Crm"]
        wait_element_and_click(
            '//*[contains(@class, "todo-form")]' +
            '//*[contains(@title, "{}")]'.format(choice(manager_lists)))
        # Change type
        wait_element_and_click(
            '//*[contains(@class, "control--select--button")' +
            ' and @data-value="1"]')
        wait_element_and_click(
            '//*[contains(@class, "control--select--list--item-inner") ' +
            'and contains(@title, "Meeting")]')
        # Type comment
        wait_element_and_send_text(
            '//*[contains(@class, "textarea-autosize")]',
            random_data())
        # Save
        wait_element_and_click(
            '//*[contains(@class, "todo-form")]' +
            '//*[contains(@class, "modal-accept")]')
        time.sleep(5)
        wait_element_and_click('//*[contains(@title, "Adding To-do")]')
    elif param == 'change_status':
        # Changing status
        wait_element_and_click('//*[contains(@data-type, "change_status")]')
        wait_element_and_click(
            '//*[contains(@class, "pipeline-select-wrapper'
            ' pipeline-select-wrapper_plain folded  ' +
            'js-control-pipeline-select control--select-white' +
            ' modal-body__inner__managers-select")]')
        try:
            # Для случая если Воронка не стоит по умлочанию
            wait_element_and_click(
                '//*[contains(@class, "custom-scroll active")]'
                '//*[contains(@class, "pipeline-select-wrapper__'
                'inner__container")]//*[@class = "pipeline-select__caption"'
                ' and @title = "Воронка"]')
        except:
            pass
        statuses = ['Переговоры', 'Принимают решение', 'Согласование договора']
        status = driver.find_element_by_xpath(
            '//*[@class = "pipeline-select__caption" and @title = "Воронка"]'
            '//parent::*//*[contains(@class, "pipeline-select__item-text")'
            ' and contains(text(), "{}")]'.format(choice(statuses)))
        wait_element_and_click(webelement=status)
        time.sleep(0.5)
        # Save
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-modal-accept")]')
        time.sleep(5)
        wait_element_and_click('//*[contains(@title, "Changing the stage")]')
    elif param == 'delete':
        # Delete leads
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions__item__icon' +
            ' icon icon-delete-trash")]')
        # Save
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-modal-accept")]')
        time.sleep(5)
        wait_element_and_click('//*[contains(@title, "Deleting elements")]')
    elif param == 'manage_tags':
        # Manage tags
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions__item__icon' +
            ' icon icon-tags")]')
        # Add tag from list
        time.sleep(0.5)
        tags = driver.find_elements_by_xpath(
            '//*[contains(@class, "modal-tags__tags-wrapper")]' +
            '//*[contains(@class, "tag")]')
        ActionChains(driver).move_to_element(tags[1]).click().perform()
        # Add new tag
        wait_element_and_send_text(
            '//*[contains(@class, "multisuggest__input' +
            ' js-multisuggest-input")]',
            random_data())
        wait_element_and_send(
            '//*[contains(@class, "multisuggest__input' +
            ' js-multisuggest-input")]',
            Keys.ENTER)
        # Save
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-modal-accept")]')
        time.sleep(5)
        wait_element_and_click('//*[contains(@title, "Editing tags")]')
    elif param == 'merge':
        # Leads merge
        wait_element_and_click(
            '//*[contains(@class, "list-multiple-actions__item__icon' +
            ' icon icon-merge-action")]')
        # Save
        wait_element_and_click(
            '//*[contains(@class, "button-input' +
            '    modal-body__actions__save js-modal-accept' +
            ' js-button-with-loader js-merge-start")]')
        time.sleep(5)
        # Continue with CRM
        wait_element_and_click('//*[contains(@title, "Performing merge")]')
    elif param == 'chat_send':
        wait_element_and_click('//*[contains(@data-type, "chat_send")]')
        wait_element_and_send_text('//*[contains(@class, "modal")]' +
                                   '//*[contains(@id, "chat_message")]',
                                   random_data())
        # Add new tag
        wait_element_and_click(
            '//*[contains(@class, "multisuggest__list-item' +
            ' js-multisuggest-item")]')
        wait_element_and_send_text(
            '//*[contains(@class, "modal-body__inner")]' +
            '//*[contains(@class, "multisuggest__input")]',
            random_data())
        wait_element_and_click(
            '//*[contains(@class, "new-tag")]')
        # Click aside
        wait_element_and_click('//*[contains(@class, "modal")]' +
                               '//*[contains(@id, "chat_message")]')
        time.sleep(0.5)
        # Checking "To all found"
        checkbox = driver.find_element_by_xpath(
            '//*[contains(@type, "checkbox") and contains(@id, "to_all")]')
        if not checkbox.is_selected():
            checkbox.click()
        else:
            pass
        # Save
        time.sleep(5)
        wait_element_and_click(
            '//*[contains(@class, "button-input    js-modal-accept")]')
        wait_element_and_click(
            '//*[@class = "modal modal-list js-modal-confirm"]' +
            '//*[contains(@class, "button-input-inner__text") ' +
            'and contains(text(), "Send")]')
        time.sleep(5)


def to_business_processes():
    """ All contacts and companies -> three dot (top right) ->
    -> business processes
    """
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner button-input-more-inner")]')
    wait_element_and_click(
        '//*[contains(@class, "element__ js-list-triggers")]')


def add_process():
    """ Add process and fill fields """
    wait_element_and_click(
        '//*[@type = "button"]//*[contains(text(), "Add process")]')
    # Choose "company is added"
    wait_element_and_click(
        '//*[contains(@class, ' +
        '"control--select trigger_settings__condition_select")]')
    wait_element_and_click('//*[@data-value = "add_company"]')
    # Change deadline "In 1 day"
    wait_element_and_click('//*[contains(@class, "deadline_select__caption")]')
    wait_element_and_click('//*[@data-deadline = "1"]')
    # Change resp user
    wait_element_and_click(
        '//*[contains(@class, "triggers_settings__responsible_select")]' +
        '//*[@type="button"]')
    wait_element_and_click('//*[@data-value = "responsible"]')
    # Change task type
    wait_element_and_click('//*[contains(@class, "task-types-holder")]' +
                           '//*[@type = "button"]')
    wait_element_and_click('//*[contains(@class, "task-types-holder")]' +
                           '//*[@data-value = "2"]')
    # Add comment
    wait_element_and_send_text('//*[contains(@class, "task-edit__textarea")]',
                               random_data())
    # Save
    wait_element_and_click(
        '//*[contains(@class, "trigger_settings__process__footer")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(2)


def add_custom_process():
    """ Add process and fill fields with custom date/task"""
    wait_element_and_click(
        '//*[@type = "button"]//*[contains(text(), "Add process")]')
    # Set custom date
    wait_element_and_click('//*[contains(@class, "deadline_select__caption")]')
    wait_element_and_send_text('//*[@name = "deadline-days"]',
                               randint(0, 99))
    wait_element_and_send_text('//*[@name = "deadline-hours"]',
                               randint(0, 23))
    wait_element_and_send_text('//*[@name = "deadline-minutes"]',
                               randint(0, 59))
    wait_element_and_click(
        '//*[contains(@class, "button-input") and contains(text(), "OK")]')
    # Create custom task
    wait_element_and_click('//*[contains(@class, "task-types-holder")]' +
                           '//*[@type = "button"]')
    wait_element_and_click('//*[contains(@class, "task-types-holder")]' +
                           '//*[@data-value = "custom"]')
    wait_element_and_send_text('//*[@name = "task_type_name"]', random_data())
    # Add comment
    wait_element_and_send_text('//*[contains(@class, "task-edit__textarea")]',
                               random_data())
    # Save
    wait_element_and_click(
        '//*[contains(@class, "trigger_settings__process__footer")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(2)


def edit_buisness_process():
    """ Select first created buisness process and edit """
    # Mouse to three dots at created bp
    mouse_to_element('//*[contains(@class, "icon icon-inline icon-v-dots-2")]')
    wait_element_and_click(
        '//*[contains(@class, "icon icon-inline icon-v-dots-2")]')
    # Click on edit button
    wait_element_and_click('//*[contains(@class, "note-actions__btn-edit")]')
    # Change resp user
    wait_element_and_click(
        '//*[contains(@class, "triggers_settings__responsible_select")]' +
        '//*[@type="button"]')
    wait_element_and_click('//*[@data-value = "responsible"]')
    # Change comment
    wait_element_and_send_text('//*[contains(@class, "task-edit__textarea")]',
                               random_data())
    wait_element_and_click(
        '//*[contains(@class, "trigger_settings__process__footer")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(2)
    wait_element_and_click(
        '//*[contains(@class, "button-input") and contains(text(), "Close")]')
    time.sleep(1)


def delete_buisness_processes():
    """ Delete all created buisness processes """
    xpath = \
        '//*[contains(@class, "trigger_settings__process read_mode inited")]'
    buissnes_processes = driver.find_elements_by_xpath(xpath)
    if len(buissnes_processes) > 0:
        for _ in buissnes_processes:
            mouse_to_element(
                '//*[contains(@class, "icon icon-inline icon-v-dots-2")]')
            wait_element_and_click(
                '//*[contains(@class, "icon icon-inline icon-v-dots-2")]')
            wait_element_and_click(
                '//*[contains(@class, "icon icon-delete-trash")]')
            time.sleep(0.5)
            wait_element_and_click('//*[contains(text(), "Yes")]')
            time.sleep(1)
        # Click aside
        wait_element_and_click(
            '//*[contains(@class, "list__body-right__top")]')
        time.sleep(1)
    else:
        raise Exception(
            "Can't find any buisness process! " +
            "Check xpath or buisness processes existence")


def add_new_source():
    """ Click on "Add source" in leads settings """
    time.sleep(5)
    wait_element_and_click('//*[contains(@class, "add-new-source")]')
    time.sleep(3)


def connect_chats():
    """ Connect list of chats as new source """
    # click connect chat
    wait_element_and_click('//*[contains(@class, "connect-chat")]')
    time.sleep(1)
    # List of chats
    if ServerType == 'PROD_USA':
        chat_list = ['Facebook',
                     'Olark',
                     'Telegram',
                     'Viber',
                     ]
    else:
        chat_list = ['Facebook',
                     'Вконтакте',
                     'Jivosite',
                     'Оларк',
                     'Telegram',
                     'Viber',
                     ]
    # Remember current tab
    main_tab = driver.current_window_handle
    # Connect each chat
    for chat in chat_list:
        wait_element_and_click(
            '//*[contains(@class, "chats-integrations-list__link") ' +
            'and contains(text(), "{}")]'.format(chat))
        time.sleep(1)
        if chat in ['Facebook', 'Вконтакте']:
            # In these cases it is necessary to go back to main tab
            driver.switch_to.window(main_tab)
        elif chat in ['Оларк', 'Olark']:
            # Click on the bottom of opened spase
            wait_element_and_click(
                '//*[contains(@class, "olark")]' +
                '//*[contains(@class, "chats-integrations-list__header")]')
            time.sleep(0.5)
            wait_element_and_click(
                '//*[contains(@class, "olark")]' +
                '//*[contains(@class, "connect-inner")]')
        else:
            # In other cases it is necessary to turn off opened space
            # but for 'Jivosite' also need:
            if chat == 'Jivosite':
                # Click on registration button
                wait_element_and_click(
                    '//*[contains(@class, "ivosite_settings")]' +
                    '//*[contains(@class, "button-input-inner")]')
                time.sleep(0.5)
                wait_element_and_click(
                    '//*[contains(@class, "jivosite")]' +
                    '//*[contains(@class, "chats-integrations-list__header")]')
            wait_element_and_click(
                '//*[contains(@class, "chats-integrations-list__link") ' +
                'and contains(text(), "{}")]'.format(chat))
    # Click aside
    wait_element_and_click('//*[@class = "dp-sources"]')


def connect_chats_fixed():
    # Connect facebook
    # //*[@data-name="facebook"]//*[text()="Add source"]
    # //*[@data-name="vk"]//*[text()="Add source"]
    # //*[@data-name="telegram"]//*[text()="Add source"]
    # //*[@data-name="instagram"]//*[text()="Add source"]
    # //*[@data-name="viber"]//*[text()="Add source"]
    # //*[@data-name="bf.skype"]//*[text()="Add source"]
    # Install - Installed - Close
    # Then delete them in sources
    # widget-state__name

    def install_check_uninstall(widget_name):
        add_new_source()
        wait_element_and_click(f'//*[@data-name="{widget_name}"]//*[text()="Add source" or text()="Добавить"]')
        time.sleep(0.5)
        try:
            driver.find_element_by_xpath('//*[@class="widget-state__name"][text()="installed" or text()="Установлено"]')
            wait_element_and_click('//*[contains(@class, "button-input button-cancel js-widget-uninstall")]')
        except exceptions.NoSuchElementException:
            pass

        wait_element_and_click('//*[contains(@class, "dp-sources__button-add dp-sources__button-add_active")]')
        try:
            time.sleep(1)
            driver.find_element_by_xpath('//*[@class="widget-state__name"][text()="installed" or text()="Установлено"]')
        except exceptions.NoSuchElementException:
            raise WidgetInstallError("Something went wrong when install button pressed")
        finally:
            wait_element_and_click('//*[contains(@class, "button-input button-cancel js-widget-uninstall")]')
            time.sleep(0.5)
            wait_element_and_click('//*[contains(@class, "modal-body__close")]')

    install_check_uninstall('telegram')
    install_check_uninstall('instagram')
    install_check_uninstall('viber')
    install_check_uninstall('bf.skype')
    install_check_uninstall('avito')
    install_check_uninstall('wechat')


def connect_sms_ru():
    """ Add source -> Click on SMS.ru -> jump to integration"""
    try:
        wait_element_and_click('//*[text()="Установить"]')
        time.sleep(2)
    except exceptions.NoSuchElementException:
        raise SMSWidgetError("There is no SMS widget install button, mb it's deprecated")


def reason_for_close_lost_switcher(param):
    """ Switch-on/off Close-Lost leads switcher and Save"""
    time.sleep(1)
    checkbox = driver.find_element_by_xpath(
        '//*[contains(@name , "enable_loss_reasons")]')
    if (param == 'on' and not checkbox.is_selected()) or \
            (param == 'off' and checkbox.is_selected()):
        wait_element_and_click(
            '//*[contains(@for, "loss_reasons_switcher")]')
        wait_element_and_click(
            '//*[contains(@class, "list__top__actions")]' +
            '//*[contains(text(), "Save")]')
        time.sleep(0.5)


def add_a_reason(test_name):
    """ Add a reason and save it name in MongoDB """
    # Click on Setup in loss reason tab
    wait_element_and_click(
        '//*[contains(@class, " digital-pipeline__item_loss-reason")]'
        '//*[contains(@class, "loss-reasons__settings")]')
    # Click on add a reson
    wait_element_and_click('//*[@title = "Add a reason"]')
    # type resason
    reason = random_data()
    name = random_data()
    save_data_to_mongo(test_name,
                       {'reason': reason,
                        'name': name, })
    time.sleep(0.5)
    add_field = driver.find_element_by_xpath(
        '//*[contains(@class, "dp-leads-loss-reasons__item js-item' +
        ' dp-leads-loss-reasons__item_no-sort")]')
    ActionChains(driver).move_to_element(add_field).send_keys(reason).perform()
    # Save
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Save")]')
    time.sleep(0.5)


def select_reason_lost(test_name):
    """ Select created reason and save """
    data = find_data_in_mongo(test_name)
    wait_element_and_click('//*[@title = "{}"]/div'.format(data['reason']))
    time.sleep(0.5)
    # Save
    wait_element_and_click('//*[contains(@class, "button-input-inner__text")' +
                           'and contains(text(), "Save")]')
    time.sleep(2)


def create_closed_lead(test_name, with_reason=False):
    """ Create a new lead and close it with created reason """
    # Name
    wait_element_and_click('//*[contains(@placeholder, "Lead #XXXXXX")]')
    data = find_data_in_mongo(test_name)
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Lead #XXXXXX")]', data['name'])
    time.sleep(0.5)
    # Select "Закрыто и не реализовано"
    wait_element_and_click(
        '//*[contains(@class, "control--select--button-colored")]')
    wait_element_and_click('//*[contains(@class, "card-entity-form__top")]' +
                           '//*[contains(@title, "Закрыто и не реализовано") '
                           '' +
                           'or contains(@title, "Closed - lost")]')
    if with_reason:
        # Select createrd reason
        data = find_data_in_mongo(test_name)
        wait_element_and_click('//*[@title = "{}"]/div'.format(data['reason']))
        time.sleep(0.5)
    # Save
    wait_element_and_click(
        '//*[contains(@class, "card-fields__button-block")]' +
        '//*[contains(text(), "Save")]')


def filter_lost_leads(test_name, with_reason=False):
    """ Select lost leads in search
    Parameters:
    :with_reason - bool, additionally select current reason in search options
    """
    # Search
    wait_element_and_click(
        '//*[contains(@class, "list-top-search__input-wrapper")]')
    time.sleep(0.5)
    # Selecr lost leads
    wait_element_and_click('//*[contains(text(), "Lost leads")]')
    time.sleep(1)
    if with_reason:
        # Click on search
        wait_element_and_click(
            '//*[contains(@class, "list-top-search__input-wrapper")]')
        time.sleep(0.5)
        # Select reason in list
        wait_element_and_click(
            '//*[contains(@class, "loss-reasons")]' +
            '//*[@class =  "checkboxes_dropdown__title"]')
        # Load data from mongo
        data = find_data_in_mongo(test_name)
        # Click on the reason
        wait_element_and_click('//*[@title = "{}"]'.format(data['reason']))
        # Apply
        wait_element_and_click(
            '//*[contains(@class, "button") ' +
            'and contains(text(), "Apply")]')
        time.sleep(1)
    # Assertion
    data = find_data_in_mongo(test_name)
    lead = driver.find_element_by_xpath(
        '//*[@title = "{}"]'.format(data['name']))
    assert lead.text == data['name']


def to_all_contacts_and_companies():
    """ Click on lists """
    wait_element_and_click(
        '//*[contains(@class, "nav__menu__item__icon")][contains(@class, "icon-catalogs")]')


def create_closed_contact(test_name):
    """ Create a new contact and close it with created reason """
    # add contact
    wait_element_and_click(
        '//*[contains(text(), "Add contact")]')
    # Contact name
    wait_element_and_click('//*[contains(@placeholder, "Full name")]')
    data = find_data_in_mongo(test_name)
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Full name")]', data['name'])
    time.sleep(0.5)
    # Save
    wait_element_and_click(
        '//*[contains(@class, "card-fields__button-block")]' +
        '//*[contains(text(), "Save")]')
    # To leads ( local submenu )
    wait_element_and_click(
        '//*[contains(@class, "card-tabs")]//*[@title="Leads"]')
    time.sleep(0.5)
    # Quick add
    wait_element_and_click(
        '//*[contains(@class, "pipeline_leads__quick_add_button_inner")]')
    # Lead name
    wait_element_and_send_text('//*[@id = "quick_add_lead_name"]',
                               random_data())
    # Change stage to - Закрыто и нереализовано
    wait_element_and_click(
        '//*[contains(@class, "pipeline_leads__quick_statuses_button")]')
    wait_element_and_click(
        '//*[contains(@class, "pipeline_leads__quick_add_form_inner")]' +
        '//*[contains(@title, "Закрыто и не реализовано") ' +
        'or contains(@title, "Closed - lost")]')
    time.sleep(1)
    # Select created reason for close
    data = find_data_in_mongo(test_name)
    wait_element_and_click(
        '//*[contains(@class, "modal-loss-reason")]' +
        '//*[@title = "{}"]'.format(data['reason']))
    time.sleep(1)
    # Save reason
    wait_element_and_click(
        '//*[contains(@class, "modal-body__actions_loss-reason")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(0.5)
    # Save lead changes
    wait_element_and_click(
        '//*[contains(@class, "pipeline_leads__quick_add_form")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(1)


def to_leads():
    """ Click on Leads button """
    wait_element_and_click('//*[contains(@class, "icon-leads")]')


def del_reason_for_close_lost_leads():
    """ Delete last reason for close-lost leads """
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, " digital-pipeline__item_loss-reason")]'
        '//*[contains(@class, "loss-reasons__settings")]')
    time.sleep(1)
    reasons = driver.find_elements_by_xpath(
        '//*[contains(@class, "dp-leads-loss-reasons__items")]//*[contains(@class, "svg-icon svg-common--trash-dims")]')
    if len(reasons) > 0:
        for _ in reasons:
            wait_element_and_click(
                '//*[contains(@class, "dp-leads-loss-reasons__item-remove '
                'js-item-remove")]'
                '[last()]//*[contains(@class, "svg-icon '
                'svg-common--trash-dims")]')
    wait_element_and_click(
        '//*[contains(@class, "list__top__actions")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(0.5)


def contact_check_existance_status_msg():
    """ Check existance of created closed lead from contact card """
    # Go to submenu Lead
    wait_element_and_click('//*[contains(@class, "card-tabs__item-inner")' +
                           'and @title = "Leads"]')
    time.sleep(0.5)
    # Go to closed lead card
    wait_element_and_click('//*[@class = "card-leads__won-lost__body__item"]')
    time.sleep(1)
    # Check existance of status message
    msg = driver.find_element_by_xpath(
        '//*[contains(@class, "closed-status-msg")]')
    if not msg.is_displayed():
        raise Exception('There is no status message at the bottom of note!')


def select_chat_in_card():
    """ Select chat in feed """
    time.sleep(1)
    mouse_to_element('//*[@class = "feed-compose-switcher"]')
    time.sleep(0.5)
    wait_element_and_click('//*[@data-id = "chat"]')
    time.sleep(0.5)


def send_message_to(stand, account):
    """ Send message to preassigned account """
    # Get account email adress
    with open('settings.yml') as auth_pair:
        pair = yaml.load(auth_pair)
    account = pair['auth'][ServerType][stand][account]
    # Type email
    wait_element_and_click(
        '//*[contains(@class, "feed-compose-user__name")]')
    wait_element_and_send_text(
        '//*[contains(@class, "multisuggest__input js-multisuggest-input")]',
        account)
    # Click on user
    wait_element_and_click(
        '//*[contains(@class, "users-select__body__item")]')
    time.sleep(0.5)


def to_message(test_name=None, unread=False):
    """ Select message in Notification Center
    Parameters:
    :test_name - using test_name as a key in MongoDB collection to find
                 the right message
    :unread - select last unread message"""
    time.sleep(0.5)
    if test_name:
        data = find_data_in_mongo(test_name)
        wait_element_and_click(
            '//*[contains(@class, "notification__item")]'
            '//*[contains(text(), "{}")]'.format(data['value']))
    elif unread:
        try:
            wait_element_and_click(
                '//*[contains(@class, "notification__item__unread")]')
        except:
            raise Exception('There is no unread messages!')
    else:
        # just last message
        wait_element_and_click(
            '//*[contains(@class, "notification-inner__title_message")]')
    time.sleep(0.5)


def select_admin_by_click_on_message():
    """ Click on admin name in first admin's message """
    wait_element_and_click(
        '//*[contains(text(), "Today")]/parent::*' +
        '//*[contains(@class, "feed-note__amojo")' +
        ' and contains(text(), "admin_for_free")]')


def delete_pipelines():
    """ Delete all created pipeline """
    # Checking existence of unused pipelines
    time.sleep(0.5)
    pipelines = driver.find_elements_by_xpath(
        '//*[contains(@class, "aside__list-item-link")]')
    # standart pipelines: Воронка, New pipeline and All leads
    if len(pipelines) > 2:
        # Create list with names of pipelines
        pipelines_names = []
        for pipeline in pipelines:
            pipelines_names.append(pipeline.text)
        # Going to setup pipeline and delete trash pipelines
        all_leads()
        refresh_page()
        leads_pipeline_to_setup()
        # Getting list of pipeline names
        for pipeline in pipelines_names:
            if pipeline not in ['Воронка', 'New pipeline', 'All leads']:
                to_setups_pipelines_list()
                # Addititonal xpath for searching current pipeline name
                add_xpath = ('//a[contains(@class, "aside__list-item-link") '
                             'and contains(text(), "{}")]'.format(pipeline) +
                             '/ancestor::*[contains(@class, '
                             '"aside__list-item")]')
                wait_element_and_click(
                    add_xpath + '/*[contains(@class, "icon-pencil")]')
                time.sleep(0.2)
                wait_element_and_click(
                    add_xpath + '//*[@data-action ="remove"]')
                time.sleep(0.5)
                # Confirm
                wait_element_and_click(
                    '//*[contains(@class, "button-input") ' +
                    'and contains(text(), "Confirm")]')
                wait_element_and_click('//*[contains(@class, "button-input") and contains(text(), "Save")]')
                refresh_page()
        # Click on back button
        wait_element_and_click(
            '//*[contains(@class, "digital-pipeline__back-button")]')
        time.sleep(0.5)


def input_password(stand, new_password=False, same_passwords=True):
    """ This function fill password field in profile settings
    Parameters:
    :cmdopt - stand
    :new_password - use new password for account. Use reverse standart password
    :same_passwords - use the same passwords for both field.
    """
    # Standart password
    with open('settings.yml') as auth_pair:
        pair = yaml.load(auth_pair)
    password = pair['auth'][ServerType][stand]['password']
    if new_password:
        password = password[::-1]
    # Type passwords in fields
    wait_element_and_send_text(
        '//*[@name = "NEW_PASSWORD"]',
        password)
    # Confirmation fields
    if same_passwords:
        wait_element_and_send_text(
            '//*[@name = "NEW_PASSWORD_CONFIRM"]',
            password)
    else:
        wait_element_and_send_text(
            '//*[@name = "NEW_PASSWORD_CONFIRM"]',
            'WrongPasswordSTR')
    time.sleep(0.5)


def change_password(stand, new_password=False):
    """ Change current account password
    Parameters:
    :stand - str, stage
    :new_password - bool, if True type new password for account
                             False use standart password"""
    time.sleep(1)
    # Type password in fields
    input_password(stand, new_password)
    # Save
    wait_element_and_click('//*[contains(@id, "save_profile_settings")]')
    time.sleep(2)


def replace_lead_to_conversation(test_name):
    """ Drag lead and drop it at the "Переговоры" stage
    Parameter:
    :test_name - name of test used as a key in MongoDB collection;
    """
    # Find name in MongoDB collection
    data = find_data_in_mongo(test_name)
    lead_name = data['value']
    # Find source element - created lead
    source_element = driver.find_element_by_xpath(
        '//*[@title = "{}"]'.format(lead_name))
    # Find destination element - first lead in column "Переговоры"
    destination_element = driver.find_element_by_xpath(
        '//*[contains(@class, "pipeline_cell")]' +
        '//*[@title = "Переговоры"]/ancestor::*' +
        '[contains(@class, "pipeline_status pipeline_cell")]' +
        '//*[@class ="pipeline_leads__lead-title"]')
    # Drag'n'Drop
    time.sleep(0.5)
    drag_and_drop(source_element, destination_element)
    time.sleep(4)


def click_on_push_lead(test_name):
    """ Click on push after replace lead in "Переговоры" stage
    also check changes in notification center counter
    """
    time.sleep(1)
    counter_before_push = int(driver.find_element_by_xpath(
        '//*[contains(@class, "inbox-counter")]').text)
    # wait for a push
    time.sleep(1)
    # load data from mongo DB
    data = find_data_in_mongo(test_name)
    lead_name = data['value']
    try:
        wait_element_and_click(
            '//*[contains(@class, "notification-inner__title_message") '
            'and contains(text(), "{}")]'.format(lead_name))
    except exceptions.NoSuchElementException:
        assert 'This is bug' == 'Is it fixed?', 'Troubles with pushs'
    time.sleep(1)
    counter_after_push = driver.find_element_by_xpath(
        '//*[contains(@class, "inbox-counter")]').text
    if counter_after_push == '':
        counter_after_push = 0
    else:
        counter_after_push = int(counter_after_push)
    assert counter_before_push == counter_after_push + 1
    time.sleep(1)


def to_notification_center():
    """ Click on notification center """
    wait_element_and_click('//*[contains(@class, "icon-notifications")]')


def complete_task_in_cn(test_name):
    """ Mouse to task from test_name collection in MongoDB and complete it"""
    data = find_data_in_mongo(test_name)
    mouse_to_element(
        '//*[contains(@class, "notification-inner__title_message") ' +
        'and contains(text(), "{}")]'.format(data['value']))
    time.sleep(0.5)
    # Click on three dots near to-do
    wait_element_and_click('//*[contains(@class, "notification__item")]' +
                           '//*[contains(text(), "{}")]/../../..//*[contains(@class, "svg-controls--button-more-dims")]'.format(
                               data['value']))
    # Complete from notifications
    wait_element_and_click(
        '(//*[contains(@class, "notification-quick-action__menu")]//*[contains(text(), "Complete")])[last()]')
    time.sleep(0.5)
    wait_element_and_send_text('//*[contains(@id, "modal_todo_result")]',
                               random_data())
    wait_element_and_click(
        '//*[contains(@class, "modal-body__actions ")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(0.5)


def sort_by_creation_date():
    """ Click on sort by creation date """
    time.sleep(0.5)
    # Three dots
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner button-input-more-inner")]')
    time.sleep(0.5)
    # Click on "By creation date" in the case if sorting not set
    xpath = ('//*[contains(@data-sort-type, "desc") '
             'and contains(@data-sort-by, "date_create")]')
    if driver.find_element_by_xpath(xpath):
        # sorting is ok, so click aside
        wait_element_and_click(
            '//*[contains(@class, "button-input-more-inner")]')
    else:
        wait_element_and_click(
            '//*[contains(text(), "By creation date")]')
    time.sleep(0.5)


def delete_task_in_card(delete=True):
    """ Click on task in card and then click on delete
    Parameters:
    :delete - bool, if True  - click "Yes" in modal window,
                       False - click no in modal window
    """
    time.sleep(0.5)
    # Select task in card
    wait_element_and_click('//*[contains(@class, "card-task__icon")]')
    # Click on Delete
    wait_element_and_click(
        '//*[contains(@class, "card-task")]' +
        '//*[contains(@class, "button_remove")]')
    if delete:
        # Clcik Yes
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]'
            '//*[contains(@class, "button")]//*[contains(text(), "Yes")]')
        time.sleep(1)
    else:
        # Click No
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]'
            '//*[contains(@class, "button")]//*[contains(text(), "No")]')
        time.sleep(0.5)


def add_todo_in_card(test_name=None):
    """
    Adding to-do in card
    :param test_name: name of test where function was called. Used to save data in DB
    :type test_name: str
    """
    time.sleep(0.5)
    mouse_to_element(
        '//*[contains(@class, "feed-compose__message-wrapper")]' +
        '//*[@class ="feed-compose-switcher"]')
    time.sleep(0.5)
    # select to-do
    wait_element_and_click('//*[@data-id = "task"]')
    # Write a commnet
    comment = random_data()
    wait_element_and_click(
        '//*[contains(@class, "control-contenteditable__area")]')
    wait_element_and_send(
        '//*[contains(@class, "control-contenteditable__area")]',
        comment)
    # click set
    time.sleep(0.2)
    wait_element_and_click('//*[contains(@class, "js-task-submit")]')
    time.sleep(0.5)
    if test_name:
        save_data_to_mongo(test_name, {'comment': comment})


def check_todo_in_card(test_name, only_name=False):
    """ Check comment changes in to-do in card """
    data = find_data_in_mongo(test_name)
    if only_name:
        new_todo = driver.find_element_by_xpath(
            '//div[contains(@class, '
            '"card-task__inner-content")]/p').text.split()[
            -1]
        assert data['comment'] == new_todo
    else:
        # Check comment changes
        wait_element_and_click(
            '//*[contains(@class, "card-task")]' +
            '//*[contains(text(), "{}")]'.format(data['comment']))
        time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "card-task__inner")]' +
            '//*[contains(text(), "{}")]'.format(data['comment']))
        time.sleep(0.5)
        new_comment = random_data()
        # clear element
        driver.find_element_by_xpath(
            '//*[contains(@class, "js-control-contenteditable ' +
            'control-contenteditable card-task__actions")]/div[2]').clear()
        wait_element_and_send(
            '//*[contains(@class, "js-control-contenteditable ' +
            'control-contenteditable card-task__actions")]/div[2]',
            new_comment)
        # Click on edit
        time.sleep(0.2)
        wait_element_and_click('//*[contains(@class, "js-task-submit")]')
        # Check changes
        refresh_page()
        card_task = driver.find_element_by_xpath(
            '//*[contains(@class, "card-task")]' +
            '//*[contains(text(), "{}")]'.format(new_comment))
        assert 'Follow-up — ' + new_comment == card_task.text


def preset_cleaner():
    """ Open search tab and delete custom search presets """
    click_on_search_and_filter()
    # Specify preset xpath
    xpath_pres = ('//*[contains(@class, "animated") and '
                  'contains(@class, "filter__list__item")]'
                  '//*[contains(@class, "pencil")]')
    time.sleep(1)
    # Delete all presets (if they exist)
    for _ in range(len(driver.find_elements_by_xpath(xpath_pres))):
        wait_element_and_click(xpath_pres)
        time.sleep(0.2)
        wait_element_and_click(
            '//*[contains(@class, "filter_items__edit__delete")]')
        time.sleep(0.2)
        wait_element_and_click(
            '//*[contains(@class, "button") and contains(text(), "Confirm")]')
        time.sleep(0.5)
    # Close search
    wait_element_and_click(
        '//*[contains(@class, "list__top__actions")]'
        '//*[contains(@class, "button-more-dims")]')


def get_subdomain():
    """ This function return a account subdomain """
    return driver.current_url.split('/')[2].split('.')[0]


def last_message():
    """ Select  last (unread) message in list """
    wait_element_and_click(
        '//*[contains(@class, "notification__item__unread")]')
    time.sleep(1)


def get_api_key(test_name):
    """ Get api key from profile and save it in MongoDB.
    Also save subdomain and  login (email)
    :test_name - collection key as a key in MongoDB
    """
    time.sleep(2)
    # getting api key
    api_key = driver.find_element_by_xpath(
        '//*[contains(@class, "js-user_profile__data__api_key")]').text
    # getting subdomain
    subdomain = get_subdomain()
    # getting login
    login = driver.find_element_by_xpath(
        '//*[contains(@class, "user-profile__table_inputs")]' +
        '//input[contains(@name, "LOGIN")]').get_attribute('value')
    save_data_to_mongo(test_name, {'api_key': api_key,
                                   'subdomain': subdomain,
                                   'login': login})


def update_data_in_mongo(collection_name, data):
    """ This function can update/append data to created mongo collection
    Parameters:
    :collection_name - collection name (usually test name)
    :data - dict, dictionary with data to append or update.
    if key exist this fucntion update data - {'existing_key': 'new_value'})
    else this function append data - {'new_key': 'new_value'})
    It is possible to combine that cases:
        update_data_in_mongo('collection_name',
                            {'new_key': 'new_value',
                             'existing_key': 'new_value'})
    """
    client = MongoClient('mongo', 27017)
    db = client['selenium_tests']
    try:
        db[collection_name].update_one(find_data_in_mongo(collection_name),
                                       {'$set': data})
    except:
        raise MyException(
            "Can't find '{}' mongo collection".format(collection_name))
    finally:
        client.close()


def api_add_lead(test_name):
    """ Add lead with contact and company by using AmoCRM api
    Parameters:
    :test_name - collection key as a key in MongoDB
    """
    # Load data from mongo
    data = find_data_in_mongo(test_name)
    # Create AmoSession object
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType,
                             password=None)
    amo_session.create_session()
    # 1. Create company
    company_name = random_data()
    # Add company by API and save response
    response_company = amo_session.add_company_contact(entity_type='company',
                                                       name=company_name)
    # get company id from request response
    company_id = response_company['_embedded']['items'][0]['id']
    # 2. Create contact
    contact_name = random_data()
    # Add contact by API and save response
    response_contact = amo_session.add_company_contact(entity_type='contact',
                                                       name=contact_name)
    # get contact id from request response
    contact_id = response_contact['_embedded']['items'][0]['id']
    # 3. Create lead
    lead_name = random_data()
    # 4. Generate tags
    tags = [random_data() for _ in range(2)]
    # 5. Sale
    sale = randint(1, 10 ** 6)
    # Add contact by API and save response
    response_lead = amo_session.add_lead(lead_name=lead_name,
                                         company_id=company_id,
                                         contact_id=contact_id,
                                         tags=tags)
    # get company id from request response
    lead_id = response_lead['_embedded']['items'][0]['id']
    # Append data to mongo
    update_data_in_mongo(test_name,
                         {'lead_name': lead_name,
                          'lead_id': lead_id,
                          'company_name': company_name,
                          'company_id': company_id,
                          'contact_name': contact_name,
                          'contact_id': contact_id,
                          'tags': tags,
                          'sale': sale,
                          })


def api_add_customer(test_name, responsible_user=False,
                     expected_amount=None, init_session=True,
                     tags=None):
    """ Add customer by using AmoCRM api
    Parameters:
    :test_name - collection key as a key in MongoDB
    :responsible_user - bool, if True than add to customer responsible user
    :excepted_amount - int, sum of excepted amount
    :init_session - bool, if True than create new amo session
                          elif False than use saved cookie
    :tags - list, list of tags to add
    """
    # Load data from mongo
    data = find_data_in_mongo(test_name)
    # Create AmoSession object
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType,
                             password=None)
    if init_session:
        amo_session.create_session()
    # Create customer
    customer_name = random_data()
    # Check responsible_user_id argument
    if responsible_user:
        # load id from mongo
        responsible_user_id = data['responsible_user_id']
    else:
        responsible_user_id = None
    # Add contact by API and save response
    response_customer = amo_session.add_customer(
        customer_name=customer_name,
        responsible_user_id=responsible_user_id,
        expected_amount=expected_amount,
        tags=tags)
    # get company id from request response
    customer_id = response_customer['_embedded']['items'][0]['id']
    # Append data to mongo
    update_data_in_mongo(test_name,
                         {'customer_name': customer_name,
                          'customer_id': customer_id,
                          'responsible_user_id': responsible_user_id,
                          'expected_amount': expected_amount,
                          'tags': tags,
                          })


def api_update_lead(test_name):
    """ Update lead content by using AmoCRM api
    Parameters:
    :test_name - collection key as a key in MongoDB
    """
    # Load data from mongo
    data = find_data_in_mongo(test_name)
    # Create AmoSession object
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType)
    # Update lead name
    new_lead_name = random_data()
    amo_session.update_entity(entity_type='lead',
                              entity_id=data['lead_id'],
                              new_name=new_lead_name)
    # Update data in mongo
    update_data_in_mongo(test_name, {'lead_name': new_lead_name})


def api_update_contact(test_name):
    """ Update contact name by using AmoCRM api
    Parameters:
    :test_name - collection key as a key in MongoDB
    """
    # Load data from mongo
    data = find_data_in_mongo(test_name)
    # Create AmoSession object
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType)
    # Update contact name
    new_contact_name = random_data()
    amo_session.update_entity(entity_type='contact',
                              entity_id=data['contact_id'],
                              new_name=new_contact_name)
    # Update data in mongo
    update_data_in_mongo(test_name, {'contact_name': new_contact_name})


def api_update_company(test_name):
    """ Update company name by using AmoCRM api
    Parameters:
    :test_name - collection key as a key in MongoDB
    """
    # Load data from mongo
    data = find_data_in_mongo(test_name)
    # Create AmoSession object
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType)
    # Update company name
    new_company_name = random_data()
    amo_session.update_entity(entity_type='company',
                              entity_id=data['company_id'],
                              new_name=new_company_name)
    # Update data in mongo
    update_data_in_mongo(test_name, {'company_name': new_company_name})


def search_suggest_in_lead(test_name, go_to_card=True, old_entity=False):
    """ Find lead/contact/company by suggesting search
    Parameters:
    :test_name - collection key as a key in MongoDB;
    :go_to_card - bool, if True then click on entity and go to card
                        else just check entity exist
    :old_entity - bool, if True then search old (prepared) entities
                         else search created entities
    """
    data = find_data_in_mongo(test_name)
    # list of entities ( need for xpath )
    entities = ['Current', 'Contacts', 'Companies']
    # list of list names ( each element is a key in mongo data )
    entity_name_list = ['lead_name', 'contact_name', 'company_name']
    # List of old entities (check old entity searching )
    old_entity_list = [
        'TEST_SUGGEST_SEARCH_LEAD',
        'TEST_SUGGEST_SEARCH_CONTACT',
        'TEST_SUGGEST_SEARCH_COMPANY',
    ]
    # Check old_entity argument - if true then search prepared entities
    if old_entity:
        entity_list = old_entity_list
    else:
        # Generate entity_list by getting data from mongo collection
        entity_list = []
        for entity_name in entity_name_list:
            entity_list.append(data[entity_name])
    # Dashboard search lead/contact/company
    for entity, entity_name in zip(entities, entity_list):
        # Send enssence name to search tab
        wait_element_and_send_text(
            '//input[contains(@class, "list-top-search__input")]',
            entity_name,
            with_assert=False)
        # Creating essnece xpath
        xpath = ('//*[contains(@class, "search-results__row-section")]'
                 '//*[contains(text(), "{}")]/parent::*'.format(entity) +
                 '//*[contains(text(), "{}")]'.format(entity_name))
        # Checking go_to_card parameter
        if go_to_card:
            wait_element_and_click(xpath)
            back_button()
        else:
            time.sleep(3)
            # Check that the element exist
            assert len(driver.find_elements_by_xpath(xpath)) > 0
            wait_element_and_click('//*[contains(@id, "search_clear_button")]')


def delete_cookies(test_name):
    """ Delete AmoSession coockies file """
    data = find_data_in_mongo(test_name)
    print('data', data)
    os.remove(data['cookies_filename'])


def dashboard_search(test_name, go_to_card=True, old_entity=False):
    """ Find lead/contact/company by dashboard search
    Parameters:
    :test_name - collection key as a key in MongoDB;
    :go_to_card - bool, if True then click on entity and go to card
                        else just check entity exist
    :old_entity - bool, if True then search old (prepared) entities
                         else search created entities
    """
    data = find_data_in_mongo(test_name)
    # list of list names ( each element is a key in mongo data )
    entity_name_list = ['lead_name', 'contact_name', 'company_name']
    # List of old essenses (check old entity searching )
    old_entity_list = [
        'TEST_SUGGEST_SEARCH_LEAD',
        'TEST_SUGGEST_SEARCH_CONTACT',
        'TEST_SUGGEST_SEARCH_COMPANY',
    ]
    # Check old_entity argument - if true then search prepared entities
    if old_entity:
        entity_list = old_entity_list
    else:
        # Generate entity_list by getting data from mongo collection
        entity_list = []
        for entity_name in entity_name_list:
            entity_list.append(data[entity_name])
    # Dashboard search lead/contact/company
    for entity_name in entity_list:
        # Send enssence name to search tab
        wait_element_and_send_text(
            '//input[contains(@class, "list-top-search__input")]',
            entity_name,
            with_assert=False)
        # Xpath prefix ( Different for leads and contacts/companies )
        if entity_name in [data['lead_name'], 'TEST_SUGGEST_SEARCH_LEAD']:
            xpath = ('//*[contains(@id, "search-suggest-drop-down-menu_container")]'
                     '//*[contains(@class, "search-results__row-section")]')
        else:
            xpath = ('//*[contains(@id, "search-suggest-drop-down-menu_container")]'
                     '//*[contains(@class, "search-results__row-section")]')
        # Xpath end part
        xpath += '//*[contains(text(), "{}")]'.format(entity_name)
        # Checking go_to_card parameter
        if go_to_card:
            time.sleep(4.5)
            wait_element_and_click(xpath)
            back_button()
        else:
            time.sleep(4.5)
            # Check that the element exist
            assert len(driver.find_elements_by_xpath(xpath)) > 0
            wait_element_and_click('//*[contains(@id, "search_clear_button")]')
            time.sleep(1)


def add_webform():
    """ Add webform in pipeline settings """
    # Click add webform
    wait_element_and_click(
        '//*[contains(@class, "modal-dp-item__button-add") ' +
        'and contains(@class, "amoforms")]')
    time.sleep(1)


def webform_save():
    """ Save changes in webform """
    wait_element_and_click(
        '//*[contains(@class, "amoforms__header-buttons")]' +
        '//*[contains(@class, "button") and contains(text(), "Save")]')
    time.sleep(2)


def add_fields_in_webform(test_name):
    """ Add field to webform
    Parameters:
    :test_name - name of test used as a key in MongoDB collection;
    """
    # Count field at webform
    counter = len(driver.find_elements_by_xpath(
        '//*[contains(@class, "amoforms__fields__container ")]'))
    # Add fields to webform (Drag field and drop to webform tab)
    dest = driver.find_element_by_xpath(
        '//*[contains(@class, "amoforms__fields__editor ")]' +
        '//*[contains(@class, "fields-sortable ui-sortable")]')
    for entity in ['Leads', 'Contacts', 'Companies']:
        # click on entity
        wait_element_and_click(
            '//*[contains(@class, "amoforms__sidebar__header") ' +
            'and contains(text(), "{}")]'.format(entity))
        time.sleep(0.2)
        field_xpath = ('//*[contains(text(), "{}")]/parent::*'.format(entity) +
                       '//*[contains(@class, "amoforms__sidebar__'
                       'item ui-draggable") and contains(@style, "flex")]')
        for _ in driver.find_elements_by_xpath(field_xpath):
            field = driver.find_element_by_xpath(field_xpath)
            drag_and_drop(field, dest)
            counter += 1
            time.sleep(0.5)
    # Check that all fields exist at the webform tab
    assert counter == len(driver.find_elements_by_xpath(
        '//*[contains(@class, "amoforms__fields__container ")]'))
    save_data_to_mongo(test_name, {'fields_number': counter})


def delete_webform_fields(test_name, num_of_fields=2):
    """ Delete fields in webform settings tab
    Parameters:
    :test_name - name of test used as a key in MongoDB collection;
    :number_of_fields - int, number of fields to delete (from the last field)
    """
    data = find_data_in_mongo(test_name)
    for _ in range(num_of_fields):
        # mouse to last field
        mouse_to_element(
            '//*[contains(@class, "amoforms__fields__container ' +
            'amoforms__fields__container_")][last()]')
        # delete field
        wait_element_and_click(
            '//*[contains(@class, "amoforms__fields__container ' +
            'amoforms__fields__container_")][last()]' +
            '//*[contains(@class, "amoforms__field__action__delete")]')
        time.sleep(0.5)
    # Update data in mongo
    fields_number = data['fields_number'] - num_of_fields
    update_data_in_mongo(test_name, {'fields_number': fields_number})
    # Delete fields assert
    assert find_data_in_mongo(test_name)['fields_number'] == len(
        driver.find_elements_by_xpath(
            '//*[contains(@class, "amoforms__fields__container ")]'))


def set_webform_view():
    """ Set webform design settings """
    # 1. Choice design theme
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and contains(@data-type, "themes")]')
    time.sleep(0.3)
    wait_element_and_click(
        '//*[contains(@class, "amoforms__settings-modal__themes__wrapper")]' +
        '//*[contains(@data-value, "{}")]'.format(randint(0, 5)))
    time.sleep(0.5)
    # 2. Choice Name position
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and contains(@data-type, "name-position")]')
    wait_element_and_click(
        '//*[contains(@class, "amoforms__setting-modal-name-position__btn")' +
        'and contains(@data-type, "{}")]'.format(choice(['left',
                                                         'top',
                                                         'inside',
                                                         ])))
    time.sleep(0.5)
    # 3. Set font color
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and contains(@data-type, "font-color")]')
    wait_element_and_send_text(
        '//*[contains(@class, "colpick_hex_field")]//input',
        randint(0, 999999))
    # 4. Choice font type
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and @data-type="font"]')
    fonts = driver.find_elements_by_xpath(
        '//*[contains(@class, "amoforms__settings-modal__font-family")]'
        '//*[contains(@style, "font-family")]')
    wait_element_and_click(webelement=choice(fonts))
    # 5. Margins
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and contains(@data-type, "form-paddings")]')
    wait_element_and_click(
        '//*[contains(@class, "amoforms__setting-modal-form-paddings__btn") '
        'and contains(@data-type, "{}")]'.format(choice(['yes', 'no'])))
    # 6 Background color
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and contains(@data-type, "background-color")]')
    wait_element_and_send_text(
        '//*[contains(@class, "colpick_hex_field")]//input',
        randint(0, 999999))
    # 7 Background image
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and contains(@data-type, "background-image")]')
    images = driver.find_elements_by_xpath(
        '//*[contains(@class, "amoforms__gallery__image__container") '
        'and contains(@data-image-id, "bg_")]')
    wait_element_and_click(webelement=choice(images))
    # 8. Field form
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and contains(@data-type, "field-form")]')
    wait_element_and_click(
        '//*[contains(@class, "amoforms__setting-modal-field-form__btn") '
        'and contains(@data-type, "{}")]'.format(choice(['rectangular',
                                                         'rounded',
                                                         ])))


def webform_form_settings(test_name):
    """ Set webform settings
    Parameter:
    :test_name - name of test used as a key in MongoDB collection;
    """
    # Click on Form settings
    wait_element_and_click(
        '//*[contains(@class, "amoforms__toggler-item-settings")]')
    # Change name
    wait_element_and_send_text(
        '//*[contains(text(), "Form Name")]/parent::*//input',
        random_data())
    # Add 2 tags
    wait_element_and_click(
        '//*[contains(@class, "amoforms__tab-settings")]' +
        '//div[contains(@id, "add_tags")]')
    time.sleep(0.2)
    for _ in range(2):
        wait_element_and_click(
            '//*[contains(@class, "amoforms__fast-tags-suggest")]' +
            '//*[@class = "tag"]')
    # missclick
    wait_element_and_click('//*[contains(text(), "Form Name")]/parent::*//input')
    # Change lead status
    wait_element_and_click(
        '//*[contains(@class, "pipeline-select-wrapper__inner__container")]')
    time.sleep(0.5)
    statuses = driver.find_elements_by_xpath(
        '//li[contains(@class, "pipeline-select__dropdown__item")]')[1:5]
    wait_element_and_click(webelement=choice(statuses))
    # chnage status back ( set incoming leads )
    wait_element_and_click(
        '//*[contains(@class, "pipeline-select-wrapper__inner__container")]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "pipeline-select__dropdown")]' +
        '//*[contains(text(), "Incoming leads")]')
    # Window form
    wait_element_and_click(
        '//*[contains(text(), "Window form")]/parent::*' +
        '//*[contains(@class, "control-checkbox__body")]')
    time.sleep(0.2)
    window_form_name = random_data()
    wait_element_and_click('//*[contains(text(), "Window form")]/parent::*' +
                           '//*[contains(@class, "amoforms__fields__submit")]//input')
    wait_element_and_send_text(
        '//*[contains(text(), "Window form")]/parent::*' +
        '//*[contains(@class, "amoforms__fields__submit")]//input',
        window_form_name)
    # Form submission
    form_submisson = random_data()
    wait_element_and_send_text(
        '//*[contains(text(), "Form submission")]/parent::*' +
        '//*[contains(@class, "text-input")]',
        form_submisson)
    update_data_in_mongo(test_name,
                         {'window_form_name': window_form_name,
                          'form_submisson': form_submisson})


def webform_form_placement(test_name):
    """ Set settings in webform form placement
    Parameter:
    :test_name - name of test used as a key in MongoDB collection;
    """
    # Go to form placement
    wait_element_and_click(
        '//*[contains(@class, "amoforms__toggler-item")]' +
        '//*[contains(text(), "Form placement")]')
    # Page background color
    wait_element_and_click(
        '//*[contains(text(), "Page background")]/parent::*' +
        '//*[contains(@data-type, "page-background-color")]')
    time.sleep(0.2)
    wait_element_and_send_text(
        '//*[contains(@class, "colpick_hex_field")]//input',
        randint(0, 999999))
    # Page background image
    wait_element_and_click(
        '//*[contains(text(), "Page background")]/parent::*' +
        '//*[contains(@data-type, "page-background-image")]')
    images = driver.find_elements_by_xpath(
        '//*[contains(@class, "amoforms__gallery__image__container ") '
        'and contains(@data-image-id, "bg")]')
    wait_element_and_click(webelement=choice(images))
    # Text
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") '
        'and contains(@data-type, "header-text")]')
    # Change font color
    wait_element_and_click(
        '//*[contains(@class, "amoforms__title_settings__btn") ' +
        'and contains(@data-type, "font-color")]')
    wait_element_and_send_text(
        '//*[contains(@class, "colpick_hex_field")]//input',
        randint(0, 999999))
    # Change font size
    wait_element_and_click(
        '//*[contains(@class, "amoforms__title_settings__btn") ' +
        'and contains(@data-type, "font-size")]')
    font_sizes = driver.find_elements_by_xpath(
        '//*[contains(@class, "amoforms__title_settings__font-size")]/li')
    wait_element_and_click(webelement=choice(font_sizes))
    # Set title
    title = random_data()
    wait_element_and_send_text(
        '//*[contains(@class, "amoforms__title-input ")]',
        title)
    update_data_in_mongo(test_name, {'title': title})
    # missclick
    wait_element_and_click(
        '//*[contains(@class, "settings__label")' +
        ' and contains(text(),"Position")]')
    # logotype
    wait_element_and_click(
        '//*[contains(@class, "amoforms__fields__settings__btn") ' +
        'and contains(@data-type, "header-image")]')
    wait_element_and_send(
        '//*[contains(@id, "amoforms__attach_image")]',
        "/home/autotester/test_data/integration_icon_{}.jpg".format(
            randint(1, 3)))
    time.sleep(3)
    # missclick
    wait_element_and_click(
        '//*[contains(@class, "settings__label")' +
        ' and contains(text(),"Position")]')
    # Set margins 90 px
    wait_element_and_send_text(
        '//*[contains(@class, "positioning-input-margin-top")]//input',
        90)
    # Description
    wait_element_and_send_text(
        '//*[contains(@id, "amoforms_page_description")]',
        random_data())


def fill_webform_page(test_name):
    """ Go to webform pasge, fill fields and submit
    Parameter:
    :test_name - name of test used as a key in MongoDB collection;
    """
    # Click on webform link
    if ServerType == 'PROD_USA':
        wait_element_and_click(
            '//*[contains(@href, "https://www.forms.amocrm.com/") '
            'and contains(text(), "https://www.forms.amocrm.com/")]')
    else:
        wait_element_and_click(
            '//*[contains(@href, "https://forms.amocrm.ru/") '
            'and contains(text(), "https://forms.amocrm.ru/")]')
    # Checking correct title and window form
    data = find_data_in_mongo(test_name)
    title_elem = driver.find_element_by_xpath(
        '//*[contains(@class, "amoforms__header")]')
    assert title_elem.text == data['title']
    window_form_elem = driver.find_element_by_xpath(
        '//*[contains(@id, "amoforms_action_btn")]')
    assert window_form_elem.text == data['window_form_name']
    # click on button
    wait_element_and_click(webelement=window_form_elem)
    time.sleep(0.2)
    # select
    driver.switch_to.frame(driver.find_element_by_xpath(
        '//*[contains(@class, "amoforms_iframe")]'))
    # Check number of fields
    fields_number = len(driver.find_elements_by_xpath(
        '//*[contains(@class, "amoforms__fields__container ' +
        'amoforms__fields__container")]'))
    assert fields_number == data['fields_number']
    # Name
    name = random_data()
    wait_element_and_send_text(
        '//*[contains(@title, "Full name")]/parent::*//input',
        name)
    # Phone
    phone = randint(89000000000, 89999999999)
    wait_element_and_send_text(
        '//*[contains(@title, "Phone")]/parent::*//input',
        phone)
    update_data_in_mongo(test_name,
                         {'name': name,
                          'phone': phone})
    # User terms
    wait_element_and_click('//*[contains(@class, "control-checkbox__body")]')
    # Submit
    wait_element_and_click('//*[contains(@type, "submit")]')
    time.sleep(0.2)
    assert WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, '//*[contains(text(), {})]'.format(
                data['form_submisson']))))
    driver.switch_to.default_content()
    browser_back_button()


def delete_webforms():
    """ Delete all webforms """
    time.sleep(1)
    webform_xpath = '//*[contains(@class, "dp-source dp-source_form ")]'
    for _ in driver.find_elements_by_xpath(webform_xpath):
        wait_element_and_click(webform_xpath)
        # Click on Form settings
        wait_element_and_click(
            '//*[contains(@class, "amoforms__toggler-item-settings")]')
        time.sleep(0.2)
        wait_element_and_click('//*[contains(@class, "delete_form__button")]')
        time.sleep(0.2)
        wait_element_and_click(
            '//*[contains(@class, "modal-body__actions ")]'
            '//*[contains(text(), "Yes")]')
        time.sleep(1)


def dashboard_setup():
    """ Click on dashboard setup """
    wait_element_and_click('//*[contains(@id, "setup_tiles")]')
    time.sleep(2)


def dashboard_add_widgets():
    """ Add Online and NPS widgets to dashboard """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    for widget in ['Online', 'NPS']:
        # Click Add widget
        mouse_to_element_with_offset(
            '//*[@value = "Leads"]//ancestor::'
            '*[contains(@class, "grid-item_edit grid-item_convertable")]',
            10,
            220)
        time.sleep(1)
        wait_element_and_click(
            '//*[@class="dashboard-tile__item_adding"]')
        # Select widget
        wait_element_and_click(
            '//*[contains(@class, "tips-item js-tips-item") '
            'and contains(text(), "{}")]'.format(widget))
        time.sleep(2)
    driver.execute_script("window.scrollTo(0, 0);")
    wait_element_and_click(
        '//*[contains(@class, "js-settings-statuses-save")]')
    refresh_page()
    # check Online widget
    assert driver.find_element_by_xpath(
        '//*[contains(@class, "dashboard-tile-online '
        'dashboard-tile__item ")]'), 'Online widget not found'
    # check NPS widget
    assert driver.find_element_by_xpath(
        '//*[contains(@class, "dashboard-tile-nps '
        'dashboard-tile__item dashboard-tile__item")]'), 'NPS widget not found'


def delete_widgets(with_assert=False):
    """ Delete Online and NPS widgets from dashboard
    Parameters:
    :parameter with_assert - bool, if True than function check that the
                             widgets were removed
    """
    widgets = ('nps', 'online')
    dashboard_setup()
    for widget in widgets:
        if driver.find_elements_by_xpath(
                '//*[contains(@class, "dashboard-tile-{}")]'.format(widget)):
            wait_element_and_click(
                f'//*[contains(@class, "dashboard-tile-{widget}")]'
                '//ancestor::*[contains(@class, "grid-item grid-item_edit '
                'ui-draggable ui-draggable-handle")]'
                '//*[contains(@class, "icon-delete-trash")]')
    if driver.find_elements_by_xpath(
            '//*[@class = "button-input   '
            'button-input-disabled button-input_blue '
            'js-settings-statuses-save"]'):
        wait_element_and_click(
            '//*[contains(@class, "js-dashboard-settings-cancel")]')
    else:
        wait_element_and_click(
            '//*[@class="button-input   '
            'button-input_blue js-settings-statuses-save"]')
    time.sleep(2)
    if with_assert:
        refresh_page()
        # Check that the widgets have been deleted
        for widget in widgets:
            assert not driver.find_elements_by_xpath(
                '//*[contains(@class, "dashboard-tile-'
                '{}__item")]'.format(widget)), "Wiget hasn't been deleted"


def lead_send_template():
    """ Send template and check template message in card """
    # Select chat
    mouse_to_element(
        '//*[contains(@class, "feed-compose__inner")]'
        '//*[contains(@class, "feed-compose-switcher")]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "notes-wrapper")]//*[contains(@data-id, '
        '"chat")]')
    # Template name
    template_name = 'template_for_test'
    # Type first letter of Template name
    wait_element_and_send(
        '//*[contains(@data-hint, "Type here")]',
        template_name[0] + Keys.DELETE)
    time.sleep(0.2)
    wait_element_and_click(
        '//*[contains(@class, "control-contenteditable__suggestions")]' +
        '//*[contains(text(), "{}")]'.format(template_name))
    # Send
    wait_element_and_click(
        '//*[contains(@class, "button-input   ' +
        'js-note-submit feed-note__button")]')
    time.sleep(1)
    # check template data
    template_message_text = driver.find_element_by_xpath(
        '//*[contains(@class, "feed-note__message_paragraph")]').text
    entity_dict = {
        'lead_id': driver.find_element_by_xpath(
            '//*[contains(@data-id, "lead_id")]/span').text.replace('#', ''),
        'lead_name': driver.find_element_by_xpath(
            '//*[contains(@id, "person_n")]').text,
        'resp_user': driver.find_element_by_xpath(
            '//*[contains(@class, "multisuggest users_select-select_one card-fields__fields-block__users-select'
            ' js-multisuggest js-can-add ")]'
            '//*[contains(@class,"multisuggest__list-item js-multisuggest-item")]').get_attribute('data-title')
    }
    for key in entity_dict.keys():
        assert entity_dict[key] in template_message_text


def add_automatic_actions_indiviual_form():
    """ Create automatic action "Individual form" in DP """
    # Check autoaction exist ( if previous test failed )
    if driver.find_elements_by_xpath(
            '//*[@class="digital-pipeline__short-task"]'):
        wait_element_and_click(
            '//*[@class="digital-pipeline__short-task"]')
        time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "digital-pipeline__edit-delete")]')
        save_dp()
    # Cell click
    wait_element_and_click(dp_cell_xpath(1, 2))
    # Add Individual form
    wait_element_and_click(
        '//*[contains(@class, "button-add")]//*[text() = "Generate form"]')
    time.sleep(0.5)
    # click on Create form
    wait_element_and_click(
        '//*[contains(@class, "digital-pipeline__trigger-button-form-init")]')
    time.sleep(0.5)
    # Go to form placement
    wait_element_and_click(
        '//*[contains(@class, "amoforms__toggler-item")]' +
        '//*[contains(text(), "Form placement")]')
    # Select text in "select field"
    wait_element_and_click(
        '//*[contains(@class, "amoforms__tab-settings__select-field-link-b")]')
    wait_element_and_click(
        '//*[contains(@class, "amoforms__tab-settings__select-field-link")]'
        '//*[contains(@title, "text")]')
    # Save
    wait_element_and_click(
        '//*[contains(@class, "amoforms__header")]' +
        '//*[contains(text(), "Save")]')
    time.sleep(2)
    # Done
    wait_element_and_click(
        '//*[contains(@class, "button-input-inner__text") ' +
        'and contains(text(), "Done")]')
    time.sleep(1)


def customer_to_next_stage(test_name):
    """ Drag customer and drop it at the next pipeline stage
    Parameter:
    :test_name - name of test used as a key in MongoDB collection;
    """
    data = find_data_in_mongo(test_name)
    # Drag'n'Drop
    source = driver.find_element_by_xpath(
        '//*[contains(@title, "{}")]'.format(data['customer_name']))
    dest = driver.find_element_by_xpath(
        '//*[contains(@class, "s-pipeline_status pipeline_status")]'
        '//*[contains(@title, "STAGE 1")]/parent::*/'
        'parent::*/following-sibling::*')
    drag_and_drop(source, dest)
    time.sleep(0.5)


def go_to_specified_customer(test_name):
    """ Go to specified customers card """
    # Find customer name in mongo
    data = find_data_in_mongo(test_name)
    wait_element_and_click(
        '//*[contains(@title, "{}")]'.format(data['customer_name']))
    time.sleep(1)


def go_to_form_from_customer(test_name):
    """ Go to form page by link from customer card page and fill it """
    # Get URL from "text" field
    url = driver.find_element_by_xpath(
        '//*[contains(@class, "card-entity-form")]'
        '//*[contains(text(), "text")]/parent::*/'
        'following-sibling::*/input').get_attribute('value')
    driver.get(url)
    time.sleep(1)
    # Switch to iframe
    driver.switch_to.frame(driver.find_element_by_xpath(
        '//*[contains(@class, "amoforms_iframe")]'))
    # Fill fields
    full_name = random_data()
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Full name")]', full_name)
    phone = randint(10000000000, 99999999999)
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Phone")]', phone)
    email = random_data() + "@example.com"
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Email")]', email)
    note = random_data()
    wait_element_and_send_text(
        '//*[contains(@placeholder, "Note")]', note)
    # Submit
    wait_element_and_click(
        '//button[contains(@class, "amoforms__submit-button")]')
    time.sleep(2)
    # Add data to mongo collection
    update_data_in_mongo(test_name,
                         {'full_name': full_name,
                          'phone': phone,
                          'email': email,
                          'note': note,
                          })
    driver.switch_to.default_content()
    browser_back_button()


def check_customer_card_data(test_name):
    """ Check customer field data (Filled by webform) """
    data = find_data_in_mongo(test_name)
    # check fields
    # 1. Name
    assert driver.find_elements_by_xpath(
        '//*[contains(@id, "contacts_list")]'
        '//*[contains(@class, "linked-form__field__value-name")]'
        '//*[contains(text(), "{}")]'.format(data['full_name']))
    # 2. Phone
    assert driver.find_elements_by_xpath(
        '//*[contains(@id, "contacts_list")]'
        '//*[contains(@class, "control-phone")]'
        '//*[contains(@value, "{}")]'.format(data['phone']))
    # 3. email
    assert driver.find_elements_by_xpath(
        '//*[contains(@id, "contacts_list")]'
        '//*[contains(@class, "linked-form__field__value")]'
        '//*[contains(@value, "{}")]'.format(data['email']))
    # 4. note
    assert driver.find_elements_by_xpath(
        '//*[contains(@class, "card-holder__feed")]'
        '//*[contains(@class, "feed-note-wrapper-note")]'
        '//*[contains(text(), "{}")]'.format(data['note']))


def set_up_pipeline_mode(mode):
    """ This fucntion set specified customers pipeline mode in customers DP
    Parameters:
    :mode - str, may be 'recurring_purchases' and 'dynamic_segmentation'
    """
    time.sleep(0.5)
    wait_element_and_click(
        '//button[contains(@class, "button-settings_dm")]')
    time.sleep(2)
    if mode not in ('Recurring purchases', 'Dynamic segmentation'):
        raise MyException('Invalid mode!')
    else:
        wait_element_and_click(
            '//*[contains(text(), "{}")]'.format(mode) +
            '/ancestor::*[contains(@class, '
            '"modal-settings-dm__item")]//button')
    wait_element_and_click('//*[contains(@class, "icon icon-modal-close")]')
    time.sleep(1)


def check_dynamic_segmentation_columns():
    """ Check that there are no columns like "Recent purchase",
    "Expected purchase", "Did not purchase"
    """
    for column in ("Recently purchase",
                   "Expected purchase",
                   "Did not purchase",
                   ):
        assert (not driver.find_elements_by_xpath(
            '//*[contains(@class, "pipeline_status__head_title")]'
            '//*[contains(text(), "{}")]'.format(column))), \
            "Column '{}' is exist!".format(column)


def dynamic_segmentation_add_conditions(test_name):
    """ Add conditions to first column in DP customers (with dynamic segm.)
    """
    # Add conditions
    for _ in range(7):
        wait_element_and_click(
            '//*[contains(@class, "digital-pipeline__item_head")][1]'
            '//*[contains(@class, "digital-pipeline__add-new-condition")]')
        time.sleep(0.2)
        wait_element_and_click(
            '//*[contains(@class, "-pipeline__selector_conditions-list")][1]'
            '//*[contains(@class, "digital-pipeline__condition-select-item")]')
        time.sleep(0.2)
        try:
            time.sleep(0.5)
            driver.find_element_by_xpath(
                '//*[contains(@class, "multisuggest__input js-multisuggest-input")][last()]').send_keys(Keys.ESCAPE)
        except exceptions.NoSuchElementException:
            pass

    condition_number = len(driver.find_elements_by_xpath(
        '//*[contains(@class, "digital-pipeline__item_head")][1]'
        '//*[contains(@class, "digital-pipeline__settings_condition-'
        'base-container")]'))
    assert condition_number == 7, \
        "Wrong number of conditions: {} != 7".format(condition_number)
    # Delete 3 condition
    for _ in range(7):
        wait_element_and_click(
            '//*[contains(@class, "digital-pipeline__item_head")][1]'
            '//*[contains(@class, "_pipeline__action-conditions_settings")]'
            '//*[contains(@class, "condition-delete")]')
    # Cancel
    wait_element_and_click(
        '//*[contains(@class, "list__top__actions list__top__actions_plain digital-pipeline__top-actions")]')
    time.sleep(2)
    # save responsible_user_id from 4 column condition to mongoDB
    responsible_user_id = driver.find_element_by_xpath(
        '//*[contains(@class, "digital-pipeline__item_head")][last()-1]'
        '//*[contains(@class, "digital-pipeline__condition_multisuggest_")]'
        '').get_attribute('data-condition-item-id')
    update_data_in_mongo(test_name,
                         {'responsible_user_id': responsible_user_id})


def check_customers_in_columns(test_name):
    """ This function check number of customers and then delete all of them
    :test_name - collection key as a key in MongoDB
    """
    id_list = []
    for col_number in range(2, 5):
        # Because tag condition in customers pipeline do not work due to a bug
        # we will use this fix. If bug is already fixed - remove next if
        if col_number == 2:
            col_number -= 1
        customers = driver.find_elements_by_xpath(
            '//*[contains(@class, "js-pipeline_status pipeline_status")]'
            '[{}]//*[contains(@id, "pipeline_item_")]'.format(col_number))
        id_list.append(customers[0].get_attribute('data-id'))
        assert len(customers) == 1, \
            'Customer count is {}, but shoud be 1'.format(len(customers))
    # Load data from Mongo
    data = find_data_in_mongo(test_name)
    # Delete customers
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType)
    amo_session.delete_customers(id_list)


def delete_all_customers(test_name, init_session=False):
    """ Delete customer from account by using AmoCRM api
    Parameters:
    :test_name - collection key as a key in MongoDB
    :init_session - bool, if True than create new amo session
                          elif False than use saved cookie
    """
    # Load data from mongo
    data = find_data_in_mongo(test_name)
    # Create AmoSession object
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType,
                             password=None)
    if init_session:
        amo_session.create_session()
    # Delete customers
    try:
        amo_session.delete_customers(amo_session.get_customers_id_list())
    except KeyError:
        # It's ok: There are no customers in account
        pass


def random_n_digits(n: int):
    """ Return a integer of n number of digits
    Parameters:
    :parameter n - int, number of digits in result integer
    """
    if n < 1:
        raise MyException('Wrong argument! n must be greater than 0')
    else:
        return randint(10 ** (n - 1), 10 ** n - 1)


def widgets_search(widget_name):
    """ Search wigdet in integration search tab
    Parameters:
    :parameter widget_name - str, name of widget to search
    """
    wait_element_and_send_text(
        '//*[contains(@id, "widgets_search")]',
        widget_name)
    time.sleep(0.5)


def add_tranzaptor():
    """ Add tranzaptor widget to account """
    # Click on tranzaptor icon
    wait_element_and_click(
        '//*[contains(@class, "widget-box")]'
        '//*[contains(@id, "amo_tranzaptorcom")]')
    # click on checkbox
    checkbox = driver.find_element_by_xpath(
        '//*[contains(@class, "widget_settings_block__switch")]'
        '//*[@type="checkbox"]')
    if not checkbox.is_selected():
        wait_element_and_click(
            '//*[contains(@class, "widget_settings_block__switch_item")]')
        wait_element_and_click(
            '//*[contains(@class, "widget-save button-input_blue")]')


def cost_formatting(cost: str, currency='руб'):
    """ Return a formatted cost string
    Parameters:
    :parameter cost - str, cost string need to format
    :parameter currency - str, which currency use in cost string
    Example:

        >>> some_cost = "30 543,30 руб"
        >>> cost_formatting(some_cost)

        30543.30

    """
    cost = cost.replace(' ', '').replace(',', '.').replace(currency, '')
    return '{:.2f}'.format(round(float(cost), 2))


def fill_tranzaptor_fields(test_name, nds='on', edit_mode=False):
    """ Fill fields in tranzaptor invoice
    Parameters:
    :parameter test_name - using test_name as a key in MongoDB collection
    :parameter nds - str, Use to on/off НДС field
                     May be "on" or "off"
    :parameter edit_mode - bool, true if function use in editing invoice
    """
    if not edit_mode:
        # Fill the fields
        customer_name = random_data()
        wait_element_and_send_text(
            '//*[contains(@class, "tranzaptor-modal_add-client_name")]/input',
            customer_name)
        inn = random_n_digits(12)
        wait_element_and_send_text(
            '//*[contains(@class, "tranzaptor-modal_add-client_inn")]/input',
            inn)
        kpp = random_n_digits(12)
        wait_element_and_send_text(
            '//*[contains(@class, "tranzaptor-modal_add-client_kpp")]/input',
            kpp)
        # Save to mongo
        update_data_in_mongo(test_name,
                             {'customer_name': customer_name,
                              'inn': inn,
                              'kpp': kpp,
                              })
    article = random_n_digits(9)
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_item_article")]/input',
        article)
    item_name = random_data()
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_item_name")]/input',
        item_name)
    item_price = randint(1, 1000)
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_item_price")]/input',
        item_price)
    item_count = random_n_digits(3)
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_item_count")]/input',
        item_count)
    discount = random_n_digits(2)
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_item_discount")]/input',
        str(discount) + '%')
    # click on НДС checkbox
    checkbox = driver.find_element_by_xpath(
        '//*[contains(@class, "tranzaptor-modal_title-nds")]'
        '//*[@type="checkbox"]')
    if nds == 'on':
        if not checkbox.is_selected():
            checkbox.click()
        # Select НДС
        wait_element_and_click(
            '//*[contains(@class, "tranzaptor-modal_item_nds")]'
            '//button[contains(@class, "control--select--button")]')
        assert len(driver.find_elements_by_xpath(
            '//*[contains(@class, "invoice_item")][1]'
            '//*[contains(@class, "tranzaptor-modal_item_nds")]'
            '//*[contains(@class, "control--select--list--item") '
            'and (@data-value = ( 0 or 18)) ]')) == 3
        nds_value = 10
        wait_element_and_click(
            '//*[contains(@class, "invoice_item")][1]'
            '//*[contains(@class, "tranzaptor-modal_item_nds")]'
            '//*[contains(@class, "control--select--list--item") '
            'and @data-value = {} ]'.format(nds_value))
    elif nds == 'off':
        checkbox.click()
        nds_value = None
    else:
        raise Exception('NDS argument may be "on" of "off"!')
    # Calculate sums and assert correct value
    resume_total = round(item_price * item_count * 0.01 * (100 - discount), 2)
    assert cost_formatting(str(resume_total)) == cost_formatting(
        driver.find_element_by_xpath(
            '//*[contains(@id, "resume_total")]').text)
    # Update data in mongo
    update_data_in_mongo(test_name,
                         {'article': article,
                          'item_name': item_name,
                          'item_price': item_price,
                          'item_count': item_count,
                          'discount': discount,
                          'nds': nds_value,
                          'resume_total': resume_total,
                          })
    # Click on Save
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-modal-body")]'
        '//*[contains(@class, "button-input-inner")]')
    time.sleep(2)


def to_tranzaptor():
    """ Click on tranzaptor tab """
    wait_element_and_click(
        '//*[contains(@class, "card-fields__fields-block")]'
        '//*[contains(@title, "Tranzaptor")]')


def tranzaptor_delete_company():
    """ This function all additional companies """
    customer_companies_xpath = (
        '//*[contains(@id, "companies_list")]'
        '//*[contains(@class, "icon-inline icon-dots-2")]')
    for _ in driver.find_elements_by_xpath(customer_companies_xpath):
        wait_element_and_click(customer_companies_xpath)
        time.sleep(0.2)
        wait_element_and_click(
            '//*[contains(@id, "companies_list")]'
            '//*[contains(@class, "icon-inline icon-unlink")]')
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]'
            '//*[contains(@class, "modal-body__actions__save")]')
        time.sleep(1)


def tranzaptor_delete_invoice(all_invoices=False):
    """ This function delete first invoice or all invoices in current card
    Parameters:
    :parameter all - bool, if True than delete all invoices
    """
    invoice_dots_xpath = (
        '//*[contains(@class, "tranzaptor-invoice")]'
        '//*[contains(@class, "button-more-dims")]')
    if all_invoices:
        invoices = driver.find_elements_by_xpath(invoice_dots_xpath)
    else:
        invoices = list([driver.find_element_by_xpath(invoice_dots_xpath)])
    for _ in invoices:
        # Click on three dots
        wait_element_and_click(invoice_dots_xpath)
        time.sleep(0.2)
        # Select Delete
        wait_element_and_click(
            '//*[contains(@class, "button-input__context-menu ")]'
            '//*[contains(@class, "dot-context_line__delete")]')
        time.sleep(0.2)
        # Select accept in modal window
        wait_element_and_click(
            '//*[contains(@class, "tranzaptor-modal-delete")]'
            '//*[contains(@class, "modal-body__actions__save")]')
        time.sleep(1)
        # Check delete record in feed
        assert driver.find_element_by_xpath(
            '//*[contains(@class, "feed-note-wrapper-service_message")]['
            'last()]'
            '//*[contains(text(), "удален")]')


def create_tranzaptor_invoice(test_name):
    """ Select tranzaptor tab in lead card and fill fields
    Parameters:
    :parameter test_name - using test_name as a key in MongoDB collection
    """
    time.sleep(0.2)
    # click on Создать счёт
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor_create-button")]')
    time.sleep(0.5)
    # Fill the fields
    fill_tranzaptor_fields(test_name, nds='on')
    # Assert note in feed
    assert driver.find_elements_by_xpath(
        '//*[contains(@class, "feed-note-wrapper-service_message")][last()]'
        '//*[contains(text(), "Счёт №") and contains(text(), "создан")]')


def edit_tranzaptor_invoice(test_name):
    """ Edit fields in tranhzaptor invoice
    Parameters:
    :parameter test_name - using test_name as a key in MongoDB collection
    """
    # Click on edit pencil
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoice-edit-icon")]')
    # Change invoice number
    invoice_number = randint(1, 1000)
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_title")]'
        '//input[contains(@name, "number")]',
        invoice_number)
    # Change date
    invoice_date = (datetime.date.today() - datetime.timedelta(
        days=1)).strftime('%d.%m.%Y')
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_title")]'
        '//input[contains(@name, "created")]',
        invoice_date)
    # Update data in Mongo
    update_data_in_mongo(test_name,
                         {'invoice_number': invoice_number,
                          'invoice_date': invoice_date,
                          })
    # Edit fields
    fill_tranzaptor_fields(test_name, nds='off', edit_mode=True)
    # Refresh page and assert notes in feed
    refresh_page()
    assert driver.find_elements_by_xpath(
        '//*[contains(@class, "feed-note-wrapper-service_message")][last()]'
        '//*[contains(text(), "Счёт №") and contains(text(), "изменен")]')


def download_tranzaptor_invoice(test_name):
    """ This function download file by button click and check pdf file in
    Downloads directory.
    Parameters:
    :parameter test_name - using test_name as a key in MongoDB collection
    """
    # Click on download
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoice-pdf_button")]')
    time.sleep(1)
    # Check that the pdf file has downloaded
    data = find_data_in_mongo(test_name)
    file_path = os.path.join(os.getcwd().split('selenium_tests')[0],
                             'Downloads/',
                             '{}.pdf'.format(data['invoice_number']))
    if not os.path.exists(file_path):
        raise MyException(
            'There is no invoice like "{}.pdf"'.format(data['invoice_number']))


def check_invoice_at_tranzaptor_site(test_name):
    """ This function go to tranzaptor site and check created invoice
    Parameters:
    :parameter test_name - using test_name as a key in MongoDB collection
    """
    url = driver.find_element_by_xpath(
        '//*[contains(@class, "tranzaptor-link-copy")]').get_attribute(
        'data-clipboard-text')
    # Create new tab and go to tranzaptor
    driver.execute_script('window.open("{}", "_blank");'.format(url))
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)
    # Check data at tranzaptor.com
    data = find_data_in_mongo(test_name)
    # Check invoice number and date
    assert driver.find_element_by_xpath(
        '//*[contains(@id, "info")]'
        '/h1[contains(text(), "{0}") and contains(text(), "{1}")]'.format(
            data['invoice_number'], data['invoice_date']))
    # Check customer
    assert driver.find_element_by_xpath(
        '//td[contains(text(), "Клиент")]'
        '/parent::*//*[contains(text(), "{}")]'.format(data['customer_name']))
    # Check fields
    fields = driver.find_elements_by_xpath(
        '//tbody[contains(@class, "data")]//td')[1:-1]
    items = (data['article'],
             data["item_name"],
             data["item_price"],
             data["item_count"],
             data["discount"])
    for data_item, field in zip(items, fields):
        assert str(data_item) in field.text, \
            "{} not in invoice".format(data_item)
    # Switch to AmoCRM window
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(0.5)


def copy_invoice(test_name, cancel=False):
    """ Click on three dots near invoice and then click copy
    Parameters:
    :parameter test_name - using test_name as a key in MongoDB collection
    :parameter cancel - bool, cancel copy (click cancel in modal window)
    """
    # Click on three dots
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-buttons-wrapper")]'
        '//*[contains(@class, "tranzaptor-invoice-dot_button")]')
    time.sleep(0.2)
    # Click on copy
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-row-dot-context_line__copy")]')
    time.sleep(0.5)
    # Update data in Mongo
    invoice_number = driver.find_element_by_xpath(
        '//*[contains(@class, "tranzaptor-modal_title")]'
        '//input[contains(@name, "number")]').get_attribute('placeholder')
    invoice_date = driver.find_element_by_xpath(
        '//*[contains(@class, "tranzaptor-modal_title")]'
        '//input[contains(@name, "created")]').get_attribute('placeholder')
    update_data_in_mongo(test_name,
                         {'invoice_number_copy': invoice_number.strip(),
                          'invoice_date_copy': invoice_date.strip(),
                          })
    if cancel:
        wait_element_and_click(
            '//*[contains(@class, "tranzaptor-modal-body")]'
            '//*[contains(@class, "button-cancel")]')
        time.sleep(0.2)
    else:
        # Update data in Mongo and save
        wait_element_and_click(
            '//*[contains(@class, "tranzaptor-modal-body")]'
            '//*[contains(@class, "button-input_add")]')
        time.sleep(1.5)
        invoice_count = len(driver.find_elements_by_xpath(
            '//*[contains(@class, "tranzaptor-invoice-title")]'))
        assert invoice_count == 2, "Invoice count != 2 "


def tranzaptor_invoice_close_act(test_name):
    """ Close tranzaptor invoice with act
    Parameters:
    :parameter test_name - using test_name as a key in MongoDB collection
    """
    data_mongo = find_data_in_mongo(test_name)
    # Click on three dots
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoices-wrapper")][last()]'
        '//*[contains(@class, "tranzaptor-invoice-dot_button")]')
    # Click on close and go to the new tab
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoices-wrapper")][last()]'
        '//*[contains(@class, "tranzaptor-invoice-close")]')
    # Focus on opened tab
    driver.switch_to.window(driver.window_handles[-1])
    assert str(data_mongo['invoice_number']) in driver.find_element_by_xpath(
        '//*[contains(@class, "pagetitle")]/a').text
    time.sleep(0.5)
    # Save invoice
    wait_element_and_click(
        '//button[contains(@type, "submit")]')
    time.sleep(1)
    with open('settings.yml') as conf:
        data_settings = yaml.load(conf)['tranzaptor']
    # Check invoice title
    assert data_settings['company'] in driver.find_element_by_xpath(
        '//*[@id="info"]//*[contains(text(), "Исполнитель")]'
        '/parent::*/*[contains(@class, "value")]').text
    assert data_mongo['customer_name'] in driver.find_element_by_xpath(
        '//*[@id="info"]//*[contains(text(), "Заказчик")]'
        '/parent::*/*[contains(@class, "value")]').text
    # Check invoice table
    table_fields = driver.find_elements_by_xpath(
        '//tbody[contains(@class, "data")]//td')[1:]
    items = ('article',
             'item_name',
             'item_price',
             'item_count',
             )
    for item, field in zip(items, table_fields):
        assert str(data_mongo[item]) in field.text, \
            "item {0}: {1} != {2}".format(item,
                                          str(data_mongo[item]),
                                          field.text)
    # Check customers fields
    assert data_mongo['customer_name'] in driver.find_element_by_xpath(
        '//td[contains(@class, "customer")]//strong').text
    assert str(data_mongo['inn']) in driver.find_element_by_xpath(
        '//*[contains(@class, "customer")]'
        '//*[contains(@class, "value ITN")]').text
    assert str(data_mongo['kpp']) in driver.find_element_by_xpath(
        '//*[contains(@class, "customer")]'
        '//*[contains(@class, "value TRRC")]').text
    # Check supplier fields
    assert data_settings['company'] in driver.find_element_by_xpath(
        '//td[contains(@class, "supplier")]//strong').text
    assert str(data_settings['inn']) in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]'
        '//*[contains(@class, "value ITN")]').text
    assert str(data_settings['kpp']) in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]'
        '//*[contains(@class, "value TRRC")]').text
    full_address = ', '.join([str(data_settings['post_index']),
                              data_settings['city'],
                              data_settings['address'],
                              ])
    assert full_address in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]'
        '//*[contains(@class, "address_value")]').text
    assert data_settings['settlement_account'] in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]//*[contains(text(), "Р/c")]'
        '/parent::*/*[contains(@class, "value")]').text, \
        "Должно быть '{0}', а на деле '{1}'".format(
            data_settings['settlement_account'],
            driver.find_element_by_xpath(
                '//*[contains(@class, "supplier")]//*[contains(text(), "Р/c")]'
                '/parent::*/*[contains(@class, "value")]').text)
    assert data_settings['correspond_account'] in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]//*[contains(text(), "К/c")]'
        '/parent::*/*[contains(@class, "value")]').text
    assert data_settings['bank'] in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]//*[contains(text(), "Банк")]'
        '/parent::*/*[contains(@class, "value")]').text
    assert data_settings['bik'] in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]//*[contains(text(), "БИК")]'
        '/parent::*/*[contains(@class, "value")]').text
    assert data_settings['telephone'] in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]//*[contains(text(), "Телефон")]'
        '/parent::*/*[contains(@class, "value")]').text
    assert data_settings['name'] in driver.find_element_by_xpath(
        '//*[contains(@class, "supplier")]//tbody'
        '//*[contains(@class, "name")]').text
    # Switch to AmoCRM
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(0.5)


def open_invoice_in_tranzaptor():
    """ This function open invoice at tranzaptor.com """
    # Click on three dots
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoices-wrapper")][last()]'
        '//*[contains(@class, "tranzaptor-invoice-dot_button")]')
    # Click on close and go to the new tab
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoices-wrapper")][last()]'
        '//*[contains(@class, "tranzaptor-invoice-open")]')
    # Focus on opened tab
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(0.5)
    # Switch to AmoCRM
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    time.sleep(0.5)


def tranzaptor_change_status_to_payed():
    """ Change invoice status if card """
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoice-status_select")]')
    time.sleep(0.5)
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoice-status_select")]'
        '//*[contains(@data-value, "payed")]')
    time.sleep(0.5)
    assert driver.find_elements_by_xpath(
        '//*[contains(@class, "feed-note-wrapper-service_message")]'
        '[last()]//*[contains(text(), "оплачен")]')


def tranzaptor_create_customer(test_name):
    """ Create new customer in tranzaptor invoice
    :parameter test_name - using test_name as a key in MongoDB collection
    """
    # Click on edit pencil
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-invoice-edit-icon")]')
    time.sleep(0.5)
    # Create new customer
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-modal_select_button")]')
    time.sleep(0.2)
    wait_element_and_click(
        '//*[contains(@id, "tranzaptor_add_client")]')
    # Fiil new customer fields
    customer_name = random_data()
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_add-client_name")]/input',
        customer_name)
    inn = random_n_digits(12)
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_add-client_inn")]/input',
        inn)
    kpp = random_n_digits(12)
    wait_element_and_send_text(
        '//*[contains(@class, "tranzaptor-modal_add-client_kpp")]/input',
        kpp)
    # Save to mongo
    update_data_in_mongo(test_name,
                         {'customer_name': customer_name,
                          'inn': inn,
                          'kpp': kpp,
                          })
    # Click on Save
    wait_element_and_click(
        '//*[contains(@class, "tranzaptor-modal-body")]'
        '//*[contains(@class, "button-input-inner")]')
    refresh_page()
    assert driver.find_elements_by_xpath(
        '//*[contains(@class, "feed-note-wrapper-service_message")]'
        '[last()]//*[contains(text(), "изменен")]')


def disable_tranzaptor_widget():
    """ Disable tranzaptor widget in extension settings """
    # Click on tranzaptor wiget
    wait_element_and_click(
        '//*[contains(@data-code, "amo_tranzaptorcom")]')
    time.sleep(0.5)
    # Disable widget
    wait_element_and_click(
        '//*[contains(@class, "modal-list")]'
        '//*[contains(@class, "widget_settings_block__switch_item")]')
    # Save
    wait_element_and_click(
        '//*[contains(@class, "widget_settings_block__controls")]'
        '//*[contains(@class, "button-input-inner ")]')
    time.sleep(0.5)


def api_change_lang(test_name, language):
    """ Change account language by api
    Parametrs:
    :parameter test_name - using test_name as a key in MongoDB collection
    :parameter language -  str, account language
                           ru - russian, en - english
    """
    # Load data from settings.yml
    data = find_data_in_mongo(test_name)
    # change language
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType,
                             password=None)
    amo_session.create_session()
    amo_session.change_account_language(language)
    refresh_page(0)


def delete_juridical_person_field():
    """ This function delete juridical person field in card if exist """
    # juridical person field line xpath
    xpath = ('//*[contains(@class, "cf-section") and '
             '@data-type="companies"]//*[contains(text(), "Юр. лицо")]')
    if driver.find_elements_by_xpath(xpath):
        wait_element_and_click(xpath)
        time.sleep(0.5)
        wait_element_and_click(
            '//*[contains(@class, "cf-section") and @data-type="companies"]'
            '//*[contains(@class, "cf-field-edit__remove")]')
        time.sleep(0.3)
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]'
            '//*[contains(@class, "modal-body__actions__save")]')
        time.sleep(1)


def check_tranzaptor_tab(status):
    """ This function check that there is no Tranzaptor tab if card
    Parameter:
    :parameter status - str, if "enable" - than check that tranzaptor tab exist
                             elif "disable" - check that tranzaptor don't exist
    """
    time.sleep(1)
    xpath = ('//*[contains(@class, "card-fields__fields-block")]'
             '//*[contains(@title, "Tranzaptor")]')

    if status == 'enable':
        assert driver.find_elements_by_xpath(xpath)
    elif status == 'disable':
        assert not driver.find_elements_by_xpath(xpath)
    else:
        raise Exception('Wrong argument! Use "enable" or "disable"')


def dp_cleaner():
    """ Delete created automatic actions """
    automatic_actions = ('Add a task',
                         'Create lead',
                         'Create customer',
                         'Send mail',
                         'Salesbot',
                         'Google Analytics',
                         'Webhook',
                         'Lead stage change',
                         'Remove tags',
                         "Change lead’s user",
                         'Change field',
                         )
    for action in automatic_actions:
        xpath = ('//*[contains(@class, "digital-pipeline__statuses-row")]'
                 '//*[contains(@class, "short-task-title") and '
                 'contains(text(), "{}")]'.format(action))
        try:
            element = driver.find_element_by_xpath(xpath)
        except exceptions.NoSuchElementException:
            element = None
        if element:
            wait_element_and_click(xpath)
            wait_element_and_click(
                '//*[contains(@class, "digital-pipeline__edit-delete")]')
            # need to scroll up for webdriver correct works
            driver.find_element_by_tag_name('body').send_keys(
                Keys.CONTROL + Keys.HOME)
            time.sleep(0.5)
    save_dp()
    time.sleep(2)


def delete_free_users():
    """ This function delete all free users if they exist """
    # check number of free users
    if driver.find_elements_by_xpath('//*[contains(@data-free-user, "Y")]'):
        # click on select all checkbox
        wait_element_and_click(
            '//*[contains(@id, "list_item_free")]'
            '//*[contains(@class, "control-checkbox__body")]')
        # remove users
        wait_element_and_click(
            '//*[contains(@id, "list_item_free")]'
            '//*[contains(@data-type, "delete")]')
        wait_element_and_click(
            '//*[contains(@class, "modal-body__inner")]'
            '//button[contains(@class, "modal-body__actions__save")]')
        time.sleep(1)


def confirm_save_changes():
    """ This function click save button in modal window"""
    wait_element_and_click(
        '//*[contains(@class, "button-input    js-modal-accept ' +
        'js-button-with-loader modal-body__actions__save ' +
        'button-input_blue")]')
    time.sleep(1)


def feed_note_expand():
    """ This function click expand button in feed"""
    wait_element_and_click(
        '//*[contains(@class, "feed-note__blue-link js-grouped-expand")]')


def dp_source_cleaner():
    """ This function delete leads sources in dp settings"""
    xpath = '//*[contains(@class, "dp_source_delete js-source_delete")]'
    if driver.find_elements_by_xpath(xpath):
        wait_element_and_click(xpath)


def make_date(date):
    """
    This function convert date to European or USA format
    :param date: input date
    :type date: str
    :return: str
    """
    if ServerType == 'PROD_USA':
        return date[3:5] + '.' + date[:2] + '.' + date[6:]
    else:
        return date


def make_time(hour, minutes):
    """
    This function convert time to 12h or 24h format
    :param hour: input time hour
    :type hour: int
    :param minutes: input time minutes
    :type minutes: int
    :return: str
    """
    if ServerType == 'PROD_USA':
        if hour == 0:
            return "12:{:02d} AM".format(minutes)
        elif hour == 12:
            return "12:{:02d} PM".format(minutes)
        elif hour < 13:
            return "{}:{:02d} AM".format(hour, minutes)
        else:
            return "{}:{:02d} PM".format(hour - 12, minutes)
    else:
        return "{:02d}:{:02d}".format(hour, minutes)


def search_titled_leads(title, choose_one=True):
    """
    Search the stage with some title using 'Search and filter'
    :param title: Title name of stage or list of that names.
    :type title: str, list of str
    :param choose_one: If its true then only one stage will be chosen
    :type choose_one: bool
    """
    wait_element_and_click('//*[contains(@class, "checkboxes_dropdown") and contains(text(), "Active stages")]')
    wait_element_and_click('//*[contains(@class, "control-checkbox__helper control-checkbox__helper_minus")]')
    if choose_one:
        if isinstance(title, list):
            xpath = '//*['
            for item in title:
                xpath += 'contains(@title, "{0}") or '.format(item)
            xpath = xpath[:-4] + ']'
        else:
            xpath = '//*[contains(@title, "{0}")]'.format(title)
        wait_element_and_click(xpath)
    else:
        if isinstance(title, str):
            title = [title]
        for item in title:
            xpath = '//*[contains(@title, "{0}")]'.format(item)
            wait_element_and_click(xpath)
    wait_element_and_click('//*[contains(@class, "button-input") and contains(text(), "Apply")]')


def save_info_unqualified_leads(test_name=False):
    """
    Save lead name, email, contact name, phone number from the card of the unqualified_lead to DB
    :param test_name: test name for get data from mongo
    :type test_name: str
    """
    time.sleep(3)
    lead_name = driver.find_element_by_xpath('//*[contains(@class,"text-input text-input-textarea card-fields'
                                             '__top-name-input js-textarea-autosize")]')
    field_lead_name = lead_name.get_attribute('placeholder').split()[-1]

    contact_name = driver.find_element_by_xpath(
        '//*[contains(@class, "linked-form__cf js-linked-name-view js-form-changes-skip text-input")]')
    field_contact_name = contact_name.get_attribute('value')

    phone_number = driver.find_element_by_xpath(
        '//*[contains(@class,"control-phone__formatted js-form-changes-skip'
        ' linked-form__cf js-linked-pei text-input")]')
    field_phone_number = phone_number.get_attribute('value')

    email = driver.find_element_by_xpath(
        '//*[contains(@class,"text-input control--suggest--input js-control--suggest--input'
        ' control--suggest--input-inline linked-form__cf js-linked-pei")]')
    field_email = email.get_attribute('value')

    if test_name:
        save_data_to_mongo(test_name,
                           {'xpath': 'xpath_contact_name',
                            'value': field_contact_name})
        save_data_to_mongo(test_name,
                           {'xpath': 'xpath_lead_name',
                            'value': field_lead_name})
        save_data_to_mongo(test_name,
                           {'xpath': 'xpath_phone_number',
                            'value': field_phone_number})
        save_data_to_mongo(test_name,
                           {'xpath': 'xpath_email',
                            'value': field_email})


def check_search_unsorted(test_name):
    """ Check two disc. The first dict - fields from DB, the second - from the card of the lead"""
    time.sleep(3)
    lead_name = driver.find_element_by_xpath('//*[@data-id="lead_id"]')
    lead_from_web = {'lead_name': lead_name.text}

    contact_name = driver.find_element_by_xpath(
        '//*[contains(@class, "linked-form__cf js-linked-name-view js-form-changes-skip text-input")]')
    lead_from_web['contact_name'] = contact_name.get_attribute('value')

    phone_number = driver.find_element_by_xpath('//*[contains(@class, "control-phone__formatted")]')
    lead_from_web['phone_number'] = phone_number.get_attribute('value')
    time.sleep(2)
    email = driver.find_elements_by_xpath(
        '//*[contains(@class,"text-input control--suggest--input '
        'js-control--suggest--input control--suggest--input-inline '
        'linked-form__cf js-linked-pei")]')
    for field in email:
        lead_from_web['email'] = field.get_attribute('value')

    lead_from_db = {'lead_name': find_data_in_mongo(test_name, {"xpath": "xpath_lead_name"})['value'],
                    'contact_name': find_data_in_mongo(test_name, {"xpath": "xpath_contact_name"})['value'],
                    'phone_number': find_data_in_mongo(test_name, {"xpath": "xpath_phone_number"})['value'],
                    'email': find_data_in_mongo(test_name, {"xpath": "xpath_email"})['value']}
    assert lead_from_web == lead_from_db, 'Lead before asserting and after - are different'


def clean_search_and_filter():
    """Clean search and filter"""
    click_on_search_and_filter()
    wait_element_and_send_text('//*[@id="search_input"]', " \n", with_assert=False)
    time.sleep(3)


def press_enter():
    """ Just press 'Enter' """
    wait_element_and_send(
        '//*[contains(@placeholder, "Search and filter")]',
        Keys.ENTER)


def api_fill_entity_with_random_data(fields, resp_users_ids=None, enums=None):
    res = dict()
    for field in fields:
        if enums and field in enums:
            enum_ids = list(enums[field].keys())
        if field in ('name', 'tags', 'company_name'):
            res[field] = random_data()
        elif any(map(lambda s: field.startswith(s), ('Position', 'text_', 'textarea_', 'short address_',
                                                     'Address'))):
            res[field] = [{'value': random_data()}]
        elif field.startswith('numeric_'):
            res[field] = [{'value': randint(1, 99999)}]
        elif field in ('Phone', 'IM'):
            res[field] = [{'value': random_data(), 'enum': 'OTHER'}]
        elif field == 'Email':
            res[field] = [{'value': random_data() + '@example.com', 'enum': 'WORK'}]
        elif field.startswith('checkbox_'):
            res[field] = [{'value': choice((True, False))}]
        elif any(map(lambda s: field.startswith(s), ('select_', 'radiobutton_'))):
            res[field] = [{'value': choice(enum_ids)}]
        elif field.startswith('multiselect_'):
            res[field] = [{'enum': choice(enum_ids)}]
        elif field.startswith('date_'):
            res[field] = [{'value': f'{randint(1, 12)}/{randint(1, 27)}/{randint(1990, 2019)}'}]
        elif field.startswith('birthday_'):
            # res[field] = [{'value': f'{randint(1, 12)}/{randint(1, 27)}/2020'}]
            res[field] = [
                {'value': f'{datetime.date.today().month}/{datetime.date.today().day}/{datetime.date.today().year}'}]
        elif field in ('url_contact', 'Web'):
            res[field] = [{'value': 'http://' + random_data()}]
        elif field == 'addr_contact':
            res[field] = [{'value': random_data(), 'subtype': 'address_line_1'}]
        elif field == 'responsible_user_id':
            res[field] = choice(resp_users_ids)
        else:
            raise NotImplementedError(f'{field} is not implemented yet')
    return res


def api_add_contacts_with_duplicate_fields(test_name, none_same_fields, same_fields):
    """
    create 2 contacts with equal fields via API
    :param test_name: name of collection in db
    :param same_fields: fields you want to be the same
    :type same_fields: list of str or tuple of str
    :param none_same_fields: fields you want to be different
    :type none_same_fields: list of str or tuple of str
    """
    resp_users_ids = api_get_users_ids(test_name)
    sames = api_fill_entity_with_random_data(same_fields, resp_users_ids)
    responses = []
    for _ in range(2):
        none_sames = api_fill_entity_with_random_data(none_same_fields, resp_users_ids)
        if 'responsible_user_id' in none_sames:
            resp_users_ids.remove(none_sames['responsible_user_id'])
        responses.append(api_add_contact(test_name, init_session=False, **sames, **none_sames))
    delete_cookies(test_name)
    return responses


def api_get_users_ids(test_name, init_session=True):
    """
    get available users ids for current account
    :param test_name: name of collection in db
    :param init_session: True if new session
    :type init_session: bool
    :return: tuple of ids
    """
    data = find_data_in_mongo(test_name)
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType,
                             password=None)
    if init_session:
        amo_session.create_session()
    return amo_session.get_users_ids()


def api_add_contact(test_name, name, init_session=True, **additional_fields):
    """
    add contact using api functions
    :param test_name: name of collection
    :param init_session: true if start new session
    :param name: name of contact
    :param additional_fields: optional arguments with names equal to contact fields. More information is here
    https://www.amocrm.ru/developers/content/api/contacts
    For example,
    Phone = [{'value': '123', 'enum': 'WORK'}, {'value': '345', 'enum': 'MOB'}],
    Email = [{'value': 'example@example.moc', 'enum': 'WORK'}, {'value': 'instance@example.moc', 'enum': 'WORK'}],
    IM = [{'value': 'example.example', 'enum': 'SKYPE'}],
    Position = ['Manager'],
    tags = 'tag1,tag2'
    """
    data = find_data_in_mongo(test_name)
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType,
                             password=None)
    if init_session:
        amo_session.create_session()
    return amo_session.add_custom_entity('contacts', {**additional_fields, 'name': name})


def save_contact_to_db(test_name, fields, enums, init_session=True):
    def to_snake_case(s: str):
        return s.lower().replace(' ', '_')

    """
    data = find_data_in_mongo(test_name)
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType,
                             password=None)
    if init_session:
        amo_session.create_session()
    enums = amo_session.get_entity_custom_fields_enums('contacts')
    resp_users = amo_session.get_users_ids()
    fields = api_fill_entity_with_random_data(fields, resp_users, enums)
    response = amo_session.add_custom_entity('contacts', {**fields})
    delete_cookies(test_name)
    drop_collection_from_mongo(test_name)
    """
    fields_to_save = dict()
    for field_name, value in fields.items():
        snake_field = to_snake_case(field_name)
        if field_name == 'multiselect_contact':
            fields_to_save[snake_field] = [enums[field_name][value[i]['enum']] for i in range(len(value))]
        elif field_name in ('name', 'resp_user_id', 'company_name'):
            fields_to_save[snake_field] = value
        elif field_name == 'tags':
            fields_to_save[snake_field] = value.split(',')
        elif field_name in ('select_contact', 'radiobutton_contact'):
            fields_to_save[snake_field] = enums[field_name][value[0]['value']]
        elif field_name in ('date_contact', 'birthday_contact'):
            month, day, year = value[0]['value'].split('/')
            fields_to_save[snake_field] = f'{day}/{month}/{year}'
        else:
            fields_to_save[snake_field] = value[0]['value']
    save_data_to_mongo(test_name, fields_to_save)


def api_add_random_contact(test_name, fields, init_session=True):
    data = find_data_in_mongo(test_name)
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType)
    if init_session:
        amo_session.create_session()
    enums = amo_session.get_entity_custom_fields_enums('contacts')
    resp_users = amo_session.get_users_ids()
    fields = api_fill_entity_with_random_data(fields, resp_users, enums)
    response = amo_session.add_custom_entity('contacts', fields)
    delete_cookies(test_name)
    drop_collection_from_mongo(test_name)

    save_contact_to_db(test_name, fields, enums, init_session)
    return response


def to_contacts_through_buttons():
    """
    go to contact page using buttons, not slide
    """
    wait_element_and_click('//*[contains(@class, "nav__menu__item__icon")][contains(@class, "icon-catalogs")]')
    refresh_page()
    wait_element_and_click('//*[contains(@class, "list-top-nav__text-button-contacts")]')
    wait_element_and_click('//*[contains(@class, "aside__list")]//*[contains(@href, "/contacts/list/contacts")]')


def save_duplicate_contacts_data(test_name, column=(1, 2)):
    """
    save data about the duplicate contacts that is shown in
    contacts -> ... -> find duplicates
    :param test_name: name of the collection
    :param column: number of duplicate columns you would like to save.
                   by default, save both
    :type column: can be int, list or tuple
    """
    contact = dict()
    if not hasattr(column, '__iter__'):
        column = (column,)
    for number in column:
        time.sleep(1.5)
        contact['name'] = driver.find_element_by_xpath(f'(//*[@data-field-code="NAME"])'
                                                       f'[{number}]').text
        contact['resp_user'] = driver.find_element_by_xpath(f'(//*[@data-field-code'
                                                            f'="MAIN_USER_ID"])[{number}]').text
        contact['tags'] = driver.find_element_by_xpath(f'(//*[@data-field-code="TAGS"])'
                                                       f'[{number}]').text.split()
        phones = driver.find_element_by_xpath(f'((//*[contains(@class, "js-merge-main-field")])[7]'
                                              f'//*[contains(@class, "cell__body")])[{number}]') \
            .text.split()
        contact['phones'] = [phone for phone in phones if not phone.startswith('(')]
        emails = driver.find_element_by_xpath(f'((//*[contains(@class, "js-merge-main-field")])[4]'
                                              f'//*[contains(@class, "cell__body")])[{number}]') \
            .text.split()
        contact['emails'] = [email for email in emails if not email.startswith('(')]
        contact['position'] = driver.find_element_by_xpath(f'((//*[contains(@class, "js-merge-main'
                                                           f'-field")])[6]//*[contains(@class, '
                                                           f'"cell__body")])[{number}]').text
        ims = driver.find_element_by_xpath(f'((//*[contains(@class, "js-merge-main-field")])[5]'
                                           f'//*[contains(@class, "cell__body")])[{number}]') \
            .text.split()
        contact['im'] = [im for im in ims if not im.startswith('(')]
        save_data_to_mongo(test_name, contact)
        del contact['_id']


def do_not_take_duplicates():
    """
    press button 'do not take' in duplicates
    """
    wait_element_and_click('//*[contains(@class, "button-input    '
                           'modal-body__actions__not-double")]')
    time.sleep(0.5)


def cancel_find_duplicates():
    """
    press button 'cancel' in duplicates
    """
    try:
        wait_element_and_click('//*[contains(@class, "modal-body__actions")]//*[text()="Cancel"]')
    # if there is no more duplicates
    except common.exceptions.NoSuchElementException:
        time.sleep(1.5)


def check_entities_in_search_filter(test_name, by, presences=None, linked=None):
    """
    search entities from all collection in db (each entity is written on separate field) by name
    :param test_name: name of the collection
    :param presences: values says if an entity must be found ot not
                      IF None, all values are considered to be True
    :param linked: search linked company or linked contact
    :type linked: srt, must be 'contact' or 'company'
    :type presences: list of bool
    :param by: keys in entry you search by
    :type by: list or tuple of str
    """
    entities = find_collection_in_mongo(test_name)
    if not presences:
        presences = [True] * len(entities)
    click_on_search_and_filter()
    if linked == 'contact':
        click_search_linked_contact()
    elif linked == 'company':
        click_search_linked_company()
    for presence, entity in zip(presences, entities):
        for parameter in by:
            # get object with name "search_filter_add_ + parameter" and call it
            # with parameter entity[parameter]
            globals()['search_filter_add_' + parameter](entity[parameter])
        save_search_filters()
        time.sleep(3)
        if presence:
            try:
                driver.find_element_by_xpath('//*[@class="list-row__template-name__name"]')
            except exceptions.NoSuchElementException:
                assert 'This is bug' == 'Is it fixed?', "Search give no result"
        else:
            driver.find_element_by_xpath('//*[@class="list__no-items"]')
        # search_clear_button()


def search_filter_add_phone(phone):
    """
    pass a random phone to 'search filter' in the proper field
    :type phone: str
    """
    click_on_search_and_filter()
    phones_xpath = '//*[@placeholder="Phone"]'
    wait_element_and_send_text(phones_xpath, phone)


def search_filter_add_name(name):
    """
    pass name to 'search filter' in the proper field
    :param name: name
    :type name: str
    """
    click_on_search_and_filter()
    name_xpath = '//*[@name="filter[name]"]'
    wait_element_and_send_text(name_xpath, name)


def search_filter_add_email(emails):
    """
    pass email to 'search filter' in the proper field
    :param emails: emails
    :type emails: list of str
    """
    click_on_search_and_filter()
    emails_xpath = '//*[@placeholder="Email"]'
    wait_element_and_send_text(emails_xpath, emails)


def search_filter_add_im(ims):
    """
    pass im to 'search filter' in the proper field
    :param ims: ims
    :type ims: list of str
    """
    click_on_search_and_filter()
    ims_xpath = '//*[@placeholder="IM"]'
    wait_element_and_send_text(ims_xpath, ims)


def search_filter_add_checkbox_contact(flag):
    click_on_search_and_filter()
    wait_element_and_click('//*[@data-before="checkbox_contact: "]')
    if flag:
        wait_element_and_click('//*[@data-value="Y"]')
    else:
        wait_element_and_click('//*[@data-value="N"]')
    time.sleep(0.5)


def search_filter_add_numeric_contact(number):
    click_on_search_and_filter()
    xpath = '//*[@placeholder="numeric_contact"]'
    wait_element_and_send_text(xpath, number)


def search_filter_add_text_contact(text):
    click_on_search_and_filter()
    xpath = '//*[@placeholder="text_contact"]'
    wait_element_and_send_text(xpath, text)


def search_filter_add_textarea_contact(text):
    click_on_search_and_filter()
    xpath = '//*[@placeholder="textarea_contact"]'
    wait_element_and_send_text(xpath, text)


def search_filter_add_url_contact(url):
    click_on_search_and_filter()
    xpath = '//*[@placeholder="url_contact"]'
    wait_element_and_send_text(xpath, url)


def search_filter_add_select_contact(contact):
    click_on_search_and_filter()
    wait_element_and_click('//*[@data-before="select_contact: "]')
    wait_element_and_click(f'//*[contains(@data-before, "select_contact: ")]/..//*[contains(text(), "{contact}")]')


def search_filter_add_radiobutton_contact(contact):
    click_on_search_and_filter()
    wait_element_and_click('//*[@data-before="radiobutton_contact: "]')
    wait_element_and_click(f'//*[@data-before="radiobutton_contact: "]/..//*[contains(text(), "{contact}")]')


def search_filter_add_multiselect_contact(contacts):
    click_on_search_and_filter()
    wait_element_and_click('//*[@data-title-before="multiselect_contact: "]')
    for contact in contacts:
        wait_element_and_click(
            f'//*[@data-title-before="multiselect_contact: "]/../../../..//*[contains(@title, "{contact}")]')


def search_filter_add_date_contact(date):
    click_on_search_and_filter()
    wait_element_and_send('//*[@placeholder="date_contact"]', date)


def search_filter_add_birthday_contact(date):
    click_on_search_and_filter()
    wait_element_and_click('//*[@placeholder="birthday_contact"]')
    wait_element_and_send('//*[@placeholder="birthday_contact"]', date)


def search_filter_add_addr_contact(addr):
    click_on_search_and_filter()
    wait_element_and_send('//*[@placeholder="Address line 1 (contact)"]', addr)


def search_filter_add_short_address_contact(addr):
    click_on_search_and_filter()
    wait_element_and_send('//*[@placeholder="short address_contact"]', addr)


def search_filter_add_tags(tags):
    """
    pass tags to 'search filter' in the proper field
    :param tags: tags
    :type tags: list of str
    """
    click_on_search_and_filter()
    tag_xpath = '//*[@placeholder="Find tags"]'
    for number, tag in enumerate(tags, 1):
        wait_element_and_send_text(tag_xpath, tag)
        time.sleep(0.5)
        wait_element_and_click(f'(//*[contains(@class, "tags-lib__item-name")])[{number}]')
        time.sleep(0.5)


def search_filter_add_assign_user(resp_user):
    """
    pass assign (responsible) user to 'search filter' in the proper field
    :param resp_user: assign (responsible) user
    :type resp_user: str
    """
    click_on_search_and_filter()
    resp_user_xpath = '//*[@data-title="Assigned users"]//*[@id="filter_users_select__holder"]'
    wait_element_and_click(resp_user_xpath)
    wait_element_and_send_text(resp_user_xpath + '//input', resp_user)


def search_filter_add_lead_name(lead_name):
    """
    pass lead name to 'search filter' in leads tab
    :type lead_name: str
    """
    click_on_search_and_filter()
    lead_name_xpath = '//*[@name="filter[name]"]'
    wait_element_and_send_text(lead_name_xpath, lead_name)


def find_collection_in_mongo(test_name):
    """
    :param test_name: name of the collection you save to
    :type test_name: str
    :return: list of fields from mongo
    """
    data = list()
    client = MongoClient('mongo', 27017)
    db = client['selenium_tests']
    for field in db[test_name].find():
        data.append(field)
    return data


def change_priorities_in_duplicates():
    """
    choosing the other name and responsible user in 'find duplicates'
    """
    name = driver.find_element_by_xpath('(//*[@data-field-code="NAME"])[2]').text
    wait_element_and_click('(//*[@name="result_element[NAME]"])[2]')
    check_text_of_element('//*[@id="NAME"]', name)
    resp_user = driver.find_element_by_xpath('(//*[@data-field-code="MAIN_USER_ID"])[2]').text
    wait_element_and_click('(//*[@name="result_element[MAIN_USER_ID]"])[2]')
    check_text_of_element('//*[@id="MAIN_USER_ID"]', resp_user)


def save_merged_contacts_data(test_name):
    """
    save data about the merged contact that is shown in
    contacts -> ... -> find duplicates
    :param test_name: name of the collection you save to
    :type test_name: str
    """
    contact = dict()
    contact['name'] = driver.find_element_by_xpath('//*[@id="NAME"]').text
    contact['resp_user'] = driver.find_element_by_xpath('//*[@id="MAIN_USER_ID"]').text
    contact['tags'] = driver.find_element_by_xpath('//*[@id="TAGS"]').text.split()
    phones = driver.find_element_by_xpath('(//*[@class="form-result"])[5]').text.split()
    contact['phones'] = [phone for phone in phones if not phone.startswith('(')]
    emails = driver.find_element_by_xpath('(//*[@class="form-result"])[4]').text.split()
    contact['emails'] = [email for email in emails if not email.startswith('(')]
    contact['position'] = driver.find_element_by_xpath('(//*[@class="form-result"])[7]').text
    ims = driver.find_element_by_xpath('(//*[@class="form-result"])[6]').text.split()
    contact['ims'] = [im for im in ims if not im.startswith('(')]
    save_data_to_mongo(test_name, contact)


def api_add_custom_lead(test_name, lead_name, init_session=True, **additional_fields):
    """
    add lead using api functions
    :param test_name: name of collection
    :param init_session: true if start new session
    :param lead_name: name of contact
    :param additional_fields: optional arguments with names equal to contact fields
    :return: api response
    """
    data = find_data_in_mongo(test_name)
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType,
                             password=None)
    if init_session:
        amo_session.create_session()
    return amo_session.add_custom_entity('leads', {**additional_fields, 'name': lead_name})


def click_search_linked_contact():
    wait_element_and_click('(//*[contains(@class,"js-filter-search__entity-header")])[2]')


def click_search_linked_company():
    wait_element_and_click('(//*[contains(@class,"js-filter-search__entity-header")])[3]')


def create_company_contact_lead_task(test_name):
    data = find_data_in_mongo(test_name)
    amo_session = AmoSession(test_name=test_name,
                             subdomain=data['subdomain'],
                             login=data['login'],
                             api_key=data['api_key'],
                             srv_type=ServerType)
    amo_session.create_session()
    company_enums = amo_session.get_entity_custom_fields_enums('companies')
    company_fields = api_fill_entity_with_random_data(('name', 'Phone', 'Email', 'Web', 'Address'),
                                                      enums=company_enums)
    company = amo_session.add_custom_entity('companies', company_fields)
    contact_enums = amo_session.get_entity_custom_fields_enums('contacts')
    contact_fields = api_fill_entity_with_random_data(
        ('name', 'company_name', 'Phone', 'Email', 'Position', 'IM',
         'text_contact', 'numeric_contact', 'checkbox_contact',
         'select_contact', 'multiselect_contact', 'date_contact',
         'url_contact', 'textarea_contact', 'radiobutton_contact',
         'short address_contact', 'addr_contact', 'birthday_contact'),
        enums=contact_enums
    )
    contact = amo_session.add_custom_entity('contacts', contact_fields)
    contact_id = contact['_embedded']['items'][0]['id']
    company_id = company['_embedded']['items'][0]['id']
    lead = amo_session.add_custom_entity('leads', {'name': random_data(), 'company_id': company_id,
                                                   'sale': 100, 'contacts_id': contact_id})
    lead_id = lead['_embedded']['items'][0]['id']
    amo_session.add_custom_entity('tasks', dict(text=random_data(), element_id=lead_id, element_type=2))
    delete_cookies(test_name)
    drop_collection_from_mongo(test_name)

    save_contact_to_db(test_name, contact_fields, contact_enums)


def create_duplicate_contacts_with_leads(test_name):
    responses = api_add_contacts_with_duplicate_fields(test_name,
                                                       ('name',),
                                                       ('Phone', 'Email'))
    for response in responses:
        contact_id = response['_embedded']['items'][0]['id']
        api_add_custom_lead(test_name,
                            random_data(),
                            contacts_id=contact_id)
        delete_cookies(test_name)


def find_element_in_list(xpath_list):
    elements = driver.find_elements_by_xpath(xpath=xpath_list)
    element = random.choice(elements)
    return element


def add_():
    # leads -> pipline -> new_deal
    wait_element_and_click("//a[contains(@class,'button-input button-input_add button-input_add-lead "
                           "content-table__name-link button-input_blue js-navigate-link')]")


def add_fields_in_deal():
    time.sleep(3)
    try:
        add_btns = driver.find_elements_by_xpath("//div[contains(@class,'cf-field-add js-card-cf-add-field')]")
        save_btn = "//div[contains(@class,'cf-field-wrapper__body edit-mode')]//span[contains(@class,'button-input-inner__text')]"
        # todo подтягивать месседж из массива
        # добавление текстового поля в три раздела
        for _ in range(3):
            wait_element_and_click(webelement=add_btns[_])
            time.sleep(5)
            wait_element_and_send(xpath="//input[contains(@placeholder,'Название поля')]", message='Тестовое название')
            wait_element_and_click(xpath=save_btn)
            time.sleep(3)

    except BaseException:
        logger.exception(
            'Необходимо удалить тестовые настройки (вероятна была создана и не удалена тестовая группа) и запустить тест заново')


SCENARIO_FILL_NAME = {
    'in_deal': {'deal': {'name': {'xpath': "//input[@id='person_n']",
                                  'message': fake.word},
                         'extra_fields': {
                             'xpath': "//div[@class='linked-forms__group-wrapper linked-forms__group-wrapper_main js-cf-group-wrapper']//input",
                             'message': fake.word}},

                'contact': {'name': {'xpath': "//input[contains(@placeholder,'Добавить контакт')]",
                                     "message": fake.name},
                            'work_mob': {
                                'xpath': "//div[@id='new_contact_form']//input[contains(@class, 'control-phone__formatted')]",
                                'message': fake.phone_number},
                            'work_email': {
                                'xpath': "//div[@id='new_contact_form']//input[@class='text-input control--suggest--input js-control--suggest--input-ajax linked-form__cf js-linked-pei']",
                                'message': fake.email},
                            'extra_fields': {
                                'xpath': "//div[@id='new_contact_form']//input[@class='linked-form__cf text-input']",
                                'message': fake.word}},

                'company': {'name': {'xpath': "//input[contains(@placeholder,'Добавить компанию')]",
                                     'message': fake.company},
                            'work_mob': {
                                'xpath': "//div[@id='new_company_form']//input[contains(@class, 'control-phone__formatted')]",
                                'message': fake.phone_number},
                            'work_email': {
                                'xpath': "//div[@id='new_company_form']//input[@class='text-input control--suggest--input js-control--suggest--input-ajax linked-form__cf js-linked-pei']",
                                'message': fake.company_email},
                            'extra_fields': {
                                'xpath': "//div[@id='new_company_form']//input[@class='linked-form__cf text-input']",
                                'message': fake.word}}
                },
    'sec_contact': {'sec_cont': {'name': {'xpath': "//input[contains(@placeholder,'Добавить контакт')]",
                                          "message": fake.name},
                                 'work_mob': {
                                     'xpath': "//form[@id='new_contact']//input[contains(@class,'control-phone__formatted js-form-changes-skip linked-form__cf js-linked-pei text-input')]",
                                     'message': fake.phone_number},
                                 'work_email': {
                                     # 'xpath': "//body//div[@id='new_contact_form']//div//div//div[2]//div[1]//div[2]//div[1]//div[1]//input[1]",
                                     'xpath': "//div[@id='new_contact_form']//input[@class='text-input control--suggest--input js-control--suggest--input-ajax linked-form__cf js-linked-pei']",
                                     'message': fake.email},
                                 'extra_fields': {
                                     'xpath': "//div[@id='new_contact_form']//input[@class='linked-form__cf text-input']",
                                     'message': fake.word}}
                    },
    'in_contact': {'contact': {'name': {'xpath': "//input[@placeholder='Имя Фамилия']",
                                        'message': fake.name},
                               'work_mob': {
                                   'xpath': "//div[contains(@class, 'linked-forms__group-wrapper_main')]//input[contains(@class, 'control-phone__formatted')]",
                                   'message': fake.phone_number},
                               'work_email': {
                                   'xpath': "//*[@id='edit_card']/div/div[4]/div[2]/div[1]/div[2]/div/div[1]/input",
                                   'message': fake.email},
                               'extra_fields': {
                                   'xpath': "//div[@class='linked-forms__group-wrapper linked-forms__group-wrapper_main js-cf-group-wrapper']//div[@class='linked-form__field linked-form__field-text ']//input",
                                   'message': fake.word}},

                   'company': {'name': {'xpath': "//input[contains(@placeholder,'Добавить компанию')]",
                                        'message': fake.company},
                               'work_mob': {
                                   'xpath': "//div[@id='new_company_form']//input[contains(@class, 'control-phone__formatted')]",
                                   'message': fake.phone_number},
                               'work_email': {
                                   'xpath': "//div[@id='new_company_form']//input[@class='text-input control--suggest--input js-control--suggest--input-ajax linked-form__cf js-linked-pei']",
                                   'message': fake.company_email},
                               'extra_fields': {
                                   'xpath': "//div[@id='new_company_form']//input[@class='linked-form__cf text-input']",
                                   'message': fake.word}}
                   },
    'in_company': {'company': {'name': {'xpath': "//input[@id='person_n']",
                                        'message': fake.company},
                               'work_mob': {
                                   'xpath': "//div[contains(@class, 'linked-forms__group-wrapper_main')]//input[contains(@class, 'control-phone__formatted')]",
                                   'message': fake.phone_number},
                               'work_email': {
                                   'xpath': "//*[@id='edit_card']/div/div[4]/div[2]/div[1]/div[2]/div/div[1]/input",
                                   'message': fake.company_email},
                               'extra_fields': {
                                   'xpath': "//div[@class='linked-forms__group-wrapper linked-forms__group-wrapper_main js-cf-group-wrapper']//div[@class='linked-form__field linked-form__field-text ']//input",
                                   'message': fake.word}},

                   'contact': {'name': {'xpath': "//input[contains(@placeholder,'Добавить контакт')]",
                                        "message": fake.name},
                               'work_mob': {
                                   'xpath': "//div[@id='new_contact_form']//input[contains(@class, 'control-phone__formatted')]",
                                   'message': fake.phone_number},
                               'work_email': {
                                   'xpath': "//div[@id='new_contact_form']//input[@class='text-input control--suggest--input js-control--suggest--input-ajax linked-form__cf js-linked-pei']",
                                   'message': fake.email},
                               'extra_fields': {
                                   'xpath': "//div[@id='new_contact_form']//input[@class='linked-form__cf text-input']",
                                   'message': fake.word}},
                   },
}


def fill_fields_in_essence(scenario, test_name):
    time.sleep(2)
    data_save = []
    try:
        for essence in SCENARIO_FILL_NAME[scenario]:

            if essence == 'deal':
                deal_name = SCENARIO_FILL_NAME[scenario][essence]['name']['message']()
                deal_text = SCENARIO_FILL_NAME[scenario][essence]['name']['message']()
                main_fields = driver.find_elements_by_xpath(
                    SCENARIO_FILL_NAME[scenario][essence]['extra_fields']['xpath'])

                main_fields[2].send_keys(deal_text)
                wait_element_and_send(xpath=SCENARIO_FILL_NAME[scenario][essence]['name']['xpath'],
                                      message=deal_name)

                data_save.append({essence: {'deal_name': str(deal_name),
                                            'deal_text': str(deal_text)}})
            else:
                name = SCENARIO_FILL_NAME[scenario][essence]['name']['message']()
                tel = SCENARIO_FILL_NAME[scenario][essence]['work_mob']['message']()
                email = SCENARIO_FILL_NAME[scenario][essence]['work_email']['message']()
                wait_element_and_send(xpath=SCENARIO_FILL_NAME[scenario][essence]['name']['xpath'],
                                      message=name)
                time.sleep(0.5)

                wait_element_and_send(xpath=SCENARIO_FILL_NAME[scenario][essence]['work_mob']['xpath'],
                                      message=tel)
                time.sleep(0.5)

                wait_element_and_send(xpath=SCENARIO_FILL_NAME[scenario][essence]['work_email']['xpath'],
                                      message=email)
                time.sleep(0.5)

                fields_extra = driver.find_elements_by_xpath(
                    SCENARIO_FILL_NAME[scenario][essence]['extra_fields']['xpath'])
                time.sleep(0.5)
                fields_extra[0].send_keys(SCENARIO_FILL_NAME[scenario][essence]['extra_fields']['message']())
                fields_extra[1].send_keys(SCENARIO_FILL_NAME[scenario][essence]['extra_fields']['message']())
                fields_extra[2].send_keys(SCENARIO_FILL_NAME[scenario][essence]['extra_fields']['message']())
                data_save.append({essence: {'name': str(name),
                                            'tel': str(tel),
                                            'email': str(email)}})
            json_write(essence, data_save)
        wait_element_and_click(controller='save_btn')
        time.sleep(0.5)
    except exceptions:
        logger.exception('Не удалось создать сущность')


def make_sec_cont_main():
    try:
        # клик на второй контакт
        wait_element_and_click(xpath="//body/div/div/div/div/div/div/ul/li[2]/form[1]/div[1]")
        time.sleep(5)
        # открываем опции контакта
        wait_element_and_click(
            "//body/div/div/div/div/div/div/ul/li[2]/form[1]/div[1]/div[2]/div[1]/span[1]")
        wait_element_and_click("//li[2]//form[1]//div[1]//div[2]//div[1]//span[1]//div[1]//div[1]//div[4]")
        # говорим да в окошке подтверждения действия
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//span[contains(@class,'button-input-inner__text')]")
        time.sleep(2)
    except TimeoutException:
        logger.exception('Ожидание заданного элемента было привышено')
    except NoSuchElementException:
        logger.exception('Элемент не был найден на странице')
    except UnexpectedAlertPresentException:
        logger.exception('Несогласованная логика')
        close_connections()
    except exceptions:
        logger.exception("Не удалось сделать второй контакт главным")


def change_resp_user():
    try:
        # меняем ответственного
        wait_element_and_click(
            xpath="//div[contains(@class,'multisuggest users_select-select_one card-fields__fields-block__users-select js-multisuggest js-can-add')]//span")
        time.sleep(2)

        wait_element_and_send(xpath="//input[contains(@class,'multisuggest__input js-multisuggest-input')]",
                              message='testom', keys_return=True)
        time.sleep(2)
        wait_element_and_click(controller='save_btn')
        time.sleep(2)
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//button[contains(@class,'js-modal-accept js-button-with-loader modal-body__actions__save')]")
        time.sleep(3)
    except TimeoutException:
        logger.exception('Ожидание заданного элемента было привышено')
    except NoSuchElementException:
        logger.exception('Элемент не был найден на странице')

    except exceptions:
        logger.exception('Не удалось изменить ответственного')


def save_current_url():
    return driver.current_url


def go_to_url(url):
    driver.get(url)


def check_feed(*essences, xpath=None):
    feed_content_xpaths = {'comp': "//div[contains(@class, 'feed-note-wrapper-company_created')]",
                           'cont': "//div[contains(@class, 'feed-note-wrapper-contact_created')]",
                           'lead': "//div[contains(@class, 'feed-note-wrapper-lead_created')]",
                           'resp_user': "//div[contains(@class, 'feed-note-wrapper-main_user_changed')]"}
    time.sleep(2)
    try:
        if xpath:
            wait_element_and_click(xpath)
            time.sleep(0.5)
        for essence in essences:
            driver.find_element_by_xpath(feed_content_xpaths[essence])
    except exceptions.NoSuchElementException as exp:
        assert 'Message: no such element: Unable to locate element:' in str(exp)
        logger.exception('В фиде нет информации о созданной сущности')


def add_notes():
    # add pic
    # todo решить вопрос с путем к необходимым файлам
    try:
        wait_element_and_click("//div[@class='js-note feed-compose_note']")
        time.sleep(2)

        wait_element_and_send(xpath="//input[@name='UserFile']",
                              message='/home/amitroshina/PycharmProjects/qa/selenium_tests/for_test/test_img.jpg')
        time.sleep(2)
        wait_element_and_click("//button[contains(@class,'js-note-submit feed-note__button')]")
        time.sleep(5)
        wait_element_and_send(xpath="//div[@class='control-contenteditable__area feed-compose__message']",
                              message='тестовое примечание')
        time.sleep(2)
        wait_element_and_click("//button[contains(@class,'js-note-submit feed-note__button')]")
    except exceptions:
        logger.exception('Ошибка в добавлении примечаний')


def create_extra_group():
    try:
        # wait_element_and_click(controller="card_settings_in")
        time.sleep(3)
        # клик на создать (иконка плюса)
        wait_element_and_click(
            "//div[@class='card-cf__tabs js-card-cf-tabs ui-sortable']//div[@class='card-tabs__item js-card-tab']//span[@class='card-tabs__item-inner']")

        # наименование
        wait_element_and_send(xpath="//div[@id='bookmarks-sort']//input[contains(@placeholder,'Название')]",
                              message='Тестовая группа')
        # клик на сохранить
        wait_element_and_click(xpath="//div[contains(@class,'modal-body__inner')]"
                                     "//button[contains(@class,'js-modal-accept js-button-with-loader "
                                     "modal-body__actions__save')]")

    except exceptions:
        logger.exception('Не удалось создать доп группу')


def create_extra_fields():
    try:

        # клик на созданную группу
        groups = driver.find_elements_by_xpath("//span[text()='Тестовая группа']")
        wait_element_and_click(webelement=groups[0])

        # wait_element_and_click(xpath="//div[contains(@class,'card-tabs__item js-card-tab js-sortable js-droppable ui-droppable')]")
        time.sleep(0.5)
        # создание поля1
        # клик на добавить поле
        add_field = [i for i in driver.find_elements_by_xpath('//*[@class="cf-field-add js-card-cf-add-field"]') if
                     i.is_displayed()][0]
        wait_element_and_click(webelement=add_field)

        wait_element_and_send(xpath="//input[contains(@placeholder,'Название поля')]",
                              message='Поле1')
        wait_element_and_click("//div[contains(@class,'control--select cf-field-edit__statuses')]"
                               "//button[contains(@class,'control--select--button')]")
        # делаем поле обязательным
        wait_element_and_click("//div[contains(@class,'cf-field-edit__body-top')]//li[2]")

        # сохранить
        wait_element_and_click("//div[contains(@class,'cf-field-wrapper__body edit-mode')]"
                               "//button[contains(@class,'js-modal-accept js-button-with-loader "
                               "modal-body__actions__save button-input_blue')]")
        # создание поля2
        wait_element_and_click(webelement=add_field)

        time.sleep(3)
        wait_element_and_send(xpath="//input[contains(@placeholder,'Название поля')]",
                              message='Поле2')
        wait_element_and_click("//div[contains(@class,'control--select cf-field-edit__type-select')]"
                               "//button[contains(@class,'control--select--button')]")
        wait_element_and_click("//div[contains(@class,'control--select cf-field-edit__type-select')]//li[2]")

        # сохранить
        wait_element_and_click("//div[contains(@class,'cf-field-wrapper__body edit-mode')]"
                               "//button[contains(@class,'js-modal-accept js-button-with-loader "
                               "modal-body__actions__save button-input_blue')]")

        # выходим из настроек
        time.sleep(5)
        # wait_element_and_click(controller="card_settings_out")
    except exceptions:
        logger.exception('Не удалось создать дополнительные поля')


def delete_extra_fields():
    try:
        wait_element_and_click(controller="card_settings_in")
        # переход в группу
        groups = driver.find_elements_by_xpath("//span[text()='Тестовая группа']")

        wait_element_and_click(webelement=groups[0])
        time.sleep(4)
        fields = driver.find_elements_by_class_name('cf-field-wrapper__inner')
        fields_displayed = [f for f in fields if f.is_displayed()]
        for f in fields_displayed:
            wait_element_and_click(webelement=f)
            time.sleep(2)
            wait_element_and_click("//div[contains(@class,'cf-field-edit__remove js-modal-trash')]")
            wait_element_and_click(
                "//div[contains(@class,'modal-body__inner')]//button[contains(@class,'js-modal-accept js-button-with-loader modal-body__actions__save')]")
            time.sleep(3)

    except IndexError:
        logger.exception('Тестовые группы отсутсвуют в карточке')

    except exceptions:
        logger.exception('Не удалось удалить дополнительные поля в доп группе')


def delete_extra_group():
    try:
        wait_element_and_click(
            "//div[contains(@class,'card-tabs__item js-card-tab js-sortable js-droppable ui-droppable selected')]//span[contains(@class,'js-tab-remove')]//*[local-name()='svg']")
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//button[contains(@class,'js-modal-accept js-button-with-loader modal-body__actions__save')]")
        time.sleep(5)
        # выход из настроек
        # wait_element_and_click(controller="card_settings_out")
    except NoSuchElementException:
        logger.exception('Элемент не был найден на странице')
    except exceptions:
        logger.exception('Не удалось удалить дополнительную группу')


def unpin_cont():
    try:
        # открепление основного контакта
        wait_element_and_click(
            "//body/div/div/div/div/div/div/ul/li[1]/form[1]/div[1]/div[2]/div[1]/span[1]/span[1]")
        time.sleep(3)
        wait_element_and_click("//body//div//div//div//div//div//div//span//div[3]")

        time.sleep(5)
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//button[contains(@class,'js-modal-accept js-button-with-loader modal-body__actions__save')]")
        time.sleep(3)
        # открепление второго контакта
        # клик на контакт
        wait_element_and_click("//ul[@id='contacts_list']")

        # удаляем
        wait_element_and_click("//ul/li/form/div/div[2]/div[1]/span[1]")
        time.sleep(3)
        wait_element_and_click("//body//div//div//div//div//div//div//span//div[3]")
        # нажимаем да в диалоговорм окне
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//span[contains(@class,'button-input-inner__text')]")

        time.sleep(3)
        # открепляем контакт
        wait_element_and_click(
            "//form[contains(@class,'linked-form')]//div[contains(@class,'linked-form__field linked-form__field-name')]")
        wait_element_and_click("//div[contains(@class,'tips-item js-tips-item js-linked-entity-unlink')]")

        time.sleep(3)
        # нажимаем да в диалоговом окне
        # wait_element_and_click(
        #     "//div[contains(@class,'modal-body__inner')]//button[contains(@class,'js-modal-accept js-button-with-loader modal-body__actions__save')]")
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//span[contains(@class,'button-input-inner__text')]")

        time.sleep(4)

    except exceptions:
        logger.exception('Не удалось открепить контакт')


def unpin_comp():
    try:
        wait_element_and_click("//span[@class='icon icon-inline icon-dots-2']")
        wait_element_and_click("//div[contains(@class,'tips-item js-tips-item js-linked-entity-unlink')]")
        time.sleep(3)
        # нажимаем да в диалоговом окне
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//button[contains(@class,'js-modal-accept js-button-with-loader modal-body__actions__save')]")
        time.sleep(4)
    except exceptions:
        logger.exception('Не удалось открепить компанию')


def unpin_cont_in_comp():
    try:
        wait_element_and_click(xpath="//ul[@id='contacts_list']"
                                     "//span[contains(@class,'icon icon-inline icon-dots-2')]")
        wait_element_and_click("//div[contains(@class,'tips-item js-tips-item js-linked-entity-unlink')]")
        time.sleep(3)
        # нажимаем да в диалоговом окне
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//button[contains(@class,'js-modal-accept js-button-with-loader modal-body__actions__save')]")
        time.sleep(4)
    except exceptions:

        logger.exception('Не удалось открепить компанию')


def delete_deal():
    try:
        wait_element_and_click(
            "//div[contains(@class,'button-input-wrapper button-input-more')]//button[contains(@class,'')]")
        time.sleep(3)
        wait_element_and_click(
            "//li[contains(@class,'element__delete-trash')]//span[contains(@class,'button-input__context-menu__item__text')]")
        time.sleep(3)
        # нажимаем поддтвердить в диалоговом окне
        wait_element_and_click(
            "//div[contains(@class,'modal-body__inner')]//button[contains(@class,'js-modal-accept js-button-with-loader modal-body__actions__save')]")

    except exceptions:
        logger.exception('Не удалось удалить сделку')


def fill_extra_fields_extra_group():
    try:
        time.sleep(2)
        # переходим в созданную группу
        # wait_element_and_click("//div[@id='card_tabs']//span[contains(text(), 'Тестовая группа')]")

        # заполняем поле2
        wait_element_and_send(
            xpath="//input[@class='linked-form__cf js-control-allow-numeric-float text-input']",
            message='532')

        # попытка сохранить
        wait_element_and_click(
            xpath="//button[@id='save_and_close_contacts_link']//span[contains(@class,'button-input-inner__text')]")
        wait_element_and_click(xpath="//span[contains(@class,'validation-button-cap__arrow right')]")

        # заполняем обязательное
        wait_element_and_send(
            xpath="//div[contains(@class,'validation-not-valid')]//input[@class='linked-form__cf text-input']",
            message="текст")
        time.sleep(5)
        # сохраняем
        wait_element_and_click("//button[@id='save_and_close_contacts_link']")
    except exceptions:
        logger.exception('Не удалось заполнить дополнительные поля дополнительной группы')


def check_pic():
    try:
        wait_element_and_click("//a[contains(@class,'feed-note__media-preview')]")
        time.sleep(2)
        # закрываем картинку
        wait_element_and_click(
            "//button[contains(@class,'mfp-close mfp-close_image-button')]//*[local-name()='svg']")
        time.sleep(2)
    except exceptions:
        logger.exception('Не удалось проверить картинку')


def fill_main_fields_in_contact():
    name_contact = fake.name()
    work_mob = fake.phone_number()
    work_email = fake.email()

    wait_element_and_send(xpath="//input[@id='person_n']", message=name_contact)
    wait_element_and_send(xpath="//div[contains(@class,'linked-forms__group-wrapper "
                                "linked-forms__group-wrapper_main js-cf-group-wrapper')]"
                                "//input[contains(@class,'control-phone__formatted js-form-changes-skip "
                                "linked-form__cf js-linked-pei text-input')]",
                          message=work_mob)
    wait_element_and_send(xpath='//*[@id="edit_card"]/div/div[4]/div[2]/div[1]/div[2]/div/div[1]/input',
                          message=work_email)
    time.sleep(0.5)
    wait_element_and_click(controller='save_btn')


def create_comp_fields_in_contact():
    name_comp = fake.company()
    work_mob = fake.phone_number()
    work_email = fake.company_email()
    address = fake.street_address()
    web_comp = fake.domain_name(levels=1)

    wait_element_and_send(xpath="//input[@id='new_company_n']",
                          message=name_comp)
    wait_element_and_send(xpath="//div[contains(@class,'linked-form__fields')]//input[@class='control-phone__formatted "
                                "js-form-changes-skip linked-form__cf js-linked-pei text-input']",
                          message=work_mob)
    wait_element_and_send(xpath='//*[@id="new_company"]/div[2]/div/div[2]/div[1]/div[2]/div/div[1]/input',
                          message=work_email)
    wait_element_and_send(xpath='//*[@id="new_company"]/div[2]/div/div[3]/div[2]/div/input',
                          message=web_comp)
    wait_element_and_send(xpath='//*[@id="new_company"]/div[2]/div/div[4]/div[2]/div/textarea',
                          message=address)
    time.sleep(0.5)

    wait_element_and_click(controller='save_btn')


def create_deal_in_essence():
    try:
        wait_element_and_click(xpath="//div[contains(@class,'pipeline_leads__quick_add_button_inner')]")

        name_deal = fake.word()
        budget_deal = fake.random_int()

        wait_element_and_send(xpath="//input[@id='quick_add_lead_name']",
                              message=name_deal)
        wait_element_and_send(xpath="//input[@id='quick_add_lead_budget']",
                              message=budget_deal)

        time.sleep(0.5)
        wait_element_and_click(xpath="//button[@id='quick_add_form_btn']")
    except exceptions:
        logger.exception('Не удалось создать сделку в контакте')


def get_text_in_element(xpath):
    return driver.find_element(By.XPATH, xpath=xpath).text


def add_essence():
    try:
        time.sleep(2)
        wait_element_and_click(controller="create_btn")
        time.sleep(2)
    except NoSuchElementException:
        logger.exception('Элемент не был найден на странице')
    except exceptions:
        logger.exception('Ошибка в нахожении кнопки "Создать сделку/контакт/компанию')


def make_favorite_note():
    # второе вложение делаем главным
    try:
        notes = driver.find_elements_by_xpath("//div[contains(@class, 'feed-note-wrapper feed-note-wrapper-note')]")
        mouse_to_element(elem=notes[1])
        # notes[1].find_element_by_class_name("feed-note__context-container").click().perform()
        time.sleep(10)
        # driver.find_element_by_css_selector('.feed-note__context_opened > .pinner').click().perform()
        wait_element_and_click("//div[4]/div/div/div[3]/div/div/span")
        time.sleep(10)
    except exceptions:
        logger.exception('Не удалось сделать примечание главным')


def check_style_note():
    el = driver.find_element_by_css_selector(".feed-note-wrapper-bill_paid .feed-note_pinned, "
                                             ".feed-note-wrapper-geolocation .feed-note_pinned, .feed-note-wrapper-note "
                                             ".feed-note_pinned, .feed-note-wrapper-payed_1c .feed-note_pinned, "
                                             ".feed-note-wrapper-payed_quickbooks .feed-note_pinned").value_of_css_property(
        'border-color')
    if el != 'rgb(254, 170, 24)':
        raise MyException('Стиль примечания не соответствует ожидаемому')


def choose_deal_in_pipeline():
    stages_in__pipeline = {
        'unsorted': '//*[contains(@class, "pipeline_cell-unsorted")]//div[contains(@class, "pipeline_leads__item")]'
    }
    try:
        deal = find_element_in_list(xpath_list=stages_in__pipeline['unsorted'])

        wait_element_and_click(webelement=deal)
    except exceptions:
        logger.exception('ошибка в нахождении и открытии сделки из пайплана')


def check_name_essence(test_name, after=False):
    field_name_xpath = "//textarea[@id='person_n']"

    try:
        if after:
            name_after = driver.find_element_by_xpath(xpath=field_name_xpath).text
            before_name = json_read(test_name)['name_deal']
            if name_after == before_name:
                return True
            else:
                raise MyException("Неверное имя сделки")

        before_accept = driver.find_element_by_xpath(xpath=field_name_xpath).text
        data = {'name_deal': before_accept}
        json_write(test_name, data)

    except exceptions:
        logger.exception('ошибка в наименовании сделки после accept')


def get_name_deal(xpath):
    name = driver.find_element_by_xpath(xpath=xpath).text
    return name


def json_write(test_name, data):
    with open(f'jsons/{test_name}.json', "a") as file:
        json.dump(data, file, indent=4)


def json_read(test_name):
    with open(f'jsons/{test_name}.json', "r") as file:
        json_data = json.load(file)

    return json_data

get_text_in_element('//*[@id="save_and_close_contacts_link"]/span/span')