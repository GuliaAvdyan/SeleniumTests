import requests

url = 'https://gtest2.amocrm.ru/api/v4/leads/pipelines'

headers = {'Authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImU2MTY3MWM4MWE1NjgyZTZmM2E4YTgwNTkwNjE0NDcwOThhMDE5ZWE4MmE5OTY3NjQyNDAxMzU2YWJhNGEwOWY3MTk3YTczMjAwZDQwZjJhIn0.eyJhdWQiOiJkNjdkYzg1ZS1iYTFlLTQ1YzEtOGRmZC02ODQ1MzI2ZmJhNWUiLCJqdGkiOiJlNjE2NzFjODFhNTY4MmU2ZjNhOGE4MDU5MDYxNDQ3MDk4YTAxOWVhODJhOTk2NzY0MjQwMTM1NmFiYTRhMDlmNzE5N2E3MzIwMGQ0MGYyYSIsImlhdCI6MTY0NDQ4OTUyMCwibmJmIjoxNjQ0NDg5NTIwLCJleHAiOjE2NDQ1NzU5MjAsInN1YiI6IjY2NDk1NjEiLCJhY2NvdW50X2lkIjoyOTY4NDQxNiwic2NvcGVzIjpbInB1c2hfbm90aWZpY2F0aW9ucyIsImNybSIsIm5vdGlmaWNhdGlvbnMiXX0.fr85UcrFOkt3cnUF0bmAvkmOAP2wV4ic-ctO6tQsMFk9-tA23vkcH4ow_dN7f1Th70HFfo2BhhZBes9OcDxCj3E_OIrrZtJnw9p_bTU3hIqb2Im5zVlqwqoYS-ToQ8uEnx4Jv289HVjRJ1Zw8AUQj4r7mU4ST9RAdSz5OT9yGBUMluDXbxI5plQyDioHaYshVnLFGpPRH6QKku2lIF-a272Lc6JuxiCc4AwUhAUZ2qg-nAIyNF7X5EQdLPOMG9tHK4BIvyt_x1a7MIBWlqM1WKKpsmFiE3h1igcOb15NNb89QJ0ew5iRVBTEkE_9LxEvu281j9H8eU_jAjDhc795Qg"}

data = '[{"name": "New pipeline","is_main": false,"is_unsorted_on": true,"sort": 20,"_embedded": {"statuses": [{"id": 143, "name": "Close"},{"name": "First","sort": 10,"color": "#fffeb2"},{"name": "Second","sort": 10}]}}]'

response = requests.post(url, headers=headers, data=data)








