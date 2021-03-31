import IOUtility as Iou
import json
import time
import shutil
from os import path
import tornado.options
import tornado.web
from tornado import gen, httpclient, ioloop
import AsyncRequestUtility as Aru
from uuid import uuid4
import random
import AsyncNodeManager as Anm
import pathlib


def calculate_intervals(name_interval, network='testnet'):
    return network


async def run_client(subprocess_index, user_home_directory, intervals, network='testnet'):
    run_with_debug = True
    interval_names = sorted([ik for ik in intervals.keys()])
    interval_name = interval_names[subprocess_index]
    name_interval = {interval_name: intervals[interval_name]}

    # print('Running client subprocess ' + str(subprocess_index) + '.')

    handshake_code_directory_prefix = user_home_directory + '/Documents/handshake/hsd'
    handshake_data_directory_prefix = user_home_directory + '/Documents/scripts/data'
    node_config_path = handshake_data_directory_prefix + '/config/node_config.txt'
    node_config = json.loads(Iou.read_from_file(node_config_path))
    for port_key in node_config['ports']:
        node_config['ports'][port_key] = str(int(node_config['ports'][port_key]) + 100 * subprocess_index)
    node_config['config_directory_prefix'] = node_config['config_directory_prefix'] + '_' + str(subprocess_index)

    async_node_manager = Anm.AsyncNodeManager(node_config, handshake_code_directory_prefix)

    # node_config_directory_prefix = node_config['config_directory_prefix']
    blockchain_directory_prefix = handshake_data_directory_prefix + '/blockchain'
    blocks_directory_prefix = blockchain_directory_prefix + '/blocks'
    names_directory_prefix = blockchain_directory_prefix + '/names'
    transactions_directory_prefix = blockchain_directory_prefix + '/transactions'

    blockchain_directory_prefix_dict = {'blockchain_directory_prefix': blockchain_directory_prefix,
                                        'blocks_directory_prefix': blocks_directory_prefix,
                                        'names_directory_prefix': names_directory_prefix,
                                        'transactions_directory_prefix': transactions_directory_prefix}

    # TODO: Copy interval method from server
    # calculate_intervals(name_interval, network=network)
    intervals[interval_name] = {}

    # TODO: Bring iterative deconstruction up to date with async methods
    # iterative deconstruction


async def initialize_default_local_blockchain(user_home_directory, gztar_name):
    gztar_path = '/'.join([user_home_directory, '.'.join([gztar_name, 'tar', 'gz'])])

    if not (path.exists(gztar_path) and path.isfile(gztar_path)):
        # await request_utility.get_blockchain(gztar_path)
        return False

    blockchain_name = '.hsd'  # TODO: Parameter or configuration dict/file
    blockchain_path = '/'.join([user_home_directory, blockchain_name])
    if path.exists(blockchain_path) and path.isdir(blockchain_path):
        shutil.rmtree(blockchain_path)
    shutil.unpack_archive(gztar_path, blockchain_path, 'gztar')
    return True


async def initialize_all_local_blockchains(request_utility, user_home_directory, gztar_name, subprocesses):
    gztar_path = '/'.join([user_home_directory, '.'.join([gztar_name, 'tar', 'gz'])])

    if not (path.exists(gztar_path) and path.isfile(gztar_path)):
        await request_utility.get_blockchain(gztar_path)

    with open(gztar_path, 'rb') as gzt:
        blockchain = gzt.read()
        for sp in range(subprocesses):
            sp_gztar_path = '/'.join([user_home_directory, '.'.join(['_'.join([gztar_name, str(sp)]), 'tar', 'gz'])])
            if not(path.exists(sp_gztar_path) and path.isfile(sp_gztar_path)):
                with open(sp_gztar_path, 'ab') as spgzt:
                    spgzt.write(blockchain)
            blockchain_name = '.hsd'  # TODO: Parameter or configuration dict/file
            sp_blockchain_path = '/'.join([user_home_directory, '_'.join([blockchain_name, str(sp)])])
            if path.exists(sp_blockchain_path) and path.isdir(sp_blockchain_path):
                shutil.rmtree(sp_blockchain_path)
            shutil.unpack_archive(sp_gztar_path, sp_blockchain_path, 'gztar')


