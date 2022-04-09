import requests

url = 'https://gtest2.amocrm.ru/api/v4/leads/pipelines'

headers = {'Authorization': "Bearer " + token}

data = '[{"name": "New pipeline","is_main": false,"is_unsorted_on": true,"sort": 20,"_embedded": {"statuses": [{"id": 143, "name": "Close"},{"name": "First","sort": 10,"color": "#fffeb2"},{"name": "Second","sort": 10}]}}]'

response = requests.post(url, headers=headers, data=data)








