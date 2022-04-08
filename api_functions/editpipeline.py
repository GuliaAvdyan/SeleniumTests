
import requests
import json


url = 'https://gtest2.amocrm.ru/api/v4/leads/pipelines'

headers = {
    'Authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImU2MTY3MWM4MWE1NjgyZTZmM2E4YTgwNTkwNjE0NDcwOThhMDE5ZWE4MmE5OTY3NjQyNDAxMzU2YWJhNGEwOWY3MTk3YTczMjAwZDQwZjJhIn0.eyJhdWQiOiJkNjdkYzg1ZS1iYTFlLTQ1YzEtOGRmZC02ODQ1MzI2ZmJhNWUiLCJqdGkiOiJlNjE2NzFjODFhNTY4MmU2ZjNhOGE4MDU5MDYxNDQ3MDk4YTAxOWVhODJhOTk2NzY0MjQwMTM1NmFiYTRhMDlmNzE5N2E3MzIwMGQ0MGYyYSIsImlhdCI6MTY0NDQ4OTUyMCwibmJmIjoxNjQ0NDg5NTIwLCJleHAiOjE2NDQ1NzU5MjAsInN1YiI6IjY2NDk1NjEiLCJhY2NvdW50X2lkIjoyOTY4NDQxNiwic2NvcGVzIjpbInB1c2hfbm90aWZpY2F0aW9ucyIsImNybSIsIm5vdGlmaWNhdGlvbnMiXX0.fr85UcrFOkt3cnUF0bmAvkmOAP2wV4ic-ctO6tQsMFk9-tA23vkcH4ow_dN7f1Th70HFfo2BhhZBes9OcDxCj3E_OIrrZtJnw9p_bTU3hIqb2Im5zVlqwqoYS-ToQ8uEnx4Jv289HVjRJ1Zw8AUQj4r7mU4ST9RAdSz5OT9yGBUMluDXbxI5plQyDioHaYshVnLFGpPRH6QKku2lIF-a272Lc6JuxiCc4AwUhAUZ2qg-nAIyNF7X5EQdLPOMG9tHK4BIvyt_x1a7MIBWlqM1WKKpsmFiE3h1igcOb15NNb89QJ0ew5iRVBTEkE_9LxEvu281j9H8eU_jAjDhc795Qg"}

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
