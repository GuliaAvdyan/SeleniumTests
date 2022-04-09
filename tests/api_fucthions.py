
import time
import os
import json
import datetime
import pickle
from random import choice
import string
import requests
from pymongo import MongoClient
from customs import CustomEntity


class AmoSession:
    """ This class create Amo session by api """
    headers = {'content-type': 'application/json'}
    session = requests.Session()

    def __init__(self, test_name, subdomain, login, api_key, srv_type, password=None):
        # test name
        self.test_name = test_name
        # account subdomain
        self.subdomain = subdomain
        # account login
        self.login = login
        # account api key (see in account profile)
        self.api_key = api_key
        if srv_type == 'PROD_USA':
            self.domain = 'com'
        else:
            self.domain = 'ru'
        self.password = password

    def create_session(self, init_mongo=False, use_password=False):
        """ Create authorization session and return cookies """
        # Make a authorization request
        if use_password:
            url = 'https://www.amocrm.{0}'.format(self.domain)
            csrf_token = requests.get(url)
            csrf_token = csrf_token.cookies['csrf_token']
            post_data = {'username': self.login,
                         'password': self.password,
                         'csrf_token': csrf_token}
        else:
            post_data = {'USER_LOGIN': self.login,
                        'USER_HASH': self.api_key}
        # Create a session
        if use_password:
            created_session = self.session.post(
                'https://{0}.amocrm.{1}/oauth2/authorize'.format(self.subdomain, self.domain),
                data=post_data)
        else:
            created_session = self.session.post(
                'https://{0}.amocrm.{1}/private/api/auth.php'.format(self.subdomain, self.domain),
                data=post_data)
        created_session.raise_for_status()
        # Save cookie as
        AmoSession.save_cookies_name(self.test_name,
                                     created_session.cookies,
                                     init_mongo)

    def add_lead(self, lead_name, company_id=None, contact_id=None,
                 tags=None, sale=None):
        """ Add lead by api and return request response as json
        Parameters:
        :lead_name - str, lead name.
        :company_id - id of the company to be attached to the lead
        :contact_id - id of the contact to be attached to the lead
        :tags - list of str with tag names (only for new tags)
        :sale - int, sale
        """
        post_data = dict()
        post_data['add'] = [{'name': lead_name}]
        if company_id:
            post_data['add'][0]['company_id'] = company_id
        if contact_id:
            post_data['add'][0]['contacts_id'] = list([contact_id])
        # Add tags
        if tags:
            post_data['add'][0]['tags'] = ','.join(tags)
        if sale:
            assert int(sale)
            # Add sale
            post_data['add'][0]['sale'] = sale
        # load cookies
        cookies = AmoSession.load_cookies(self.test_name)
        # Create POST request and return response
        response = self.session.post(
            'https://{0}.amocrm.{1}/api/v2/leads'.format(self.subdomain, self.domain),
            cookies=cookies,
            data=json.dumps(post_data),
            headers=self.headers)
        response.raise_for_status()
        return response.json()

    def add_tasks(self, count, days, hour=23, minute=59):
        """ Add tasks by api and return request response as json
        Parameters:
        :count - int, number of tasks per day .
        :days - int, number of days with tasks
        :hour - int, hour part of complete task time
        :minute - int, minute part of complete task time
        """
        # Generate tasks list
        tasks_list = []
        # Init task time (just time)
        complete_time = datetime.time(hour=hour, minute=minute)
        for day in range(days):
            # init task date
            complete_date = datetime.datetime.today().date() \
                            + datetime.timedelta(days=day)
            # Combine task date and task time
            complete_till_at = datetime.datetime.combine(complete_date,
                                                         complete_time)
            for _ in range(count):
                task = {
                    'complete_till_at': complete_till_at.timestamp(),
                    'text': AmoSession.random_data()
                }
                tasks_list.append(task)
        post_data = dict()
        post_data['add'] = tasks_list
        # load cookies
        cookies = AmoSession.load_cookies(self.test_name)
        # Create POST request and return response
        response = self.session.post(
            'https://{0}.amocrm.{1}/api/v2/tasks'.format(self.subdomain, self.domain),
            cookies=cookies,
            data=json.dumps(post_data),
            headers=self.headers)
        response.raise_for_status()
        return response.json()

    def add_company_contact(self, entity_type, name):
        """ Add contact/company by api and return request response as json
        Parameters:
        :name - str, contact/company name .
        :entity_type - type of entity.
                        May be 'contact' or 'company'
        """
        # load cookies
        cookies = AmoSession.load_cookies(self.test_name)
        # Correct 'entity_type' argument assertion
        assert entity_type in ['contact', 'company']
        # Create post data
        post_data = dict()
        post_data['add'] = [{'name': name}]
        # Create POST request and return response
        if entity_type == 'contact':
            url = 'https://{0}.amocrm.{1}/api/v2/{2}'.format(self.subdomain,
                                                             self.domain,
                                                             'contacts')
        elif entity_type == 'company':
            url = 'https://{0}.amocrm.{1}/api/v2/{2}'.format(self.subdomain,
                                                             self.domain,
                                                             'companies')
        response = self.session.post(url,
                                     cookies=cookies,
                                     data=json.dumps(post_data),
                                     headers=self.headers)
        response.raise_for_status()
        return response.json()

    def add_custom_entity(self, entity, additional_fields):
        """
        :param entity: type of the entity in plural (contacts, leads, companies, ...)
        :type entity: str
        :param additional_fields: dict with keys equal to the entity fields
        :type additional_fields: dict
        """
        cookies = AmoSession.load_cookies(self.test_name)
        custom_fields = self.get_entity_custom_fields_ids(entity)
        post_data = CustomEntity()
        for field, value in additional_fields.items():
            if custom_fields and field in custom_fields:
                post_data.set_custom_field(custom_fields[field], value)
            else:
                post_data.set_field(field, value)
        url = f'https://{self.subdomain}.amocrm.{self.domain}/api/v2/{entity}'
        response = self.session.post(url, cookies=cookies,
                                     data=json.dumps({'add': [post_data.result_dict]}),
                                     headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_entity_custom_fields_ids(self, entity):
        """
        get dictionary with custom fields names and their ids
        :param entity: type of the entity in plural (contacts, leads, companies, ...)
        :type entity: str
        :return: dict were keys is names of fields and values -- ids
        """
        cookies = AmoSession.load_cookies(self.test_name)
        url = f'https://{self.subdomain}.amocrm.{self.domain}/api/v2/account?with=custom_fields'
        response = self.session.get(url, cookies=cookies)
        if entity not in response.json()['_embedded']['custom_fields']:
            return
        fields = response.json()['_embedded']['custom_fields'][entity]
        if fields:
            return {value['name']: key for key, value in fields.items()}

    def get_entity_custom_fields_enums(self, entity):
        """
        :param entity: type of the entity in plural (contacts, leads, companies, ...)
        :type entity: str
        :param entity: type of the entity in plural. For example, contacts or companies
        """
        cookies = AmoSession.load_cookies(self.test_name)
        url = f'https://{self.subdomain}.amocrm.{self.domain}/api/v2/account?with=custom_fields'
        response = self.session.get(url, cookies=cookies)
        fields = response.json()['_embedded']['custom_fields'][entity].items()
        return {value['name']: value['enums'] for key, value in fields if 'enums' in value}

    def get_users_ids(self):
        """
        get available users ids for current account
        :return: list of str
        """
        cookies = AmoSession.load_cookies(self.test_name)
        url = f'https://{self.subdomain}.amocrm.{self.domain}/api/v2/account?with=users'
        response = self.session.get(url, cookies=cookies)
        return list(response.json()['_embedded']['users'].keys())

    def add_customer(self, customer_name, responsible_user_id=None,
                     expected_amount=None, tags=None):
        """ Add customer by api and return request response as json
        Parameters:
        :customer_name - str, customer name.
        """
        # load cookies
        cookies = AmoSession.load_cookies(self.test_name)
        # Create post data
        post_data = dict()
        next_purchase = (datetime.datetime.today() +
                         datetime.timedelta(days=5)).timestamp()
        post_data['add'] = [{'name': customer_name,
                             'next_date': next_purchase}]
        # Add kwargs to post data
        if responsible_user_id:
            post_data['add'][0]['responsible_user_id'] = responsible_user_id
        if expected_amount:
            post_data['add'][0]['next_price'] = expected_amount
        if tags:
            post_data['add'][0]['tags'] = ', '.join(tags)
        # Create POST request and return response
        url = 'https://{0}.amocrm.{1}/api/v2/customers'.format(self.subdomain,
                                                               self.domain)
        response = self.session.post(url,
                                     cookies=cookies,
                                     data=json.dumps(post_data),
                                     headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_customers_id_list(self):
        """ This method return list of all account customers id """
        # load cookies
        cookies = AmoSession.load_cookies(self.test_name)
        # Create GET url
        url = ('https://{0}.amocrm.{1}/api/v2/customers'.format(self.subdomain,
                                                                self.domain) +
               '?filter[date][type]=create&filter[date][from]=01.01.1970')
        # Make GET request
        response = self.session.get(url,
                                    cookies=cookies)
        response.raise_for_status()
        # Create list of id
        return [item['id'] for item in response.json()['_embedded']['items']]

    def delete_customers(self, customer_id):
        """ Delete customers by api.
        Parameters:
        :customer_id - str or list, customer id to delete
        May be given several ids as list of id
        """
        # load cookies
        cookies = AmoSession.load_cookies(self.test_name)
        # Create post data
        post_data = dict()
        post_data['delete'] = list(customer_id)
        # Create POST request and return response
        url = 'https://{0}.amocrm.{1}/api/v2/customers'.format(self.subdomain,
                                                               self.domain)
        response = self.session.post(url,
                                     cookies=cookies,
                                     data=json.dumps(post_data),
                                     headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_entity(self, entity_type, entity_id, new_name):
        """ Update contact/company by api
        Parameters:
        :new_name - str,  new lead/contact/company name .
        :entity_type - type of entity.
                        May be 'lead', 'contact' or 'company'
        :entity_id - id of the entity to be updated
        """
        # load cookies
        cookies = AmoSession.load_cookies(self.test_name)
        # Correct 'entity_type' argument assertion
        assert entity_type in ['lead', 'contact', 'company']
        # Create post data
        post_data = dict()
        post_data['update'] = [
            {
                'id': entity_id,
                'updated_at': int(time.time()),
                'name': new_name,
            }]
        # Create POST request and return response
        if entity_type == 'lead':
            url = 'https://{0}.amocrm.{1}/api/v2/{2}'.format(self.subdomain,
                                                             self.domain,
                                                            'leads')
        elif entity_type == 'contact':
            url = 'https://{0}.amocrm.{1}/api/v2/{2}'.format(self.subdomain,
                                                            self.domain,
                                                            'contacts')
        elif entity_type == 'company':
            url = 'https://{0}.amocrm.{1}/api/v2/{2}'.format(self.subdomain,
                                                             self.domain,
                                                            'companies')
        response = self.session.post(url,
                                     cookies=cookies,
                                     data=json.dumps(post_data),
                                     headers=self.headers)
        response.raise_for_status()
        return response.json()

    def change_account_language(self, language):
        """ Change account language
        Parameters:
        :parameter language - str, account language
                              ru - russian, en - english
        """
        url = 'https://{0}.amocrm.{1}/api/v2/account?lang={2}'.format(
            self.subdomain,
            self.domain,
            language)
        cookies = AmoSession.load_cookies(self.test_name)                                           # load cookies
        response = self.session.get(url, cookies=cookies)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def save_cookies_name(test_name, cookies, init_mongo=False):
        """ Save cookies name in mongo """
        # Generate cookie file name and save in MongoDB
        filename = 'cookies/cookies_{}.pickle'.format(
            datetime.datetime.now().strftime("%Y_%m_%d_%M_%S_%f"))
        client = MongoClient('localhost', 27017)
        # client = MongoClient('mongo', 27017) # если запуск в докере
        db = client['selenium_tests']

        dataset = {'cookies_filename': filename}
        if init_mongo:

            db[test_name].insert_one(dataset)
        else:

            db[test_name].update_one(db[test_name].find_one(),
                                     {'$set': dataset})
        client.close()
        # Save cookie in file
        with open(filename, 'wb') as cookie_file:
            pickle.dump(cookies, cookie_file)

    @staticmethod
    def load_cookies(test_name):
        """ Load cookies file """
        # Find cookie name in Mongo
        client = MongoClient('localhost', 27017)
        # client = MongoClient('mongo', 27017) если запуск в докере
        db = client['selenium_tests']
        data = db[test_name].find_one()
        client.close()
        # Load cookie
        with open(data['cookies_filename'], 'rb') as cookie_file:
            cookie = pickle.load(cookie_file)
        # os.remove(data['cookies_filename'])
        return cookie

    @staticmethod
    def random_data():
        """ Generate random data string """
        return ''.join(choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits)
                       for _ in range(16))
