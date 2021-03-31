from tornado import httpclient, ioloop
from os import path, remove
import json


class AsyncRequestUtility:
    def __init__(self, control_server_ip_address, control_server_port_number):
        self.control_server_ip_address = control_server_ip_address
        self.control_server_port_number = control_server_port_number
        self.url_prefix = '/'.join(['http:', '', ':'.join([control_server_ip_address, control_server_port_number])])

        # self.client_uuid = uuid4().hex
        self.client_uuid = '37b783ca1ba44f668ffcbe4d301139b0'
        self.client_id = self.client_uuid[:6]

    # Blockchain Requests
    # TODO: Maybe move to IOUtility
    @staticmethod
    async def write_blockchain(path_name, chunk):
        with open(path_name, 'ab') as gzt:
            gzt.write(chunk)

    async def get_blockchain(self, path_name):
        gztar_name = 'blockchain'  # TODO: API endpoints in config dict
        get_blockchain_url = '/'.join([self.url_prefix, gztar_name])
        client = httpclient.AsyncHTTPClient(force_instance=True, max_buffer_size=314572800)
        try:
            if path.exists(path_name) and path.isfile(path_name):
                remove(path_name)
            loop = ioloop.IOLoop.current()
            print('Starting fetch operation.')
            await client.fetch(get_blockchain_url, streaming_callback=lambda chunk:
                               loop.spawn_callback(AsyncRequestUtility.write_blockchain, path_name, chunk))
            print('Finished fetch operation.')
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        httpclient.AsyncHTTPClient.configure(None, force_instance=False, max_buffer_size=104857600)

    # Clients Requests
    async def post_clients(self):
        clients_name = 'clients'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, clients_name])
        data = {'client_id': self.client_id}
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='POST', body=json.dumps(data))
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 201:
                response_body = str(response.body, 'utf_8')
                print('Response Body: ' + response_body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    # Client Requests
    async def get_client(self):
        clients_name = 'clients'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, clients_name, self.client_id])
        intervals = {}
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='GET')
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200:
                intervals = json.loads(response.body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return intervals

    async def put_client(self, intervals):
        clients_name = 'clients'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, clients_name, self.client_id])
        data = intervals
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='PUT', body=json.dumps(data))
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200:
                response_body = str(response.body, 'utf_8')
                print('Response Body: ' + response_body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    async def delete_client(self):
        clients_name = 'clients'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, clients_name, self.client_id])
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='DELETE')
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200:
                response_body = str(response.body, 'utf_8')
                print('Response Body: ' + response_body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    # Help Requests
    async def get_help(self):
        help_name = ''  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, help_name])
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='GET')
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200:
                response_body_json = json.loads(response.body)
                print('\n'.join(['Response Body: ', json.dumps(response_body_json, sort_keys=True, indent=4)]))
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    # Results Requests
    async def post_results(self, interval):
        results_name = 'results'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, results_name])
        data = interval
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='POST', body=json.dumps(data))
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 201:
                response_body = str(response.body, 'utf_8')
                print('Response Body: ' + response_body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    # Result Requests
    async def get_result(self, name):
        results_name = 'results'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, results_name, str(name)])
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='GET')
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200:
                response_body_json = json.loads(response.body)
                print('\n'.join(['Response Body: ', json.dumps(response_body_json, sort_keys=True, indent=2)]))
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    async def put_result(self, interval):
        results_name = 'results'  # TODO: API endpoints in config dict
        name = [ik for ik in interval.keys()][0]
        url = '/'.join([self.url_prefix, results_name, name])
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='PUT', body=json.dumps(interval))
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200:
                response_body = str(response.body, 'utf_8')
                print('Response Body: ' + response_body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    async def delete_result(self, name):
        results_name = 'results'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, results_name, name])
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='DELETE')
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200:
                response_body = str(response.body, 'utf_8')
                print('Response Body: ' + response_body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    # Server Requests
    async def get_server(self):
        server_name = 'server'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, server_name])
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='GET')
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200:
                response_body_json = json.loads(response.body)
                print('\n'.join(['Response Body: ', json.dumps(response_body_json, sort_keys=True, indent=2)]))
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    async def put_server(self, server_is_running):
        server_name = 'server'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, server_name])
        server_status_json = {'server_is_running': server_is_running}
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='PUT', body=json.dumps(server_status_json))
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 200 or response_code == 202:
                response_body = str(response.body, 'utf_8')
                print('Response Body: ' + response_body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code

    async def delete_server(self):
        server_name = 'server'  # TODO: API endpoints in config dict
        url = '/'.join([self.url_prefix, server_name])
        response_code = None
        try:
            response = await httpclient.AsyncHTTPClient().fetch(url, method='DELETE')
            response_code = response.code
            print('Reponse Status Code: ' + str(response_code))
            if response_code == 202:
                response_body = str(response.body, 'utf_8')
                print('Response Body: ' + response_body)
            else:
                print('Response Reason: ' + response.reason)
        except httpclient.HTTPClientError as ce:
            print("HTTPClientError: " + str(ce))
            # raise ce
        except Exception as e:
            print("Error: " + str(e))
            # raise e
        return response_code