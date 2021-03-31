import requests
import json
import random

from requests.exceptions import ConnectionError


# result_id = random.randrange(25000)
result_id = 'indie'

data_json = {result_id: {}}
url = 'http://localhost:8080/results/' + str(result_id)
try:
    req = requests.put(url, json=data_json)
    req_stat = req.status_code
    print('Reponse Status: ' + str(req_stat))
    if req_stat == 200:
        print('Response Content: ' + req.text)
    else:
        print('Response Reason: ' + req.reason)
except ConnectionError:
    print("ConnectionError occurred.")
except:
    print("Unexpected error occurred.")
