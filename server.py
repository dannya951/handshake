import json
import shutil
import pathlib
import time
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import NodeManager as Nm
import IOUtility as Iou
import name_subset_analysis as nsa
import temporal_analysis as ta

from tornado.options import define, options
from os import path

define("port", default=8080, type=int)

api_help_message = ('\n'
                    '\n'
                    'The API schema for this server is as follows:'
                    '\n'
                    '\n    /'
                    '\n        GET: Get this help page.'
                    '\n'
                    '\n    /server'
                    '\n        GET: Get diagnostic data on the server.'
                    '\n        DELETE: Stop and close this server.'
                    '\n'
                    '\n    /clients'
                    '\n        POST: Create a new client resource.'
                    '\n            Required body format: {"client_id": <client_id>}'
                    '\n'
                    '\n    /clients/<client_id>'
                    '\n        GET: Get the next available name-interval allocation for the client.'
                    '\n        PUT: Update the server with the client\'s current progress.'
                    '\n            Required body format: {<name>: {}}'
                    '\n        DELETE: Remove this client\'s profile from the server.'
                    '\n'
                    '\n    /blockchain'
                    '\n        GET: Get a compressed (tar.gz) copy of the blockchain.'
                    '\n'
                    '\n    /results'
                    '\n        POST: Create a new result resource, mapping a name to its data.'
                    '\n            Required body format: {<name>: {}}'
                    '\n'
                    '\n    /results/<name>'
                    '\n        GET: Get a copy of the result resource.'
                    '\n        PUT: Update the result resource with the client\'s query responses.'
                    '\n        DELETE: Remove this result resource from the server.'
                    '\n')


def perform_iterative_deconstruction(hsd_directory_path, name_dicts):
    username = Nm.identify_username()
    user_home_directory = '/home/' + username

    handshake_code_directory_prefix = user_home_directory + '/Documents/handshake/hsd'
    handshake_data_directory_prefix = user_home_directory + '/Documents/scripts/data'
    node_config_path = handshake_data_directory_prefix + '/config/node_config.txt'
    node_config = json.loads(Iou.read_from_file(node_config_path))

    debug = False

    connections = Nm.identify_connections()
    node_manager = Nm.NodeManager(node_config, handshake_code_directory_prefix)
    max_height = 40210
    event_height_to_name_list_dict = {max_height: []}
    for name in name_dicts:
        name_intervals = name_dicts[name]['intervals']
        for interval in name_intervals:
            interval_start_block = interval[1]
            if interval_start_block not in event_height_to_name_list_dict:
                event_height_to_name_list_dict[interval_start_block] = []
            event_height_to_name_list_dict[interval_start_block].append(name)
        if name not in event_height_to_name_list_dict[max_height]:
            event_height_to_name_list_dict[max_height].append(name)

    Nm.manage_connections(connections, action='disconnect')
    node_manager.start_node()
    try:
        for height in range(0, max_height + 1)[::-1]:
            if height < max_height:
                if not node_manager.reset_chain(height):
                    break
            if height in event_height_to_name_list_dict:
                for name in event_height_to_name_list_dict[height]:
                    name_info = node_manager.get_name_info(name)
                    name_resource = node_manager.get_name_resource(name)
                    if 'name_infos' not in name_dicts[name]:
                        name_dicts[name]['name_infos'] = {}
                    name_dicts[name]['name_infos'][height] = name_info
                    if 'name_resources' not in name_dicts[name]:
                        name_dicts[name]['name_resources'] = {}
                    name_dicts[name]['name_resources'][height] = name_resource
            if debug:
                if height % 2000 == 0:
                    print('Checkpoint: ' + str(height))
    except Exception as e:
        print("Error: " + str(e))

    node_manager.stop_node()
    Nm.manage_connections(connections, action='connect')


def update_block_headers(hsd_directory_path, block_headers):
    username = Nm.identify_username()
    user_home_directory = '/home/' + username

    handshake_code_directory_prefix = user_home_directory + '/Documents/handshake/hsd'
    handshake_data_directory_prefix = user_home_directory + '/Documents/scripts/data'
    node_config_path = handshake_data_directory_prefix + '/config/node_config.txt'
    node_config = json.loads(Iou.read_from_file(node_config_path))

    debug = False

    connections = Nm.identify_connections()
    node_manager = Nm.NodeManager(node_config, handshake_code_directory_prefix)

    Nm.manage_connections(connections, action='disconnect')
    node_manager.start_node()
    try:
        max_height = 40210
        for height in range(max_height + 1):
            block_hash = node_manager.get_block_hash_by_height(height)
            block_header = node_manager.get_block_header_by_hash(block_hash)
            block_info = node_manager.get_block_by_height(height)
            block_header['tx_count'] = len(block_info['txs'])
            block_headers[height] = block_header
            if debug:
                if height % 1000 == 0:
                    print(height)
    except Exception as e:
        print("Error: " + str(e))

    node_manager.stop_node()
    Nm.manage_connections(connections, action='connect')


