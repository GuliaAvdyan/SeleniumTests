
#to create company with phone number
import requests

url = 'https://gtest2.amocrm.ru/api/v4/companies'


headers = {'Authorization': "Bearer " + token}

data = '[{"name": "Holiday Inn", "custom_fields_values": [{"field_code": "PHONE", "values": [{"value": "+7912322222","enum_code": "WORK"}]}] }]'

response = requests.post(url, headers=headers, data=data)