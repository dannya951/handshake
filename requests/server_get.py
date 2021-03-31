import requests
import json

from requests.exceptions import ConnectionError


url = 'http://localhost:8080/server'
try:
    req = requests.get(url)
    req_stat = req.status_code
    print('Reponse Status: ' + str(req_stat))
    if req_stat == 200:
        req_json = json.loads(req.text)
        print(json.dumps(req_json, sort_keys=True, indent=4))
    else:
        print('Response Reason: ' + req.reason)
except ConnectionError:
    print("ConnectionError occurred.")
except:
    print("Unexpected error occurred.")