def perform_analysis(hsd_directory_path):
    gztar_name = 'blockchain'
    initialize_default_local_blockchain(hsd_directory_path, gztar_name)

    name_dicts = {}
    current_path = str(pathlib.Path(__file__).parent.absolute())
    path_to_name_interval_records_file = '/'.join([current_path, 'names_with_intervals.txt'])
    if not (path.exists(path_to_name_interval_records_file) and path.isfile(path_to_name_interval_records_file)):
        update_name_intervals(hsd_directory_path, name_dicts)
        try:
            with open(path_to_name_interval_records_file, 'w') as f:
                f.write(json.dumps(name_dicts))
        except Exception as e:
            print("Error: " + str(e))
    else:
        with open(path_to_name_interval_records_file, 'r') as f:
            name_dicts = json.loads(f.read())

    block_headers = {}
    path_to_block_header_records_file = '/'.join([current_path, 'block_headers.txt'])
    if not (path.exists(path_to_block_header_records_file) and path.isfile(path_to_block_header_records_file)):
        update_block_headers(hsd_directory_path, block_headers)
        try:
            with open(path_to_block_header_records_file, 'w') as f:
                f.write(json.dumps(block_headers))
        except Exception as e:
            print("Error: " + str(e))
    else:
        with open(path_to_block_header_records_file, 'r') as f:
            block_headers = json.loads(f.read())

    path_to_names_with_info_record_file = '/'.join([current_path, 'complete_name_info.txt'])
    if not (path.exists(path_to_names_with_info_record_file) and path.isfile(path_to_names_with_info_record_file)):
        perform_iterative_deconstruction(hsd_directory_path, name_dicts)
        try:
            with open(path_to_names_with_info_record_file, 'w') as f:
                f.write(json.dumps(name_dicts))
        except Exception as e:
            print("Error: " + str(e))
    else:
        with open(path_to_names_with_info_record_file, 'r') as f:
            name_dicts = json.loads(f.read())

    nsa.perform_name_subset_analysis(name_dicts, block_headers)
    ta.perform_temporal_analysis(name_dicts, block_headers)


