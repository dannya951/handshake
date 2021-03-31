import requests

from requests.exceptions import ConnectionError


url = 'http://localhost:8080/'
try:
    req = requests.get(url)
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