
#create and edit lead
import requests
import json

url = 'https://gtest2.amocrm.ru/api/v4/leads'

headers = {'Authorization': "Bearer " + token}

data = '[{"name": "Lead2","created_by": 0,"price": 20000}]'

response = requests.post(url, headers=headers, data=data)