def compute_intervals(exposed_name_dict, network='testnet'):
    network_values = get_network_values(network=network)
    tree_interval = network_values['tree_interval']
    lockup_period = network_values['lockup_period']
    bidding_period = network_values['bidding_period']
    reveal_period = network_values['reveal_period']
    renewal_window = network_values['renewal_window']
    auction_maturity = network_values['auction_maturity']
    open_period = tree_interval + 1

    intervals = []
    name_state = -1
    state_start_height = 0
    state_end_height = -1
    closed_update_height_saver = -1
    max_height = 40210
    name = exposed_name_dict['name']
    debug = False
    was_registered = False
    has_redeemed = False
    action_taken = False

    for block_height in range(max_height + 1):
        action_taken = False
        block_height_str = str(block_height)
        cov_types = []
        if block_height_str in exposed_name_dict['blocks']:
            block_txs = exposed_name_dict['blocks'][str(block_height)]
            for tx in block_txs:
                for out in tx['outputs']:
                    out_cov = out['covenant']
                    out_cov_type = out_cov['type']
                    if out_cov_type != 0:
                        name_hash = out_cov['items'][0]
                        if name_hash == exposed_name_dict['name_hash']:
                            cov_types.append(out_cov_type)
                            if debug:
                                print(block_height_str)
                                print(json.dumps(out_cov, indent=2))
                                print()
        if len(cov_types) > 0:
            for cov_type in cov_types:
                if name_state == -1:  # Unregistered
                    if cov_type == 2:
                        action_taken = True
                        interval = [name_state, state_start_height, block_height]
                        intervals.append(interval)

                        last_name_state = name_state
                        name_state = 0
                        state_start_height = block_height
                        state_end_height = state_start_height + open_period
                        if debug:
                            print(block_height_str + ': ' + str(last_name_state) + ' -> ' + str(name_state))
                            print()

                elif name_state == 0:  # Opening
                    if cov_type == 3:
                        action_taken = True
                        interval = [name_state, state_start_height, state_end_height]
                        intervals.append(interval)

                        last_name_state = name_state
                        name_state = 2
                        state_start_height = state_end_height
                        state_end_height = state_start_height + bidding_period
                        if debug:
                            print(block_height_str + ': ' + str(last_name_state) + ' -> ' + str(name_state))
                            print()

                elif name_state == 2:  # Bidding
                    if cov_type == 4 or cov_type == 5:
                        action_taken = True
                        has_redeemed = True
                        interval = [name_state, state_start_height, state_end_height]
                        intervals.append(interval)

                        last_name_state = name_state
                        name_state = 3
                        state_start_height = state_end_height
                        state_end_height = state_start_height + reveal_period
                        if debug:
                            print(block_height_str + ': ' + str(last_name_state) + ' -> ' + str(name_state))
                            print()
                            print(str(interval))
                            print()
                            print(str([name_state, state_start_height, state_end_height]))
                            print()

                elif name_state == 3:
                    if cov_type == 4 or cov_type == 5:
                        action_taken = True
                        has_redeemed = True
                        interval = [name_state, state_start_height, state_end_height]
                        intervals.append(interval)

                        last_name_state = name_state
                        name_state = 4
                        state_start_height = state_end_height
                        state_end_height = state_start_height + renewal_window - open_period - bidding_period - reveal_period
                        if debug:
                            print(block_height_str + ': ' + str(last_name_state) + ' -> ' + str(name_state))
                            print()

                    elif cov_type == 6:
                        action_taken = True
                        was_registered = True
                        interval = [name_state, state_start_height, state_end_height]
                        intervals.append(interval)

                        last_name_state = name_state
                        name_state = 4
                        state_start_height = state_end_height
                        state_end_height = state_start_height + renewal_window
                        if debug:
                            print(block_height_str + ': ' + str(last_name_state) + ' -> ' + str(name_state))
                            print()

                elif name_state == 4:
                    if cov_type == 2:
                        action_taken = True
                        name_state = -1
                        was_registered = False
                        has_redeemed = False

                        interval = [name_state, state_start_height, block_height]
                        intervals.append(interval)

                        last_name_state = name_state
                        name_state = 0
                        state_start_height = block_height
                        state_end_height = state_start_height + open_period
                        if debug:
                            print(block_height_str + ': ' + str(last_name_state) + ' -> ' + str(name_state))
                            print()

                    elif cov_type == 4 or cov_type == 5:
                        has_redeemed = True

                    elif cov_type == 6:
                        action_taken = True

                        name_state = 6

                        interval = [name_state, state_start_height, block_height]
                        intervals.append(interval)

                        name_state = 4

                        state_start_height = block_height
                        state_end_height = state_start_height + renewal_window
                        was_registered = True
                        has_redeemed = True

                    elif cov_type == 7:
                        action_taken = True

                        name_state = 6

                        interval = [name_state, state_start_height, block_height]
                        intervals.append(interval)

                        name_state = 4

                        last_name_state = name_state
                        if closed_update_height_saver == -1:
                            closed_update_height_saver = state_start_height
                        state_start_height = block_height

                        was_registered = True
                        has_redeemed = True

                        if debug:
                            print(block_height_str + ': ' + str(last_name_state) + ' -> ' + str(name_state))
                            print()

                    elif cov_type == 8:
                        action_taken = True

                        name_state = 6

                        interval = [name_state, state_start_height, block_height]
                        intervals.append(interval)

                        name_state = 4

                        was_registered = True
                        has_redeemed = True

                        last_name_state = name_state
                        if closed_update_height_saver == -1:
                            closed_update_height_saver = state_start_height
                        state_start_height = block_height
                        state_end_height = state_start_height + renewal_window
                        if debug:
                            print(block_height_str + ': ' + str(last_name_state) + ' -> ' + str(name_state))
                            print()

        if name_state != -1 and block_height >= state_end_height and not action_taken:
            if debug:
                print('Block ' + block_height_str + ': Entered state timeout.')
                print()

            if name_state == 0:
                interval = [name_state, state_start_height, state_end_height]
                intervals.append(interval)

                name_state = 2
                state_start_height = state_end_height
                state_end_height = state_start_height + bidding_period
            elif name_state == 2:
                interval = [name_state, state_start_height, state_end_height]
                intervals.append(interval)
                has_redeemed = False

                name_state = 3
                state_start_height = state_end_height
                state_end_height = state_start_height + reveal_period
            elif name_state == 3:
                interval = [name_state, state_start_height, state_end_height]
                intervals.append(interval)

                was_registered = False

                name_state = 4
                state_start_height = state_end_height
                state_end_height = state_end_height + renewal_window - open_period - bidding_period - reveal_period

            elif name_state == 4:
                if has_redeemed:
                    if not was_registered:
                        name_state = -2
                    else:
                        name_state = 6
                    interval = [name_state, state_start_height, state_end_height]
                    intervals.append(interval)
                    state_start_height = state_end_height

                has_redeemed = False
                was_registered = False

                name_state = -1
                state_end_height = -1
                closed_update_height_saver = -1

    if state_start_height != max_height:
        if name_state == 4:
            if was_registered:
                name_state = 6
            elif has_redeemed:
                name_state = -2
            else:
                name_state = -1

        interval = [name_state, state_start_height, max_height + 1]
        intervals.append(interval)

    exposed_name_dict['intervals'] = intervals


