import asyncio
import time
import json
import IOUtility as Iou
from tornado import gen, httpclient


async def async_identify_connections():
    arg_list = ['nmcli', 'connection', 'show']

    # conn_str = subprocess.run(args=arg_list, stdout=subprocess.PIPE, encoding='utf-8').stdout
    proc = await asyncio.create_subprocess_shell(
        ' '.join(arg_list),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    conn_str = stdout.decode('utf-8')

    conn_lines = conn_str.rstrip('\n').split('\n')
    keys = conn_lines[0].split()
    conn_list = []
    for conn_line in conn_lines[1:]:
        split_line = conn_line.split()
        conn_length = len(split_line)
        keys_length = len(keys)
        conn_dict = {}
        for index in range(1, keys_length)[::-1]:
            conn_dict[keys[index]] = split_line[conn_length - (keys_length - index)]
        conn_dict[keys[0]] = ' '.join(split_line[:conn_length - (keys_length - 1)])
        conn_list.append(conn_dict)
    return conn_list


async def async_identify_username():
    arg_list = ['whoami']

    # username_str = subprocess.run(args=arg_list, stdout=subprocess.PIPE, encoding='utf-8').stdout
    proc = await asyncio.create_subprocess_shell(
        ' '.join(arg_list),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    username_str = stdout.decode('utf-8')

    return username_str.rstrip('\n')


async def async_manage_connections(connections, action, debug=False):
    assert (action == 'connect') or (action == 'disconnect')
    connect = True
    if action == 'disconnect':
        connect = False
    for conn in connections:
        arg_list = ['nmcli']
        if connect:
            arg_list.append('-p')
            arg_list.append('con')
            arg_list.append('up')
            arg_list.append('id')
            arg_list.append('\'' + conn['NAME'] + '\'')
            arg_list.append('ifname')
            arg_list.append(conn['DEVICE'])
        else:
            arg_list.append('dev')
            arg_list.append('disconnect')
            arg_list.append(conn['DEVICE'])

        # comm_result = subprocess.run(args=arg_list, stdout=subprocess.PIPE, encoding='utf-8')
        proc = await asyncio.create_subprocess_shell(
            ' '.join(arg_list),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        comm_result = stdout.decode('utf-8')

        if debug:
            # print(comm_result.stdout)
            print(comm_result)


async def async_test_connection_cycle(connections, debug=False):
    first_display = True
    for i in range(5)[::-1]:
        if first_display:
            print('Disconnecting in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        # time.sleep(1.0)
        await gen.sleep(1)
    await async_manage_connections(connections, action='disconnect', debug=debug)

    # await gen.sleep(5)

    first_display = True
    for i in range(5)[::-1]:
        if first_display:
            print('Reconnecting in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        # time.sleep(1.0)
        await gen.sleep(1)
    await async_manage_connections(connections, action='connect', debug=debug)


async def async_test_node_start_stop_cycle(connections, async_node_manager, time_interval=5, debug=False):
    first_display = True
    for i in range(time_interval)[::-1]:
        if first_display:
            print('Disconnecting in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        # time.sleep(1.0)
        await gen.sleep(1)
    await async_manage_connections(connections, 'disconnect', debug=debug)

    first_display = True
    for i in range(time_interval)[::-1]:
        if first_display:
            print('Starting node in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        # time.sleep(1.0)
        await gen.sleep(1)
    await async_node_manager.async_start_node(debug=debug)

    first_display = True
    for i in range(time_interval)[::-1]:
        if first_display:
            print('Stopping node in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        # time.sleep(1.0)
        await gen.sleep(1)
    await async_node_manager.async_stop_node(debug=debug)

    first_display = True
    for i in range(time_interval)[::-1]:
        if first_display:
            print('Reconnecting in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        # time.sleep(1.0)
        await gen.sleep(1)
    await async_manage_connections(connections, 'connect', debug=debug)


def format_dict_to_print(dict_to_format, depth=0):
    if dict_to_format is None:
        return str(None)
    space_tab = '  '
    lines = ['{']
    for key in list(dict_to_format.keys()):
        if isinstance(dict_to_format[key], dict):
            # lines.append(('\t' * (depth + 1)) + str(key) + ' :')
            lines.append((space_tab * (depth + 1)) + str(key) + ':')

            # lines.append(('\t' * (depth + 1)) + format_dict_to_print(depth + 1, dict_to_format[key]))
            lines.append((space_tab * (depth + 1)) + format_dict_to_print(dict_to_format[key], depth + 1))
        elif isinstance(dict_to_format[key], list):
            # lines.append(('\t' * (depth + 1)) + str(key) + ' :')
            lines.append((space_tab * (depth + 1)) + str(key) + ':')

            # lines.append(('\t' * (depth + 1)) + format_list_to_print(depth + 1, dict_to_format[key]))
            lines.append((space_tab * (depth + 1)) + format_list_to_print(dict_to_format[key], depth + 1))
        else:
            # lines.append(('\t' * (depth + 1)) + str(key) + ' : ' + str(dict_to_format[key]))
            lines.append((space_tab * (depth + 1)) + str(key) + ': ' + str(dict_to_format[key]))
    # lines.append(('\t' * depth) + '}')
    lines.append((space_tab * depth) + '}')

    dict_str = '\n'.join(lines)
    return dict_str


def format_list_to_print(list_to_format, depth):
    lines = ['[']
    space_tab = '  '
    for element in list_to_format:
        if isinstance(element, dict):
            # lines.append(('\t' * (depth + 1)) + format_dict_to_print(depth + 1, element))
            lines.append((space_tab * (depth + 1)) + format_dict_to_print(element, depth + 1))
        elif isinstance(element, list):
            # lines.append(('\t' * (depth + 1)) + format_list_to_print(depth + 1, element))
            lines.append((space_tab * (depth + 1)) + format_list_to_print(element, depth + 1))
        else:
            # lines.append(('\t' * (depth + 1)) + str(element))
            lines.append((space_tab * (depth + 1)) + str(element))
    # lines.append(('\t' * depth) + ']')
    lines.append((space_tab * depth) + ']')

    list_str = '\n'.join(lines)
    return list_str


class AsyncNodeManager:
    # def __init__(self, node_config_path, handshake_code_directory_prefix):
    def __init__(self, node_config, handshake_code_directory_prefix):
        # self.node_config = json.loads(Iou.read_from_file(node_config_path))
        self.node_config = node_config
        self.handshake_code_directory_prefix = handshake_code_directory_prefix

    async def async_start_node(self, start_delay=20, debug=False):
        node_start_arg_list = self.configure_start_arguments()
        if debug:
            print('Starting node with following command-line input:')
            print(' '.join(node_start_arg_list))

        # node_start_result = subprocess.run(args=node_start_arg_list, stdout=subprocess.PIPE, encoding='utf-8')
        proc = await asyncio.create_subprocess_shell(
            ' '.join(node_start_arg_list),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        node_start_result = stdout.decode('utf-8')

        if debug:
            # print(node_start_result.stdout)
            print(node_start_result)
        # time.sleep(20.0)
        await gen.sleep(start_delay)

    async def async_stop_node(self, stop_delay=20, debug=False):
        node_stop_arg_list = self.configure_stop_arguments()
        if debug:
            print('Stopping node with following command-line input:')
            print(' '.join(node_stop_arg_list))

        # node_stop_result = subprocess.run(args=node_stop_arg_list, stdout=subprocess.PIPE, encoding='utf-8')
        proc = await asyncio.create_subprocess_shell(
            ' '.join(node_stop_arg_list),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        node_stop_result = stdout.decode('utf-8')

        if debug:
            # print(node_stop_result.stdout)
            print(node_stop_result)
        # time.sleep(20.0)
        await gen.sleep(stop_delay)

    def configure_start_arguments(self):
        start_arg_list = [self.handshake_code_directory_prefix + '/bin/hsd',
                          '--network=' + self.node_config['network'],
                          '--listen=' + self.node_config['listen'],
                          '--index-tx=' + self.node_config['index-tx'],
                          '--index-address=' + self.node_config['index-address'],
                          '--http-port=' + self.node_config['ports']['http'],
                          '--port=' + self.node_config['ports']['pool'],
                          '--wallet-http-port=' + self.node_config['ports']['wallet-http'],
                          '--ns-port=' + self.node_config['ports']['ns'],
                          '--rs-port=' + self.node_config['ports']['rs'],
                          '--prefix=' + self.node_config['config_directory_prefix']]
        if self.node_config['bools']['daemon']:
            start_arg_list.append('--daemon')
        if self.node_config['bools']['no_auth']:
            start_arg_list.append('--no-auth')
        return start_arg_list

    def configure_stop_arguments(self):
        stop_arg_list = [self.handshake_code_directory_prefix + '/node_modules/hs-client/bin/hsd-cli',
                         '--http-port=' + self.node_config['ports']['http'],
                         'rpc',
                         'stop']
        return stop_arg_list

    '''
    def async_add_peer_node(self, identity):
        add_peer_node_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http']
        add_peer_node_query_data = '{"method":"addnode","params":["' + identity + '", "add"]}'
        return json.loads(Iou.get_from_curl_with_data(add_peer_node_query_url, data=add_peer_node_query_data))['result']

    def async_remove_peer_node(self, identity):
        remove_peer_node_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http']
        remove_peer_node_query_data = '{"method":"addnode","params":["' + identity + '", "remove"]}'
        return json.loads(Iou.get_from_curl_with_data(remove_peer_node_query_url,
                                                      data=remove_peer_node_query_data))['result']

    def async_get_node_identity(self, debug=False):
        run_with_debug = debug
        node_info_query_response = self.async_get_node_info(debug=run_with_debug)
        node_identity_key = node_info_query_response['pool']['identitykey']
        configured_identity_key = node_identity_key + '@127.0.0.1:' + self.node_config['ports']['pool']
        if run_with_debug:
            print('Configured identity key: ' + configured_identity_key)
            print()
        return configured_identity_key
    '''

    async def async_get_chain_height(self, retry_counter=0, retry_delay=5, debug=False):
        run_with_debug = debug
        node_info_query_response = await self.async_get_node_info(
            retry_counter=retry_counter,
            retry_delay=retry_delay,
            debug=run_with_debug)
        chain_height_response = int(node_info_query_response['chain']['height'])
        if run_with_debug:
            print('Chain height response: ' + str(chain_height_response))
            print()
        return chain_height_response

    async def async_get_node_info(self, retry_counter=0, retry_delay=5, debug=False):
        # Because of the time component, sequential calls to this endpoint may produce different results
        node_info_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        response_body = None
        response_reason = None
        while response_body is None and response_reason is None and retry_counter >= 0:
            wait_for_server = False
            try:
                response = await httpclient.AsyncHTTPClient().fetch(node_info_query_url, method='GET')
                response_code = response.code
                if debug:
                    print('Reponse Status Code: ' + str(response_code))
                if response_code == 200:
                    response_body = json.loads(str(response.body, 'utf_8'))
                    if debug:
                        # print('Response Body: ' + json.dumps(response_body, indent=4))
                        print(format_dict_to_print(response_body))
                else:
                    response_reason = response.reason
                    if debug:
                        print('Response Reason: ' + response.reason)
            except httpclient.HTTPClientError as ce:
                wait_for_server = True
                if debug:
                    print("HTTPClientError: " + str(ce))
                # raise ce
            except Exception as e:
                wait_for_server = True
                if debug:
                    print("Error: " + str(e))
                # raise e
            if wait_for_server:
                await gen.sleep(retry_delay)
            retry_counter -= 1
        return response_body

    async def async_reset_chain(self, desired_height, retry_counter=0, retry_delay=5, request_timeout=20, debug=False):
        chain_reset_request_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/reset'
        data = {'height': desired_height}
        response_body = None
        response_reason = None
        while response_body is None and response_reason is None and retry_counter >= 0:
            wait_for_server = False
            try:
                response = await httpclient.AsyncHTTPClient().fetch(
                    chain_reset_request_url,
                    method='POST',
                    body=json.dumps(data),
                    request_timeout=request_timeout)
                response_code = response.code
                if debug:
                    print('Reponse Status Code: ' + str(response_code))
                if response_code == 200:
                    response_body = json.loads(str(response.body, 'utf_8'))['success']
                    if debug:
                        # print('Response Body: ' + json.dumps(response_body, indent=4))
                        print(format_dict_to_print({'success': response_body}))
                else:
                    response_reason = response.reason
                    if debug:
                        print('Response Reason: ' + response.reason)
            except httpclient.HTTPClientError as ce:
                wait_for_server = True
                if debug:
                    print("HTTPClientError: " + str(ce))
                # raise ce
            except Exception as e:
                wait_for_server = True
                if debug:
                    print("Error: " + str(e))
                # raise e
            if wait_for_server:
                await gen.sleep(retry_delay)
            retry_counter -= 1
        return response_body

    def set_config_options(self, option_dict):
        for key in list(option_dict.keys()):
            if key in self.node_config:
                self.node_config[key] = option_dict[key]

    def get_config_options(self, option_list):
        config_dict = {}
        for key in option_list:
            if key in self.node_config:
                config_dict[key] = self.node_config[key]
        return config_dict

    async def async_get_blockchain_info(self, retry_counter=0, retry_delay=5, debug=False):  # rpc
        # Because of the time component, sequential calls to this endpoint may produce different results
        blockchain_info_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        data = {'method': 'getblockchaininfo'}
        response_body = None
        response_reason = None
        while response_body is None and response_reason is None and retry_counter >= 0:
            wait_for_server = False
            try:
                response = await httpclient.AsyncHTTPClient().fetch(
                    blockchain_info_query_url,
                    method='POST',
                    body=json.dumps(data))
                response_code = response.code
                if debug:
                    print('Reponse Status Code: ' + str(response_code))
                if response_code == 200:
                    response_body = json.loads(str(response.body, 'utf_8'))['result']
                    if debug:
                        # print('Response Body: ' + json.dumps(response_body, indent=4))
                        print(format_dict_to_print(response_body))
                else:
                    response_reason = response.reason
                    if debug:
                        print('Response Reason: ' + response.reason)
            except httpclient.HTTPClientError as ce:
                wait_for_server = True
                if debug:
                    print("HTTPClientError: " + str(ce))
                # raise ce
            except Exception as e:
                wait_for_server = True
                if debug:
                    print("Error: " + str(e))
                # raise e
            if wait_for_server:
                await gen.sleep(retry_delay)
            retry_counter -= 1
        return response_body

    async def async_get_block_by_height(self, height, retry_counter=0, retry_delay=5, debug=False):  # cli
        # Because of the time component, sequential calls to this endpoint may produce different results
        # block_by_height['time'] is constant, but block_by_height['txs'][i]['mtime'] is variable
        block_by_height_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/block/' + str(height)
        response_body = None
        response_reason = None
        while response_body is None and response_reason is None and retry_counter >= 0:
            wait_for_server = False
            try:
                response = await httpclient.AsyncHTTPClient().fetch(block_by_height_query_url, method='GET')
                response_code = response.code
                if debug:
                    print('Reponse Status Code: ' + str(response_code))
                if response_code == 200:
                    response_body = json.loads(str(response.body, 'utf_8'))
                    if debug:
                        # print('Response Body: ' + json.dumps(response_body, indent=4))
                        print(format_dict_to_print(response_body))
                else:
                    response_reason = response.reason
                    if debug:
                        print('Response Reason: ' + response.reason)
            except httpclient.HTTPClientError as ce:
                wait_for_server = True
                if debug:
                    print("HTTPClientError: " + str(ce))
                # raise ce
            except Exception as e:
                wait_for_server = True
                if debug:
                    print("Error: " + str(e))
                # raise e
            if wait_for_server:
                await gen.sleep(retry_delay)
            retry_counter -= 1
        return response_body

    async def async_get_names(self, retry_counter=0, retry_delay=5, debug=False):  # rpc
        blockchain_names_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        data = {'method': 'getnames'}
        response_body = None
        response_reason = None
        while response_body is None and response_reason is None and retry_counter >= 0:
            wait_for_server = False
            try:
                response = await httpclient.AsyncHTTPClient().fetch(
                    blockchain_names_query_url,
                    method='POST',
                    body=json.dumps(data))
                response_code = response.code
                if debug:
                    print('Reponse Status Code: ' + str(response_code))
                if response_code == 200:
                    response_body = json.loads(str(response.body, 'utf_8'))['result']
                    if debug:
                        # print('Response Body: ' + json.dumps(response_body, indent=4))
                        print(format_dict_to_print(response_body))
                else:
                    response_reason = response.reason
                    if debug:
                        print('Response Reason: ' + response.reason)
            except httpclient.HTTPClientError as ce:
                wait_for_server = True
                if debug:
                    print("HTTPClientError: " + str(ce))
                # raise ce
            except Exception as e:
                wait_for_server = True
                if debug:
                    print("Error: " + str(e))
                # raise e
            if wait_for_server:
                await gen.sleep(retry_delay)
            retry_counter -= 1
        return response_body

    async def async_get_name_info(self, name, retry_counter=0, retry_delay=5, debug=False):  # rpc
        blockchain_name_info_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        data = {'method': 'getnameinfo', 'params': [name]}
        response_body = None
        response_reason = None
        while response_body is None and response_reason is None and retry_counter >= 0:
            wait_for_server = False
            try:
                response = await httpclient.AsyncHTTPClient().fetch(
                    blockchain_name_info_query_url,
                    method='POST',
                    body=json.dumps(data))
                response_code = response.code
                if debug:
                    print('Reponse Status Code: ' + str(response_code))
                if response_code == 200:
                    response_body = json.loads(str(response.body, 'utf_8'))['result']
                    if debug:
                        # print('Response Body: ' + json.dumps(response_body, indent=4))
                        print(format_dict_to_print(response_body))
                else:
                    response_reason = response.reason
                    if debug:
                        print('Response Reason: ' + response.reason)
            except httpclient.HTTPClientError as ce:
                wait_for_server = True
                if debug:
                    print("HTTPClientError: " + str(ce))
                # raise ce
            except Exception as e:
                wait_for_server = True
                if debug:
                    print("Error: " + str(e))
                # raise e
            if wait_for_server:
                await gen.sleep(retry_delay)
            retry_counter -= 1
        return response_body

    async def async_get_name_resource(self, name, retry_counter=0, retry_delay=5, debug=False):  # rpc
        blockchain_name_resource_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        data = {'method': 'getnameresource', 'params': [name]}
        response_body = None
        response_reason = None
        while response_body is None and response_reason is None and retry_counter >= 0:
            wait_for_server = False
            try:
                response = await httpclient.AsyncHTTPClient().fetch(
                    blockchain_name_resource_query_url,
                    method='POST',
                    body=json.dumps(data))
                response_code = response.code
                if debug:
                    print('Reponse Status Code: ' + str(response_code))
                if response_code == 200:
                    response_body = json.loads(str(response.body, 'utf_8'))['result']
                    if debug:
                        # print('Response Body: ' + json.dumps(response_body, indent=4))
                        print(format_dict_to_print(response_body))
                else:
                    response_reason = response.reason
                    if debug:
                        print('Response Reason: ' + response.reason)
            except httpclient.HTTPClientError as ce:
                wait_for_server = True
                if debug:
                    print("HTTPClientError: " + str(ce))
                # raise ce
            except Exception as e:
                wait_for_server = True
                if debug:
                    print("Error: " + str(e))
                # raise e
            if wait_for_server:
                await gen.sleep(retry_delay)
            retry_counter -= 1
        return response_body

    # node_query_data = '{"method":"<method_name>","params":["' + <method_parameter_string> + '"]}'
    # node_query_json = json.loads(Iou.get_from_curl_with_data(node_query_url, data=node_query_data))['result']
