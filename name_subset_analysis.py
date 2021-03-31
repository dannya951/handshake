import name_analysis as na


def perform_name_subset_analysis(name_dicts, block_headers, results_dir_name='names_subsets'):
    report_list = [perform_all_subset_analysis(name_dicts, block_headers),
                   perform_namebase_subset_analysis(name_dicts, block_headers),
                   perform_non_namebase_subset_analysis(name_dicts, block_headers)]
    report_list.extend(perform_name_group_subset_analysis(name_dicts, block_headers))
    print('\n\n')
    for report in report_list:
        print('Report for ' + report[1] + ' names:')
        print(report[0])
        print('\n**********\n')


def perform_all_subset_analysis(name_dicts, block_headers, results_dir_name='names_subsets'):
    subset_label = 'All'

    print('Beginning Subset Analysis for "' + subset_label + '" Names:')

    data_points_dict = na.perform_name_analysis(name_dicts, block_headers)
    print('Finished Subset Analysis for "' + subset_label + '" Names.')

    print('Generating Subset Report for "' + subset_label + '" Names:')
    report = na.generate_name_report(data_points_dict, name_dicts, subset_label)
    print('Generated Subset Report for "' + subset_label + '" Names.\n')

    return report, subset_label


def perform_name_group_subset_analysis(name_dicts, block_headers, results_dir_name='names_subsets'):
    name_groups = get_name_groups(name_dicts)
    report_list = []
    for group_key in name_groups:
        subset_label = group_key
        subset_of_names = name_groups[subset_label]
        print('Beginning Subset Analysis for "' + subset_label + '" Names:')
        placeholder_dict = {}
        for name in name_dicts:
            if name not in subset_of_names:
                placeholder_dict[name] = name_dicts[name]
        for name in placeholder_dict:
            del name_dicts[name]

        data_points_dict = na.perform_name_analysis(name_dicts, subset_label)
        print('Finished Subset Analysis for "' + subset_label + '" Names.')

        # subset namebase.io report
        subset_namebase_report = perform_namebase_subset_analysis(name_dicts, block_headers)
        print('Report for ' + subset_label + ' ' + subset_namebase_report[1] + ' names:')
        print(subset_namebase_report[0])
        print('**********')

        # subset non-namebase.io report
        subset_non_namebase_report = perform_non_namebase_subset_analysis(name_dicts, block_headers)
        print('Report for ' + subset_label + ' ' + subset_non_namebase_report[1] + ' names:')
        print(subset_non_namebase_report[0])
        print('**********')

        print('Generating Subset Report for "' + subset_label + '" Names:')
        report = na.generate_name_report(data_points_dict, name_dicts, subset_label)

        for name in placeholder_dict:
            name_dicts[name] = placeholder_dict[name]
        print('Generated Subset Report for "' + subset_label + '" Names.\n')

        report_list.append((report, subset_label))

    return report_list
        
        
def perform_non_namebase_subset_analysis(name_dicts, block_headers, results_dir_name='names_subsets'):
    subset_label = 'Non-Namebase.io'

    print('Beginning Subset Analysis for "' + subset_label + '" Names:')
    non_namebase_names_list = get_non_namebase_subset(name_dicts)

    placeholder_dict = {}
    for name in name_dicts:
        if name not in non_namebase_names_list:
            placeholder_dict[name] = name_dicts[name]
    for name in placeholder_dict:
        del name_dicts[name]

    data_points_dict = na.perform_name_analysis(name_dicts, non_namebase_names_list)
    print('Finished Subset Analysis for "' + subset_label + '" Names.')

    print('Generating Subset Report for "' + subset_label + '" Names:')

    report = na.generate_name_report(data_points_dict, name_dicts, subset_label)

    for name in placeholder_dict:
        name_dicts[name] = placeholder_dict[name]
    print('Generated Subset Report for "' + subset_label + '" Names.\n')

    return report, subset_label


def perform_namebase_subset_analysis(name_dicts, block_headers, results_dir_name='names_subsets'):
    subset_label = 'Namebase.io'

    print('Beginning Subset Analysis for "' + subset_label + '" Names:')
    namebase_names_list = get_namebase_subset(name_dicts)

    placeholder_dict = {}
    for name in name_dicts:
        if name not in namebase_names_list:
            placeholder_dict[name] = name_dicts[name]
    for name in placeholder_dict:
        del name_dicts[name]

    data_points_dict = na.perform_name_analysis(name_dicts, namebase_names_list)
    print('Finished Subset Analysis for "' + subset_label + '" Names.')

    print('Generating Subset Report for "' + subset_label + '" Names:')
    report = na.generate_name_report(data_points_dict, name_dicts, subset_label)

    for name in placeholder_dict:
        name_dicts[name] = placeholder_dict[name]
    print('Generated Subset Report for "' + subset_label + '" Names.\n')

    return report, subset_label


def get_name_groups(name_dicts):
    distinct_name_groups = {'one-domain-and-one-bid-testing': [], 'one-domain-and-one-bid-test': [],
                            'one-domain-one-bid-test': [], 'three-hundred-domains-and-one-bid-testing': [],
                            'three-hundred-domains-ten-bids': [], 'test': [], 'synack': [], 'unique': []}

    for name in name_dicts:
        if name.find('one-domain-and-one-bid-testing') == 0:
            distinct_name_groups['one-domain-and-one-bid-testing'].append(name)
        elif name.find('one-domain-and-one-bid-test') == 0:
            distinct_name_groups['one-domain-and-one-bid-test'].append(name)
        elif name.find('one-domain-one-bid-test') == 0:
            distinct_name_groups['one-domain-one-bid-test'].append(name)
        elif name.find('three-hundred-domains-and-one-bid-testing') == 0:
            distinct_name_groups['three-hundred-domains-and-one-bid-testing'].append(name)
        elif name.find('three-hundred-domains-ten-bids') == 0:
            distinct_name_groups['three-hundred-domains-ten-bids'].append(name)
        elif name.find('test') == 0 and len(name) <= 6:
            distinct_name_groups['test'].append(name)
        elif name.find('synack') == 0 and '-' in name:
            distinct_name_groups['synack'].append(name)
        else:
            distinct_name_groups['unique'].append(name)
    return distinct_name_groups


def get_non_namebase_subset(name_dicts):
    namebase_names_list = []
    for name in name_dicts:
        name_dict = name_dicts[name]
        if not is_from_namebase(name_dict):
            namebase_names_list.append(name)
    return namebase_names_list


def get_namebase_subset(name_dicts):
    namebase_names_list = []
    for name in name_dicts:
        name_dict = name_dicts[name]
        if is_from_namebase(name_dict):
            namebase_names_list.append(name)
    return namebase_names_list


def is_from_namebase(name_dict):
    from_namebase = False
    for resource_block in name_dict['name_resources']:  # sorted(list(name_dicts.keys())):
        name_resource_dict = name_dict['name_resources'][resource_block]
        if name_resource_dict and 'text' in name_resource_dict:
            name_resource_text = name_resource_dict['text']
            if name_resource_text and 'Registered with namebase.io/' in name_resource_text:
                from_namebase = True
                break
        if name_resource_dict and 'hosts' in name_resource_dict:
            name_resource_hosts = name_resource_dict['hosts']
            if name_resource_hosts and '52.71.101.8' in name_resource_hosts:
                from_namebase = True
                break
    return from_namebase


def get_name_from_dicts(name_dicts):
    return name_dicts[str([int(dict_key) for dict_key in list(name_dicts.keys())][0])]['name_record']['name']