def get_network_values(network='testnet'):
    # testnet values
    testnet_pow_target_spacing = 10 * 60
    testnet_pow_blocks_per_day = int((24 * 60 * 60) / testnet_pow_target_spacing)
    testnet_auction_start = int(0.25 * testnet_pow_blocks_per_day)
    testnet_rollout_interval = int(0.25 * testnet_pow_blocks_per_day)
    testnet_lockup_period = int(0.25 * testnet_pow_blocks_per_day)
    testnet_renewal_window = 30 * testnet_pow_blocks_per_day
    testnet_claim_period = 90 * testnet_pow_blocks_per_day
    testnet_bidding_period = 1 * testnet_pow_blocks_per_day
    testnet_reveal_period = 2 * testnet_pow_blocks_per_day
    testnet_tree_interval = int(testnet_pow_blocks_per_day / 4)
    testnet_transfer_lockup = 2 * testnet_pow_blocks_per_day
    testnet_auction_maturity = (1 + 2 + 4) * testnet_pow_blocks_per_day
    testnet_no_rollout = False
    testnet_no_reserved = False

    # main values
    main_pow_target_spacing = 10 * 60
    main_pow_blocks_per_day = int((24 * 60 * 60) / main_pow_target_spacing)
    main_auction_start = 10 * main_pow_blocks_per_day
    main_rollout_interval = 7 * main_pow_blocks_per_day
    main_lockup_period = 30 * main_pow_blocks_per_day
    main_renewal_window = (2 * 365) * main_pow_blocks_per_day
    main_claim_period = (4 * 365) * main_pow_blocks_per_day
    main_bidding_period = 5 * main_pow_blocks_per_day
    main_reveal_period = 10 * main_pow_blocks_per_day
    main_tree_interval = int(main_pow_blocks_per_day / 4)
    main_transfer_lockup = 2 * main_pow_blocks_per_day
    main_auction_maturity = (5 + 10 + 14) * main_pow_blocks_per_day
    main_no_rollout = False
    main_no_reserved = False

    values = {}
    if network == 'testnet':
        values = {
            'pow_target_spacing': testnet_pow_target_spacing,
            'pow_blocks_per_day': testnet_pow_blocks_per_day,
            'auction_start': testnet_auction_start,
            'rollout_interval': testnet_rollout_interval,
            'lockup_period': testnet_lockup_period,
            'renewal_window': testnet_renewal_window,
            'claim_period': testnet_claim_period,
            'bidding_period': testnet_bidding_period,
            'reveal_period': testnet_reveal_period,
            'tree_interval': testnet_tree_interval,
            'transfer_lockup': testnet_transfer_lockup,
            'auction_maturity': testnet_auction_maturity,
            'no_rollout': testnet_no_rollout,
            'no_reserved': testnet_no_reserved
        }
    if network == 'main':
        values = {
            'pow_target_spacing': main_pow_target_spacing,
            'pow_blocks_per_day': main_pow_blocks_per_day,
            'auction_start': main_auction_start,
            'rollout_interval': main_rollout_interval,
            'lockup_period': main_lockup_period,
            'renewal_window': main_renewal_window,
            'claim_period': main_claim_period,
            'bidding_period': main_bidding_period,
            'reveal_period': main_reveal_period,
            'tree_interval': main_tree_interval,
            'transfer_lockup': main_transfer_lockup,
            'auction_maturity': main_auction_maturity,
            'no_rollout': main_no_rollout,
            'no_reserved': main_no_reserved
        }
    return values


def get_intervals_from_file(exposed_name_dict):
    name_results_by_block_from_file = {}
    max_height = 25000  # Hold over for compatibility testing against previous exhaustive method
    name_from_name_dict = exposed_name_dict['name']
    try:
        current_path = str(pathlib.Path(__file__).parent.absolute())
        path_to_name_results_file = '/'.join([current_path, 'data', 'blockchain', 'names', '.'.join([name_from_name_dict, 'txt'])])
        if not (path.exists(path_to_name_results_file) and path.isfile(path_to_name_results_file)):
            return []
        else:
            with open(path_to_name_results_file, 'r') as f:
                name_results_by_block_from_file = json.loads(f.read())
            for block_height in name_results_by_block_from_file:

                registered_at_block = name_results_by_block_from_file[str(block_height)]['name_record']['registered']
                name_results_by_block_from_file[str(block_height)]['registered'] = registered_at_block
                del name_results_by_block_from_file[str(block_height)]['name_record']
    except Exception as e:
        print("Error: " + str(e))

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
        -2: 'UNREGISTERED',
        -1: 'INACTIVE',
        0: 'OPENING',
        1: 'LOCKED',
        2: 'BIDDING',
        3: 'REVEAL',
        4: 'CLOSED',
        5: 'REVOKED',
        6: 'REGISTERED'
    }
    current_name_state = -1
    current_interval_start = 0
    currently_registered = False
    for block_height in range(0, max_height + 1):
        block_not_present = str(block_height) not in name_results_by_block_from_file
        if block_not_present or name_results_by_block_from_file[str(block_height)]['name_info']['info'] is None:  # state is -1
            if current_name_state != -1:
                if current_name_state == 4 and not currently_registered:
                    current_name_state = -2
                elif current_name_state == 4:
                    current_name_state = 6
                interval = [current_name_state, current_interval_start, block_height]
                intervals.append(interval)
                current_interval_start = block_height
                current_name_state = -1
        else:
            state_string = name_results_by_block_from_file[str(block_height)]['name_info']['info']['state']
            new_name_state = states[state_string]
            if new_name_state != current_name_state:
                if current_name_state == 4 and not currently_registered:
                    current_name_state = -2
                elif current_name_state == 4:
                    current_name_state = 6
                interval = [current_name_state, current_interval_start, block_height]
                intervals.append(interval)
                current_interval_start = block_height
                current_name_state = new_name_state
        if str(block_height) in name_results_by_block_from_file:
            currently_registered = name_results_by_block_from_file[str(block_height)]['registered']
    if current_interval_start != max_height:
        if current_name_state == 4:
            if not currently_registered:
                if name_results_by_block_from_file[str(max_height)]['name_info']['info'] is None:
                    current_name_state = -1
                else:
                    current_name_state = -2
            else:
                current_name_state = 6
        interval = [current_name_state, current_interval_start, max_height + 1]
        intervals.append(interval)
    return intervals


