import IOUtility as Iou
import json
import pathlib


def generate_name_report(data_points_dict, name_dicts, results_label, debug=False):
    if debug:
        print('Generating Subset Report:')

    report_list = []

    unique_name_resources = data_points_dict['unique_name_resources']
    start_values = data_points_dict['start_values']
    reserved_status = data_points_dict['reserved_status']

    report_list.append(str(len(name_dicts)) + ' names have been opened.')
    names_with_hosts_count = 0
    names_with_canonical_count = 0
    host_ip_counter = {}
    unique_host_ip_list_counter = {}
    unique_canonical_counter = {}
    for name in unique_name_resources:
        name_has_host = False
        name_has_canonical = False
        name_host_ip_set = set()
        host_ip_list_set = set()
        canonical_set = set()
        for name_resource_string in unique_name_resources[name]:
            name_resource = json.loads(name_resource_string)
            if 'hosts' in name_resource:
                name_has_host = True
                for host in name_resource['hosts']:
                    name_host_ip_set.add(host)
                host_ip_list_set.add(str(name_resource['hosts']))
            if 'canonical' in name_resource:
                name_has_canonical = True
                canonical_set.add(str(name_resource['canonical']))
        if name_has_host:
            names_with_hosts_count += 1
        if name_has_canonical:
            names_with_canonical_count += 1
        for name_host_ip in name_host_ip_set:
            if name_host_ip not in host_ip_counter:
                host_ip_counter[name_host_ip] = 0
            host_ip_counter[name_host_ip] += 1
        for host_ip_list in host_ip_list_set:
            if host_ip_list not in unique_host_ip_list_counter:
                unique_host_ip_list_counter[host_ip_list] = 0
            unique_host_ip_list_counter[host_ip_list] += 1
        for canonical in canonical_set:
            if canonical not in unique_canonical_counter:
                unique_canonical_counter[canonical] = 0
            unique_canonical_counter[canonical] += 1

    report_list.append(str(names_with_hosts_count) + ' names have at least one "hosts" record.')
    report_list.append('Unique host IP addresses appeared in resources for the following number of names:\n\t' +
                       '\n\t'.join([host + ': ' + str(host_ip_counter[host]) for host in host_ip_counter]))
    report_list.append('Unique host IP-address lists appeared in resources for the following number of names:\n\t' +
                       '\n\t'.join([host_ip_list + ': ' + str(unique_host_ip_list_counter[host_ip_list]) for
                                    host_ip_list in unique_host_ip_list_counter]))
    report_list.append('Unique canonical records appeared in resources for the following number of names:\n\t' +
                       '\n\t'.join([c + ': ' + str(unique_canonical_counter[c]) for c in unique_canonical_counter]))

    active_at_last_block_count = 0
    inactive_at_last_block_count = 0
    more_than_one_activity_interval_count = 0
    opened_more_than_once_and_active_at_last_block_count = 0

    for name in name_dicts:
        intervals = name_dicts[name]['intervals']
        if intervals[-1][0] != -1:
            active_at_last_block_count += 1
        else:
            inactive_at_last_block_count += 1

        # Verification not currently necessary
        '''
        found_a_negative_one = False
        for interval in intervals:  # [1:]:
            if interval[0] == -1:
                if found_a_negative_one:
                    inactive_at_last_block_count += 1
                    break
                else:
                    found_a_negative_one = True
        '''

        first_open = False
        more_than_one = False
        for interval in intervals:
            if interval[0] == 0:
                if not first_open:
                    first_open = True
                else:
                    more_than_one = True
                    break
        if more_than_one and intervals[-1][0] != -1:
            opened_more_than_once_and_active_at_last_block_count += 1
        if more_than_one:
            more_than_one_activity_interval_count += 1

    report_list.append(str(active_at_last_block_count) + ' names were still active by the last block.')
    report_list.append(str(inactive_at_last_block_count) + ' names were inactive by the last block.')
    report_list.append(str(more_than_one_activity_interval_count) + ' names were opened more than once.')
    report_list.append(str(opened_more_than_once_and_active_at_last_block_count) +
                       ' names were opened more than once and were still active by the last block.')

    opened_within_day_of_availability_count = 0
    for name in start_values:
        name_values = start_values[name]
        start_block = name_values['start_block']
        start_week = name_values['start_week']
        # Format: ((interval_start, block_height), registration_status)

        first_opening = name_dicts[name]['intervals'][1][1]
        if first_opening - start_block <= 144:  # TODO: Hardcoded value, refer back to network values
            opened_within_day_of_availability_count += 1

    report_list.append(str(opened_within_day_of_availability_count) +
                       ' names were opened within one day of when they became available.')

    reserved_name_registered = 0
    claimed_while_reserved_count = 0
    for name in reserved_status:
        name_status = reserved_status[name]
        if name_status:
            reserved_name_registered += 1
            first_opening = name_dicts[name]['intervals'][0][1]
            if name_dicts[name]['intervals'][0][0] == -1:
                first_opening = name_dicts[name]['intervals'][1][1]

            if first_opening < 12960:  # TODO: Hardcoded value, refer back to network values
                claimed_while_reserved_count += 1
                # Currently excluded from report
                '''
                print('\n\n')
                print('###################################################################')
                print('Reserved Name Claimed.')
                print('Name: ' + name)
                print('\n'.join([str(interval) for interval in name_dicts[name]['intervals']]))
                print('###################################################################')
                print('\n\n')
                '''

    report_list.append(str(reserved_name_registered) + ' reserved names were registered.')
    report_list.append(str(claimed_while_reserved_count) +
                       ' reserved names were claimed prior to becoming available for open registration.')

    if debug:
        print('Generated Subset Report.')

    return '\n'.join(report_list)


