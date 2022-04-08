
import requests
import json


url = 'https://gtest2.amocrm.ru/api/v4/leads/pipelines'

headers = {'Authorization': "Bearer " + token}

data = '[{"name": "New pipeline","is_main": false,"is_unsorted_on": true,"sort": 20,"_embedded": {"statuses": [{"id": 143, "name": "Close"},{"name": "First","sort": 10,"color": "#fffeb2"},{"name": "Second","sort": 10}]}}]'
lead_response = requests.post(url, headers=headers, data=data)

# get new pipeline id
parse_response = json.loads(lead_response.text)
embedded = parse_response.get('_embedded')
pipelines = embedded.get("pipelines")
id = pipelines[0].get("id")


def edit_pipeline():
    url_id = url + "/" + str(id)
    data = '{"name": "New name"}'
    pipeline_response = requests.patch(url_id, headers=headers, data=data)
    return pipeline_response


def add_status():
    url_status = url + "/" + str(id) + "/statuses"
    data = '[{"name": "New status","sort": 100,"color": "#fffeb2"},{"name": "New status 2","sort": 200,"color": "#fffeb2"}]'
    status_response = requests.post(url_status, headers=headers, data=data)
    return status_response


# get new status id
# parse status_response




def delete_pipeline():
    url_id = url + "/" + str(id)
    delete_pipeline = requests.delete(url_id, headers=headers, data=data)
    return delete_pipeline


print(add_status())