def condense_intervals(intervals):  # only exists to conform current intervals to same format as old intervals
    element_placeholder = None
    new_condensed_interval = []
    for interval in intervals:
        if element_placeholder is None:
            element_placeholder = interval
        else:
            previous_name_state = element_placeholder[0]
            this_element_name_state = interval[0]
            if previous_name_state == this_element_name_state:
                element_placeholder = [this_element_name_state, element_placeholder[1], interval[2]]
            else:
                new_condensed_interval.append(element_placeholder)
                element_placeholder = interval
    if element_placeholder is not None:
        new_condensed_interval.append(element_placeholder)
    return new_condensed_interval


def update_name_intervals(hsd_directory_path, name_dicts_to_update):
    reverse_states = {
        -2: 'UNREGISTERED',
        -1: 'INACTIVE',
        0: 'OPENING',
        1: 'LOCKED',
        2: 'BIDDING',
        3: 'REVEAL',
        4: 'CLOSED',
        5: 'REVOKED',
        6: 'ACTIVE'
    }

    update_name_transaction_blocks(hsd_directory_path, name_dicts_to_update)
    debug = False

    for name_being_updated in name_dicts_to_update:
        compute_intervals(name_dicts_to_update[name_being_updated])
    # Removed check that verified output against previous exhaustive method.


def update_name_transaction_blocks(hsd_directory_path, name_dicts_to_update):
    update_name_hashes(hsd_directory_path, name_dicts_to_update)

    current_path = str(pathlib.Path(__file__).parent.absolute())
    path_to_name_transaction_records_file = '/'.join([current_path, 'transactions.txt'])
    hash_to_name_map = {}
    for name_being_updated in name_dicts_to_update:
        name_hash = name_dicts_to_update[name_being_updated]['name_hash']
        hash_to_name_map[name_hash] = name_being_updated

    if not (path.exists(path_to_name_transaction_records_file) and path.isfile(path_to_name_transaction_records_file)):
        user_home_directory = hsd_directory_path.rsplit('/', 1)[0]
        handshake_code_directory_prefix = user_home_directory + '/Documents/handshake/hsd'

        node_config_path = '/'.join([current_path, 'data', 'config', 'node_config.txt'])
        node_config = json.loads(Iou.read_from_file(node_config_path))
        node_manager = Nm.NodeManager(node_config, handshake_code_directory_prefix)
        connections = Nm.identify_connections()

        Nm.manage_connections(connections, action='disconnect')
        node_manager.start_node(start_delay=10.0)
        try:
            chain_height = node_manager.get_chain_height()
            transactions_corresponding_to_update_name = {}
            for block_height in range(0, chain_height + 1):
                block = node_manager.get_block_by_height(block_height)
                block_transactions = block['txs']
                name_transactions_from_current_block = {}
                for tx in block_transactions:
                    tx_fee = tx['fee']
                    tx_rate = tx['rate']
                    tx_time = tx['mtime']
                    tx_hash = tx['hash']
                    tx_index = tx['index']
                    names_to_update_with_transactions = set()
                    ins = []
                    for tx_in in tx['inputs']:
                        tx_coin_cov = None
                        if 'coin' in tx_in:
                            tx_coin_cov = tx_in['coin']['covenant']
                        else:
                            ins.append({'address': None})
                        if tx_coin_cov is not None:
                            tx_coin = tx_in['coin']
                            coin = {
                                'height': tx_coin['height'],
                                'value': tx_coin['value'],
                                'address': tx_coin['address'],
                                'covenant': tx_coin['covenant']
                            }
                            ins.append(coin)

                            tx_cov_items = tx_coin_cov['items']
                            if len(tx_cov_items) > 0:
                                name_hash_from_tx_cov = tx_cov_items[0]
                                name_from_hash = hash_to_name_map[name_hash_from_tx_cov]
                                names_to_update_with_transactions.add(name_from_hash)
                    outs = []
                    for tx_out in tx['outputs']:
                        coin = {
                            'value': tx_out['value'],
                            'address': tx_out['address'],
                            'covenant': tx_out['covenant']
                        }
                        outs.append(coin)

                        tx_cov_items = tx_out['covenant']['items']
                        if len(tx_cov_items) > 0:
                            name_hash_from_tx_cov = tx_cov_items[0]
                            name_from_hash = hash_to_name_map[name_hash_from_tx_cov]
                            names_to_update_with_transactions.add(name_from_hash)

                    reduced_tx = {
                        'fee': tx_fee,
                        'rate': tx_rate,
                        'mtime': tx_time,
                        'index': tx_index,
                        'hash': tx_hash,
                        'inputs': ins,
                        'outputs': outs
                    }
                    for name_to_update in names_to_update_with_transactions:
                        if name_to_update not in name_transactions_from_current_block:
                            name_transactions_from_current_block[name_to_update] = []
                        name_transactions_from_current_block[name_to_update].append(reduced_tx)

                for name_to_update_from_block in name_transactions_from_current_block:
                    if 'blocks' not in name_dicts_to_update[name_to_update_from_block]:
                        name_dicts_to_update[name_to_update_from_block]['blocks'] = {}
                        name_dicts_to_update[name_to_update_from_block]['intervals'] = []
                    new_name_transactions_list = name_transactions_from_current_block[name_to_update_from_block]
                    name_dicts_to_update[name_to_update_from_block]['blocks'][block_height] = new_name_transactions_list

            with open(path_to_name_transaction_records_file, 'w') as f:
                f.write(json.dumps(name_dicts_to_update))

        except Exception as e:
            print("Error: " + str(e))
        node_manager.stop_node(stop_delay=10.0)
        Nm.manage_connections(connections, action='connect')
    else:
        name_dicts_loaded_from_file = None
        with open(path_to_name_transaction_records_file, 'r') as f:
            name_dicts_loaded_from_file = json.loads(f.read())
        if name_dicts_loaded_from_file is not None:
            for name_loaded_from_file in name_dicts_loaded_from_file:
                blocks_from_file = name_dicts_loaded_from_file[name_loaded_from_file]['blocks']
                intervals_from_file = name_dicts_loaded_from_file[name_loaded_from_file]['intervals']
                name_dicts_to_update[name_loaded_from_file]['blocks'] = blocks_from_file
                name_dicts_to_update[name_loaded_from_file]['intervals'] = intervals_from_file