def perform_name_analysis(all_name_dicts, name_list, debug=False):
    current_path = str(pathlib.Path(__file__).parent.absolute())
    reserved_json_path = current_path + '/reserved/names.json'
    reserved_tld_path = current_path + '/reserved/tld.json'

    reserved_names_json = json.loads(Iou.read_from_file(reserved_json_path))  # uses name hashes as keys
    reserved_tlds_json = json.loads(Iou.read_from_file(reserved_tld_path))  # uses names as keys

    data_points_dict = {'activity_intervals': {}, 'unique_name_resources': {}, 'states_by_block': {},
                        'start_values': {}, 'reserved_status': {}}

    if debug:
        print('Beginning Subset Analysis:')

    counter = 0
    progress_increment = 0.2
    current_progress = 0.0 + progress_increment

    for name in all_name_dicts:
        name_dict = all_name_dicts[name]
        activity_intervals = []
        data_points_dict['unique_name_resources'][name] = get_unique_name_resources(name_dict)

        # states_by_block
        data_points_dict['states_by_block'][name] = get_states_by_block(name_dict)

        # start_values
        data_points_dict['start_values'][name] = get_start_values(name_dict)

        # reserved_status
        data_points_dict['reserved_status'][name] = name_dict['name_hash'] in \
            reserved_names_json or name in reserved_tlds_json

        # Currently excluded from report.
        '''
        if data_points_dict['reserved_status'][name]:
            print('\n\n')
            print('###################################################################')
            print('Reserved Name Claimed.')
            print('Name: ' + name)
            print('Name is TLD: ' + str(name in reserved_tlds_json))
            if name in reserved_tlds_json:
                print('TLD Name Hash Prefix: ' + reserved_tlds_json[name][:16])
            print('Name is Domain: ' + name_dict['name_hash'] in reserved_names_json)
            print('\n'.join([str(interval) for interval in name_dict['intervals']]))
            print('###################################################################')
            print('\n\n')
        '''
    if debug:
        print('Finished Subset Analysis.')

    return data_points_dict


