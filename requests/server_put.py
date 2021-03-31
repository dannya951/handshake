import requests
import json

from requests.exceptions import ConnectionError


server_is_running = True
# server_is_running = False
data_json = {'server_is_running': server_is_running}
url = 'http://localhost:8080/server'
try:
    req = requests.put(url, json=data_json)
    req_stat = req.status_code
    print('Reponse Status: ' + str(req_stat))
    if req_stat == 200 or req_stat == 202:
        print('Response Content: ' + req.text)
    else:
        print('Response Reason: ' + req.reason)
except ConnectionError:
    print("ConnectionError occurred.")
except:
    print("Unexpected error occurred.")