async def tests():
    username = await Anm.async_identify_username()
    user_home_directory = '/home/' + username

    handshake_code_directory_prefix = user_home_directory + '/Documents/handshake/hsd'
    handshake_data_directory_prefix = user_home_directory + '/Documents/scripts/data'
    node_config_path = handshake_data_directory_prefix + '/config/node_config.txt'
    node_config = json.loads(Iou.read_from_file(node_config_path))

    # Not currently used with current version of tests
    '''
    control_server_ip_address = '127.0.0.1'
    control_server_port_number = '8080'
    request_utility = Aru.AsyncRequestUtility(control_server_ip_address, control_server_port_number)
    '''

    gztar_name = 'blockchain'
    default_local_blockchain_initialized = await initialize_default_local_blockchain(user_home_directory, gztar_name)
    if not default_local_blockchain_initialized:
        return

    debug = False

    connections = await Anm.async_identify_connections()
    async_node_manager = Anm.AsyncNodeManager(node_config, handshake_code_directory_prefix)

    block_results = {}
    max_height = -1

    await Anm.async_manage_connections(connections, action='disconnect', debug=debug)
    await async_node_manager.async_start_node(start_delay=5, debug=debug)

    # tests here
    try:
        transactions = {}
        current_path = str(pathlib.Path(__file__).parent.absolute())
        transactions_path = '/'.join([current_path, 'transactions.txt'])
        with open(transactions_path, 'r') as f:
            transactions = json.loads(f.read())
        if len(transactions) == 0:
            return

        name = 'tieshun'
        name_results_path = '/'.join([current_path, 'notes', '_'.join([name, 'results.txt'])])
        if not (path.exists(name_results_path) and path.isfile(name_results_path)):
            if debug:
                print('Querying')

            current_height = await async_node_manager.async_get_chain_height()
            max_height = current_height
            for target_height in range(0, current_height + 1)[::-1]:
                if target_height % 1000 == 0:
                    print(target_height)
                    print()
                if target_height != current_height:
                    success = await async_node_manager.async_reset_chain(target_height, request_timeout=0)
                    if not success:
                        print('Failed reset.')
                        break
                name_info = await async_node_manager.async_get_name_info(name)
                name_resource = await async_node_manager.async_get_name_resource(name)
                block_results[target_height] = {'name_info': name_info, 'name_resource': name_resource}
            with open(name_results_path, 'a') as f:
                f.write(json.dumps(block_results))
        else:
            if debug:
                print('Loading')
            with open(name_results_path, 'r') as f:
                block_results = json.loads(f.read())
            max_height = len(block_results) - 1

        # TODO: Restore chain at end of this block so it can be included with subsequent test
        '''
        current_height = None
        first_time = True
        while first_time or current_height >= 0:
            if debug:
                print('Pausing to allow for stopping.')
                await gen.sleep(10)
            if current_height is None:
                current_height = await async_node_manager.async_get_chain_height(debug=debug)
                first_time = False
            if debug:
                print(current_height)

            reset_target_offset = 1
            reset_target = max(0, current_height - reset_target_offset)
            success = await async_node_manager.async_reset_chain(reset_target)
            if debug:
                print(success)

            async_blockchain_info = await async_node_manager.async_get_blockchain_info(debug=debug)
            async_node_info = await async_node_manager.async_get_node_info(debug=debug)
            current_height = int(async_node_info['chain']['height'])
            
            if debug:
                if current_height % 100 == 10:
                    print(current_height)
                    print()

            if not success or current_height is None:
                print('Failed.')
                break
            elif current_height == 0:
                print('Finished.')
                break
        '''
    except Exception as e:
        print("Error: " + str(e))

    await async_node_manager.async_stop_node(stop_delay=0, debug=debug)
    await Anm.async_manage_connections(connections, action='connect', debug=debug)

    intervals = []
    states = {
        'OPENING': 0,
        'LOCKED': 1,
        'BIDDING': 2,
        'REVEAL': 3,
        'CLOSED': 4,
        'REVOKED': 5
    }
    reverse_states = {
        -1: 'NONE',
        0: 'OPENING',
        1: 'LOCKED',
        2: 'BIDDING',
        3: 'REVEAL',
        4: 'CLOSED',
        5: 'REVOKED'
    }
    current_name_state = -1
    current_interval_start = 0
    for block_height in range(0, max_height + 1):
        if block_results[str(block_height)]['name_info']['info'] is None:  # state is -1
            if current_name_state != -1:
                interval = [current_name_state, current_interval_start, block_height]
                intervals.append(interval)
                current_interval_start = block_height
                current_name_state = -1
        else:
            state_string = block_results[str(block_height)]['name_info']['info']['state']
            new_name_state = states[state_string]
            if new_name_state != current_name_state:
                interval = [current_name_state, current_interval_start, block_height]
                intervals.append(interval)
                current_interval_start = block_height
                current_name_state = new_name_state
    if current_interval_start != max_height:
        interval = [current_name_state, current_interval_start, max_height + 1]
        intervals.append(interval)
    for interval in intervals:
        print(reverse_states[interval[0]] + ': ' + str(interval[1]) + ' -> ' + str(interval[2]))
    print('Finished tests.')