def get_start_values(name_dict):
    min_block_height = name_dict['intervals'][0][1]
    if name_dict['intervals'][0][0] == -1:
        min_block_height = name_dict['intervals'][1][1]

    start_dict = {'start_block': name_dict['name_infos'][str(min_block_height)]['start']['start'],
                  'start_week': name_dict['name_infos'][str(min_block_height)]['start']['week']}
    return start_dict


def get_states_by_block(name_dict):
    state_dict = {}

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
    print('Entering state loop.')
    for interval in name_dict['intervals']:
        for block_height in range(interval[1], interval[2]):
            name_state = interval[0]
            state_name = reverse_states[name_state]
            state_tuple = (state_name, 'ACTIVE')
            if name_state == -1:
                state_tuple = (state_name, 'INACTIVE')
            state_dict[str(block_height)] = state_tuple
    print('Exiting state loop.')
    return state_dict


def get_unique_name_resources(name_dict):
    name_resource_set = set()
    for name_resource_block in name_dict['name_resources']:
        name_resource = name_dict['name_resources'][name_resource_block]
        if name_resource is not None and len(name_resource) > 0:
            name_resource_set.add(json.dumps(name_resource))
    return list(name_resource_set)


def get_activity_intervals(name_dicts):
    max_block_height = max([int(dict_key) for dict_key in list(name_dicts.keys())])
    interval_list = []
    interval_start = None
    registered_during_interval = False
    for block_height in range(0, max_block_height + 1):
        # check if name existed at block height
        if str(block_height) not in name_dicts:
            continue

        # check if name is active
        if name_dicts[str(block_height)]['name_info']['info'] is not None:
            # check if beginning of new interval
            if interval_start is None:
                interval_start = block_height

            # check if name was registered during activity period
            if name_dicts[str(block_height)]['name_info']['info']['state'] == 'CLOSED' and \
                    not registered_during_interval:
                registered_during_interval = True

        # check if name is active and (it's the last block or the the name is not active at the next block)
        if interval_start is not None and \
                (block_height == max_block_height or name_dicts[str(block_height + 1)]['name_info']['info'] is None):
            registration_status = 'UNREGISTERED'
            if registered_during_interval:
                registration_status = registration_status[2:]
            # interval indexes are inclusive
            interval_list.append(((interval_start, block_height), registration_status))

            # reset interval values
            interval_start = None
            registered_during_interval = False

    return interval_list


def is_reserved(data_directory_prefix_dict, name_dicts):
    index_str = str(max([int(dict_key) for dict_key in list(name_dicts.keys())]))
    name = get_name_from_dicts(name_dicts)
    name_hash = name_dicts[index_str]['name_record']['nameHash']
    return is_reserved_name(data_directory_prefix_dict, name_hash) or is_reserved_tld(data_directory_prefix_dict, name)


def is_reserved_name(data_directory_prefix_dict, name_hash):
    reserved_names_json = json.loads(Iou.read_from_file(data_directory_prefix_dict['reserved_names_directory_prefix'] +
                                                        '/' + 'names.json'))  # uses name hashes as keys
    return name_hash in reserved_names_json


def is_reserved_tld(data_directory_prefix_dict, name):
    reserved_tlds_json = json.loads(Iou.read_from_file(data_directory_prefix_dict['reserved_names_directory_prefix'] +
                                                       '/' + 'tld.json'))  # uses names as keys
    return name in reserved_tlds_json


def get_name_from_dicts(name_dicts):
    return name_dicts[str([int(dict_key) for dict_key in list(name_dicts.keys())][0])]['name_record']['name']


def report_progress(counter, progress_increment, current_progress, max_iterations):
    counter += 1
    updated_progress = counter / max_iterations
    if updated_progress > current_progress:
        update_percent_str = str(int(100 * updated_progress))
        update_percent_str = update_percent_str + '%'
        print('Current Progress: ' + update_percent_str)
        current_progress += progress_increment
    return counter, current_progress

# useful_names = ['www', 'acmechallenge', 'coin', 'wig', 'father', 'turbomaze', 'tieshun']
# meeting: two unregistered intervals
# indie: two registered intervals
