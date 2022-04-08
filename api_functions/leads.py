
import requests
import json

url = 'https://gtest2.amocrm.ru/api/v4/leads'

headers = {'Authorization': "Bearer " + token}

data = '[{"name": "Lead2","created_by": 0,"price": 20000}]'

response = requests.post(url, headers=headers, data=data)


tests
for i in range(1, 11):
    name = str(i) + " lead"
    Client.create_lead("gtest2", Oauth, name, str(random.randint(1, 1000000)))