def update_name_hashes(hsd_directory_path, name_dicts_to_update):
    current_path = str(pathlib.Path(__file__).parent.absolute())
    path_to_name_records_file = '/'.join([current_path, 'names.txt'])

    if not (path.exists(path_to_name_records_file) and path.isfile(path_to_name_records_file)):
        user_home_directory = hsd_directory_path.rsplit('/', 1)[0]
        handshake_code_directory_prefix = user_home_directory + '/Documents/handshake/hsd'

        node_config_path = '/'.join([current_path, 'data', 'config', 'node_config.txt'])
        node_config = json.loads(Iou.read_from_file(node_config_path))
        node_manager = Nm.NodeManager(node_config, handshake_code_directory_prefix)
        connections = Nm.identify_connections()

        Nm.manage_connections(connections, action='disconnect')
        node_manager.start_node()
        try:
            hsd_get_names_result = node_manager.get_names()
            for name_record_from_hsd in hsd_get_names_result:
                name_from_record = name_record_from_hsd['name']
                updated_name_dict = {'name': name_from_record, 'name_hash': name_record_from_hsd['nameHash']}
                name_dicts_to_update[name_from_record] = updated_name_dict
            with open(path_to_name_records_file, 'w') as f:
                f.write(json.dumps(name_dicts_to_update))
        except Exception as e:
            print("Error: " + str(e))
        node_manager.stop_node()
        Nm.manage_connections(connections, action='connect')
    else:
        with open(path_to_name_records_file, 'r') as f:
            names_loaded_from_file = json.loads(f.read())
            for loaded_name in names_loaded_from_file:
                name_dicts_to_update[loaded_name] = names_loaded_from_file[loaded_name]


def initialize_default_local_blockchain(hsd_directory_path, gztar_name):
    user_home_directory = hsd_directory_path.rsplit('/', 1)[0]
    gztar_path = '/'.join([user_home_directory, '.'.join([gztar_name, 'tar', 'gz'])])

    if path.exists(hsd_directory_path) and path.isdir(hsd_directory_path):
        shutil.rmtree(hsd_directory_path)
    shutil.unpack_archive(gztar_path, hsd_directory_path, 'gztar')


def get_blockchain_archive(hsd_directory_path, gztar_name):
    current_path = str(pathlib.Path(__file__).parent.absolute())

    path_name = '/'.join([current_path, '.'.join([gztar_name, 'tar', 'gz'])])

    if not (path.exists(path_name) and path.isfile(path_name)):
        print('Making archive.')
        shutil.make_archive(gztar_name, 'gztar', hsd_directory_path)
        print('Finished archiving.')
    else:
        print('Archive already exists.')

    print('Reading in archive.')
    blockchain = None
    with open('.'.join([gztar_name, 'tar', 'gz']), 'rb') as bc:
        blockchain = bc.read()
    print('Finished reading in archive.')
    # print('Blockchain size: ' + str(sys.getsizeof(blockchain)) + ' bytes')
    return blockchain


