
import requests

url= 'https://gtest2.amocrm.ru/api/v4/contacts'


headers = {'Authorization': "Bearer " + token}

data = '[{"first_name": "Peter", "last_name": "Smirnov"}]'

response = requests.post(url, headers=headers, data=data)
