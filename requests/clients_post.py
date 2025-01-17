import requests
import json

from uuid import uuid4
from requests.exceptions import ConnectionError


# client_uuid = uuid4().hex
client_uuid = '37b783ca1ba44f668ffcbe4d301139b0'
client_id = client_uuid[:6]
data_json = {'client_id': client_id}
url = 'http://localhost:8080/clients'
try:
    req = requests.post(url, json=data_json)
    req_stat = req.status_code
    print('Reponse Status: ' + str(req_stat))
    if req_stat == 201:
        print('Response Content: ' + req.text)
    else:
        print('Response Reason: ' + req.reason)
except ConnectionError:
    print("ConnectionError occurred.")
except:
    print("Unexpected error occurred.")