class ServerApplication(tornado.web.Application):
    def __init__(self, hsd_directory_path):
        handlers = [
            (r'/', HelpHandler),  # done
            (r'/server', ServerHandler),
            (r'/clients/([0-9a-f]{6})', ClientHandler),  # done
            (r'/clients', ClientsHandler),  # done
            (r'/blockchain', BlockchainHandler),  # done
            (r'/results/([0-9a-zA-Z]+)', ResultHandler),  # done
            (r'/results', ResultsHandler)  # done
        ]  # TODO: Implement Service Directory Server with associated handler

        gztar_name = 'blockchain'
        initialize_default_local_blockchain(hsd_directory_path, gztar_name)

        self.name_dicts = {}
        update_name_intervals(hsd_directory_path, self.name_dicts)
        self.remaining_names = {}
        for name in self.name_dicts:
            self.remaining_names[name] = self.name_dicts[name]
        self.incomplete_intervals = {}

        self.clients = {}
        # self.incomplete_allocations = {}
        self.allocation_size = 5
        self.server_is_running = True
        self.interval_results = {}

        # TODO: Implement out efficient streaming of large file (possibly with websockets), then reduce buffer size
        tornado.web.Application.__init__(self, handlers, max_buffer_size=314572800)

    # Temporarily keeping previous allocation method for reference
    '''
    def allocate_blocks(self, client_id):
        first_block = None
        last_block = None
        if client_id not in self.clients:
            return first_block, last_block

        if 'first_block' in self.clients[client_id] and 'last_block' in self.clients[client_id]:
            first_block = self.clients[client_id]['first_block']
            last_block = self.clients[client_id]['last_block']
        else:
            if len(self.incomplete_allocations) > 0:
                incomplete_allocation = self.incomplete_allocations.pop(0)
                first_block = incomplete_allocation[0]
                last_block = incomplete_allocation[1]
            else:
                if self.remaining_blocks is None:
                    return first_block, last_block
                first_block = self.remaining_blocks[0]
                last_block = first_block + (self.allocation_size - 1)
                if last_block > self.remaining_blocks[1]:
                    last_block = self.remaining_blocks[1]
                if last_block == self.remaining_blocks[1]:
                    self.remaining_blocks = None
                else:
                    self.remaining_blocks = (last_block + 1, self.remaining_blocks[1])
            self.clients[client_id]['first_block'] = first_block
            self.clients[client_id]['last_block'] = last_block
        return first_block, last_block
    '''

    def allocate_intervals(self, client_id):  # TODO: implement time-based allocations according to client performance
        intervals = {}
        if client_id not in self.clients:
            return intervals

        if len(self.clients[client_id]) > 0:
            intervals = self.clients[client_id]
        else:
            if len(self.incomplete_intervals) > 0:
                for name_interval in self.incomplete_intervals:
                    intervals[name_interval] = self.incomplete_intervals[name_interval]
                    del self.incomplete_intervals[name_interval]
                    if len(intervals) == self.allocation_size or len(self.incomplete_intervals) == 0:
                        break
            else:
                if len(self.remaining_names) == 0:
                    return intervals
                for name_interval in self.remaining_names:
                    intervals[name_interval] = self.remaining_names[name_interval]
                    if len(intervals) == self.allocation_size or len(intervals) == len(self.remaining_names):
                        break
                for name_interval in intervals:
                    del self.remaining_names[name_interval]

            self.clients[client_id] = intervals
        return intervals

    # Temporarily keeping previous deallocation method for reference.
    '''
    def deallocate_blocks(self, client_id):
        if client_id not in self.clients:
            return
        elif not ('first_block' in self.clients[client_id] and 'last_block' in self.clients[client_id]):
            return

        incomplete_allocation = (self.clients[client_id]['first_block'], self.clients[client_id]['last_block'])
        self.incomplete_allocations.append(incomplete_allocation)
        del self.clients[client_id]['first_block']
        del self.clients[client_id]['last_block']
        return
    '''

    def deallocate_intervals(self, client_id):
        if client_id not in self.clients:
            return
        elif len(self.clients[client_id]) == 0:
            return

        for incomplete_interval in self.clients[client_id]:
            self.incomplete_intervals[incomplete_interval] = self.clients[client_id][incomplete_interval]
            del self.clients[client_id][incomplete_interval]

        return


class ResultHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    def get(self, name):
        if name not in self.application.interval_results:
            self.set_status(404, 'Not Found')
        else:
            if len(self.application.interval_results[name]) == 0:
                self.set_status(204, 'No Content')
            else:
                data = {name: self.application.interval_results[name]}
                self.set_status(200)
                self.write(data)

    def put(self, name):
        if name not in self.application.interval_results:
            self.set_status(404, 'Not Found')
        else:
            intervals = json.loads(self.request.body)
            if name not in intervals or len(intervals) > 1:
                self.set_status(406, 'Not Acceptable')
            else:
                self.application.interval_results[name] = intervals[name]
                self.set_status(200)
                self.write('Result resource updated.')

    def delete(self, name):
        if name not in self.application.interval_results:
            self.set_status(404, 'Not Found')
        else:
            del self.application.interval_results[name]
            self.set_status(200)
            self.write('Result resource deleted.')


class ResultsHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ('POST')

    def post(self):
        intervals = json.loads(self.request.body)
        if len(intervals) != 1:
            self.set_status(406, 'Not Acceptable')
        else:
            interval = [ik for ik in intervals.keys()][0]
            if interval in self.application.interval_results:
                self.set_status(403, 'Already Exists')
            else:
                self.application.interval_results[interval] = {}
                self.set_status(201)
                self.write('Created new result resource for ' + interval)


class BlockchainHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ('GET')

    async def get(self):  # TODO: Reimplement to avoid needing to increase max_buffer_size (possibly with websockets)
        self.set_status(200)
        '''
        self.write(self.application.blockchain)
        '''
        index = 0
        buffer_tracker = 0
        while index < len(self.application.blockchain):
            new_index = index + 4 * 1024
            if new_index > len(self.application.blockchain):
                new_index = len(self.application.blockchain)
            self.write(self.application.blockchain[index:new_index])
            index = new_index
            buffer_tracker += 16 * 1024
            if buffer_tracker >= 50 * 1024 * 1024:
                await self.flush()
                buffer_tracker = 0
        # '''


class ClientHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    def get(self, client_id):  # TODO: Schedule task to deallocate blocks after a certain period of client inactivity
        if client_id not in self.application.clients:
            self.set_status(404, 'Not Found')
        else:
            intervals = self.application.allocate_intervals(client_id)
            if len(intervals) == 0:  # This happens when the serve has allocated all blocks
                self.set_status(204, 'No Content')
            else:
                data = intervals
                self.set_status(200)
                self.write(data)

    def put(self, client_id):  # TODO: Reset scheduled deallocation task to reflect new client activity
        if client_id not in self.application.clients:
            self.set_status(404, 'Not Found')
        elif len(self.application.clients[client_id]) == 0:
            self.set_status(409, 'Conflict')
        else:
            intervals = json.loads(self.request.body)
            all_intervals_valid = True
            for interval in intervals:
                if interval not in self.application.clients[client_id]:
                    self.set_status(409, 'Conflict')
                    all_intervals_valid = False
                    break
            if all_intervals_valid:
                for interval in intervals:
                    del self.application.clients[client_id][interval]
                self.set_status(200)
                self.write('Client resource updated.')

    def delete(self, client_id):  # TODO: Destroy scheduled deallocation task
        if client_id not in self.application.clients:
            self.set_status(404, 'Not Found')
        else:
            if len(self.application.clients[client_id]) > 0:
                self.application.deallocate_intervals(client_id)
            del self.application.clients[client_id]

            if not self.application.server_is_running and len(self.application.clients) == 0:
                tornado.ioloop.IOLoop.current().stop()

            self.set_status(200)
            self.write('Client resource deleted.')


class ClientsHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ('POST')

    def post(self):
        request_body = json.loads(self.request.body)
        client_id = request_body['client_id']

        if client_id in self.application.clients:
            self.set_status(403, 'Already Exists')
        else:
            self.application.clients[client_id] = {}
            self.set_status(201)
            self.write('Created new profile for client with ID ' + client_id)


class HelpHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ('GET')

    def get(self):
        self.set_status(200)
        self.write(api_help_message)


class ServerHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    def get(self):
        # TODO: Show values, not just counts, for variables of interest
        incomplete_intervals = len(self.application.incomplete_intervals)
        remaining_names = len(self.application.remaining_names)
        client_profiles = len(self.application.clients)  # Number of Client Profiles
        result_resources = len(self.application.interval_results)  # Number of Result Resources
        server_is_running = self.application.server_is_running  # Operational State of the Server
        server_info = {'incomplete_intervals': incomplete_intervals, 'remaining_names': remaining_names,
                       'client_profiles': client_profiles, 'result_resources': result_resources,
                       'server_is_running': server_is_running}

        self.set_status(200)
        self.write(server_info)

    def put(self):
        request_body = json.loads(self.request.body)
        put_server_is_running = request_body['server_is_running']

        if self.application.server_is_running and not put_server_is_running:
            self.application.server_is_running = False
            self.set_status(202)
            if len(self.application.clients) == 0:
                tornado.ioloop.IOLoop.current().stop()
                self.write("Stopping server.")
            else:
                self.write('Server will be stopped when all clients have disconnected.')
        elif not self.application.server_is_running and put_server_is_running:
            if len(self.application.clients) > 0:
                self.application.server_is_running = True
                self.set_status(200)
                self.write('Server will no longer be stopped if all clients disconnect.')
            else:
                self.set_status(409, 'Conflict')
        elif self.application.server_is_running and put_server_is_running:
            self.set_status(200)
            self.write('Server was already set to continue running without clients.')
        elif not self.application.server_is_running and not put_server_is_running:
            self.set_status(200)
            self.write('Server was already set to be stopped if all clients disconnected.')

    def delete(self):
        if self.application.server_is_running:
            self.application.server_is_running = False
            tornado.ioloop.IOLoop.current().stop()
            self.set_status(202)
            self.write("Stopping server.")
        else:
            self.set_status(404, "Server was already stopped.")


def main():
    hsd_directory_path = '/home/dannya951/.hsd'
    analyze = False

    application = ServerApplication(hsd_directory_path)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)

    print('Starting server.')
    tornado.ioloop.IOLoop.current().start()
    print("Server stopped.")

    if analyze:
        perform_analysis(hsd_directory_path)


if __name__ == "__main__":
    start_time = time.time()
    main()
    elapsed_seconds = int((time.time() - start_time) + 0.5)
    remainder_seconds = elapsed_seconds % 60
    elapsed_minutes = int((elapsed_seconds - remainder_seconds) / 60)
    print('Elapsed Time: ' + str(elapsed_minutes) + ' minutes and ' + str(remainder_seconds) + ' seconds')
