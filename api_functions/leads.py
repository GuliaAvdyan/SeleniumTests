
import requests
import json

url = 'https://gtest2.amocrm.ru/api/v4/leads'

headers = {'Authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjhmMzI3NDJlMmUyYmNjMGI4YjQxMzk1NDkyOWJjOWU3YWJkYWY0ZWY4ZmMxMzJiOGYxZWRlM2ViN2Y2NWVhZDJhZmUzMmU5OWY2YzkwM2ZmIn0.eyJhdWQiOiJkNjdkYzg1ZS1iYTFlLTQ1YzEtOGRmZC02ODQ1MzI2ZmJhNWUiLCJqdGkiOiI4ZjMyNzQyZTJlMmJjYzBiOGI0MTM5NTQ5MjliYzllN2FiZGFmNGVmOGZjMTMyYjhmMWVkZTNlYjdmNjVlYWQyYWZlMzJlOTlmNmM5MDNmZiIsImlhdCI6MTY0NDQ4NjE3MCwibmJmIjoxNjQ0NDg2MTcwLCJleHAiOjE2NDQ1NzI1NzAsInN1YiI6IjY2NDk1NjEiLCJhY2NvdW50X2lkIjoyOTY4NDQxNiwic2NvcGVzIjpbInB1c2hfbm90aWZpY2F0aW9ucyIsImNybSIsIm5vdGlmaWNhdGlvbnMiXX0.Yi87bFS_UvD9I92jOYrJ0a4YChYYdZYY_Xw99E18IUQgVYvDqv0pnVBHLqP0IpLy-LjcupOxlg83lMuwZJ2gbowDrdWB83Xa-wj2t4y53Lco-MpPY7PjbULkiAF1wGstwxUj0bYZnDxPds_GzuYZnlCFiD8VmfqR1UT4QgGnSzVUYm73xO7S-9vrDbPwEUsl8hAM-npY4F6BneFtaC036cekXykwBT7X40Qx3lw1WcWgpSbBC1_2ecAotH0rqPgTFkZ5Tf8-38yptMLMAHlsoAK_P_gdBqZLJ9G1ftfnk2djNSDtIqcLwXo0DgdCoGfch3-pagk7BjpRljou5N5ijw"}

data = '[{"name": "Lead2","created_by": 0,"price": 20000}]'

response = requests.post(url, headers=headers, data=data)


tests
for i in range(1, 11):
    name = str(i) + " lead"
    Client.create_lead("gtest2", Oauth, name, str(random.randint(1, 1000000)))




