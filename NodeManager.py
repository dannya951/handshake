import subprocess
import time
import json
import IOUtility as Iou


def identify_connections():
    arg_list = ['nmcli', 'connection', 'show']
    conn_str = subprocess.run(args=arg_list, stdout=subprocess.PIPE, encoding='utf-8').stdout
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


def identify_username():
    arg_list = ['whoami']
    username_str = subprocess.run(args=arg_list, stdout=subprocess.PIPE, encoding='utf-8').stdout
    return username_str.rstrip('\n')


def manage_connections(connections, action, debug=False):
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
            arg_list.append(conn['NAME'])
            arg_list.append('ifname')
            arg_list.append(conn['DEVICE'])
        else:
            arg_list.append('dev')
            arg_list.append('disconnect')
            arg_list.append(conn['DEVICE'])
        comm_result = subprocess.run(args=arg_list, stdout=subprocess.PIPE, encoding='utf-8')
        if debug:
            print(comm_result.stdout)


def test_connection_cycle(connections, debug=False):
    first_display = True
    for i in range(5)[::-1]:
        if first_display:
            print('Disconnecting in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        time.sleep(1.0)
    manage_connections(connections, action='disconnect', debug=debug)

    # time.sleep(5)

    first_display = True
    for i in range(5)[::-1]:
        if first_display:
            print('Reconnecting in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        time.sleep(1.0)
    manage_connections(connections, action='connect', debug=debug)


def test_node_start_stop_cycle(connections, node_manager, time_interval=5, debug=False):
    first_display = True
    for i in range(time_interval)[::-1]:
        if first_display:
            print('Disconnecting in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        time.sleep(1.0)
    manage_connections(connections, 'disconnect', debug=debug)

    first_display = True
    for i in range(time_interval)[::-1]:
        if first_display:
            print('Starting node in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        time.sleep(1.0)
    node_manager.start_node(debug=debug)

    first_display = True
    for i in range(time_interval)[::-1]:
        if first_display:
            print('Stopping node in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        time.sleep(1.0)
    node_manager.stop_node(debug=debug)

    first_display = True
    for i in range(time_interval)[::-1]:
        if first_display:
            print('Reconnecting in ' + str(i + 1))
            first_display = False
        else:
            print(str(i + 1))
        time.sleep(1.0)
    manage_connections(connections, 'connect', debug=debug)


def format_dict_to_print(depth, dict_to_format):
    if dict_to_format is None:
        return str(None)
    lines = ['{']
    for key in list(dict_to_format.keys()):
        if isinstance(dict_to_format[key], dict):
            lines.append(('\t' * (depth + 1)) + str(key) + ' :')
            lines.append(('\t' * (depth + 1)) + format_dict_to_print(depth + 1, dict_to_format[key]))
        elif isinstance(dict_to_format[key], list):
            lines.append(('\t' * (depth + 1)) + str(key) + ' :')
            lines.append(('\t' * (depth + 1)) + format_list_to_print(depth + 1, dict_to_format[key]))
        else:
            lines.append(('\t' * (depth + 1)) + str(key) + ' : ' + str(dict_to_format[key]))
    lines.append(('\t' * depth) + '}')
    dict_str = '\n'.join(lines)
    return dict_str


def format_list_to_print(depth, list_to_format):
    lines = ['[']
    for element in list_to_format:
        if isinstance(element, dict):
            lines.append(('\t' * (depth + 1)) + format_dict_to_print(depth + 1, element))
        elif isinstance(element, list):
            lines.append(('\t' * (depth + 1)) + format_list_to_print(depth + 1, element))
        else:
            lines.append(('\t' * (depth + 1)) + str(element))
    lines.append(('\t' * depth) + ']')
    list_str = '\n'.join(lines)
    return list_str


class NodeManager:
    # def __init__(self, node_config_path, handshake_code_directory_prefix):
    def __init__(self, node_config, handshake_code_directory_prefix):
        # self.node_config = json.loads(Iou.read_from_file(node_config_path))
        self.node_config = node_config
        self.handshake_code_directory_prefix = handshake_code_directory_prefix

    def start_node(self, start_delay=20.0, debug=False):
        node_start_arg_list = self.configure_start_arguments()
        if debug:
            print('Starting node with following command-line input:')
            print(' '.join(node_start_arg_list))
        node_start_result = subprocess.run(args=node_start_arg_list, stdout=subprocess.PIPE, encoding='utf-8')
        if debug:
            print(node_start_result.stdout)
        time.sleep(start_delay)

    def stop_node(self, stop_delay=20.0, debug=False):
        node_stop_arg_list = self.configure_stop_arguments()
        if debug:
            print('Stopping node with following command-line input:')
            print(' '.join(node_stop_arg_list))
        node_stop_result = subprocess.run(args=node_stop_arg_list, stdout=subprocess.PIPE, encoding='utf-8')
        if debug:
            print(node_stop_result.stdout)
        time.sleep(stop_delay)

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

    def add_peer_node(self, identity):
        add_peer_node_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http']
        add_peer_node_query_data = '{"method":"addnode","params":["' + identity + '", "add"]}'
        return json.loads(Iou.get_from_curl_with_data(add_peer_node_query_url, data=add_peer_node_query_data))['result']

    def remove_peer_node(self, identity):
        remove_peer_node_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http']
        remove_peer_node_query_data = '{"method":"addnode","params":["' + identity + '", "remove"]}'
        return json.loads(Iou.get_from_curl_with_data(remove_peer_node_query_url,
                                                      data=remove_peer_node_query_data))['result']

    def get_node_identity(self, debug=False):
        run_with_debug = debug
        node_info_query_response = self.get_node_info(debug=run_with_debug)
        node_identity_key = node_info_query_response['pool']['identitykey']
        configured_identity_key = node_identity_key + '@127.0.0.1:' + self.node_config['ports']['pool']
        if run_with_debug:
            print('Configured identity key: ' + configured_identity_key)
            print()
        return configured_identity_key

    def get_chain_height(self, debug=False):
        run_with_debug = debug
        node_info_query_response = self.get_node_info(debug=run_with_debug)
        chain_height_response = int(node_info_query_response['chain']['height'])
        if run_with_debug:
            print('Chain height response: ' + str(chain_height_response))
            print()
        return chain_height_response

    def get_node_info(self, debug=False):
        run_with_debug = debug
        node_info_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        response = json.loads(Iou.get_from_curl(node_info_query_url))
        if run_with_debug:
            print('Node info query response:')
            print('{')
            for key in list(response.keys()):
                print('\t' + key + ': ' + str(response[key]))
            print('}')
            print()
        return response

    def reset_chain(self, desired_height):
        chain_reset_request_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/reset'
        chain_reset_request_data = '{"height":' + str(desired_height) + '}'
        return json.loads(Iou.get_from_curl_with_data(chain_reset_request_url,
                                                      data=chain_reset_request_data))['success']

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

    def get_blockchain_info(self, debug=False):  # rpc
        run_with_debug = debug
        blockchain_info_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        blockchain_info_query_data = '{"method":"getblockchaininfo"}'
        response = json.loads(Iou.get_from_curl_with_data(blockchain_info_query_url,
                                                          data=blockchain_info_query_data))['result']
        return response

    def get_block_header_by_hash(self, block_hash, debug=False):  # rpc
        run_with_debug = debug
        blockchain_info_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        blockchain_info_query_data = '{"method":"getblockheader","params":["' + block_hash + '", 1]}'
        response = json.loads(Iou.get_from_curl_with_data(blockchain_info_query_url,
                                                          data=blockchain_info_query_data))['result']
        return response

    def get_block_hash_by_height(self, height, debug=False):  # rpc
        run_with_debug = debug
        blockchain_info_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        blockchain_hash_query_data = '{"method":"getblockhash","params":[' + str(height) + ']}'
        response = json.loads(Iou.get_from_curl_with_data(blockchain_info_query_url,
                                                          data=blockchain_hash_query_data))['result']
        # response = Iou.get_from_curl_with_data(blockchain_info_query_url, data=blockchain_hash_query_data)
        return response

    def get_block_by_height(self, height, debug=False):  # cli
        run_with_debug = debug
        block_by_height_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/block/' + str(height)
        response = json.loads(Iou.get_from_curl(block_by_height_query_url))
        return response

    def get_names(self, debug=False):  # rpc
        run_with_debug = debug
        blockchain_names_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        blockchain_names_query_data = '{"method":"getnames"}'
        response = json.loads(Iou.get_from_curl_with_data(blockchain_names_query_url,
                                                          data=blockchain_names_query_data))['result']
        return response

    def get_name_info(self, name, debug=False):  # rpc
        run_with_debug = debug
        blockchain_name_info_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        blockchain_name_info_query_data = '{"method":"getnameinfo","params":["' + name + '"]}'
        response = json.loads(Iou.get_from_curl_with_data(blockchain_name_info_query_url,
                                                          data=blockchain_name_info_query_data))['result']
        return response

    def get_name_resource(self, name, debug=False):  # rpc
        run_with_debug = debug
        blockchain_name_resource_query_url = 'http://127.0.0.1:' + self.node_config['ports']['http'] + '/'
        blockchain_name_resource_query_data = '{"method":"getnameresource","params":["' + name + '"]}'
        response = json.loads(Iou.get_from_curl_with_data(blockchain_name_resource_query_url,
                                                          data=blockchain_name_resource_query_data))['result']
        return response

    # node_query_data = '{"method":"<method_name>","params":["' + <method_parameter_string> + '"]}'
    # node_query_json = json.loads(Iou.get_from_curl_with_data(node_query_url, data=node_query_data))['result']