async def main():
    testing = False
    if testing:
        await tests()
    else:
        control_server_ip_address = '127.0.0.1'
        control_server_port_number = '8080'
        url_prefix = '/'.join(['http:', '', ':'.join([control_server_ip_address, control_server_port_number])])
        user_home_directory = '/home/dannya951'
        max_subprocesses = 5
        network = 'testnet'
        clients_working = True
        debug = True

        request_utility = Aru.AsyncRequestUtility(control_server_ip_address, control_server_port_number)
        post_clients_code = await request_utility.post_clients()
        if post_clients_code is None:
            print('Failed to create new clients.')
            clients_working = False

        while clients_working:
            intervals = await request_utility.get_client()
            interval_subprocesses = len(intervals)
            interval_subprocesses = min(interval_subprocesses, max_subprocesses)
            if interval_subprocesses == 0:
                # server is done allocating blocks, break from while loop
                clients_working = False
            else:
                gztar_name = 'blockchain'
                await initialize_all_local_blockchains(
                    request_utility,
                    user_home_directory,
                    gztar_name,
                    interval_subprocesses
                )

                for interval in intervals:
                    await request_utility.post_results({interval: {}})

                connections = await Anm.async_identify_connections()
                await Anm.async_manage_connections(connections, 'disconnect', debug=debug)

                if debug:
                    print('Starting ' + str(interval_subprocesses) + ' client subprocesses.')

                interval_names = sorted([ik for ik in intervals.keys()])
                clients = gen.multi([run_client(subprocess_index,
                                                user_home_directory,
                                                intervals,
                                                network=network)
                                     for subprocess_index in range(interval_subprocesses)])
                await clients

                await Anm.async_manage_connections(connections, 'connect', debug=debug)

                for subprocess_index in range(interval_subprocesses):
                    interval_name = interval_names[subprocess_index]
                    await request_utility.put_client({interval_name: intervals[interval_name]})
                    await request_utility.put_result({interval_name: intervals[interval_name]})


if __name__ == "__main__":
    start_time = time.time()
    print('Starting client.')
    ioloop.IOLoop.current().run_sync(main)
    print('Stopped client.')
    elapsed_seconds = int((time.time() - start_time) + 0.5)
    remainder_seconds = elapsed_seconds % 60
    elapsed_minutes = int((elapsed_seconds - remainder_seconds) / 60)
    print('Elapsed Time: ' + str(elapsed_minutes) + ' minutes and ' + str(remainder_seconds) + ' seconds')


