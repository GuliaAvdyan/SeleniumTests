import requests

from config.widget import Oauth


class ApiClient:

    def create_lead(self, subdomain: str, token: str, name, price):
        url = "https://" + subdomain + ".amocrm.ru/api/v4/leads"

        headers = {'Authorization': "Bearer " + token}

        data = '[{"name": "' + name + '","created_by": 0,"price": "' + price + '"}]'

        response = requests.post(url, headers=headers, data=data)
        return response


Client = ApiClient()
Client.create_lead("gtest2", Oauth.Auth(), "test", "10000")
