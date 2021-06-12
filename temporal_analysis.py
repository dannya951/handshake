import IOUtility as Iou
import json
import time
from pathlib import Path
import analyze_names as an
import numpy as np
import matplotlib.pyplot as plt


def perform_temporal_analysis(name_dicts, block_headers, results_dir_name='blocks'):
    print('Beginning Temporal Analysis:')

    analyze_blockchain(name_dicts, block_headers)

    # Temporarily keeping for reference, used with previous exhaustive method
    '''
    blocks_directory = Path(data_directory_prefix_dict['blocks_directory_prefix'])
    file_path_strings = []
    for block_file in blocks_directory.iterdir():
        file_path_strings.append(str(block_file))
    print('Total number of block files: ' + str(len(file_path_strings)))
    '''
    print('Finished Temporal Analysis.' + '\n\n')


def analyze_blockchain(name_dicts, block_headers):
    result_string = ''
    all_ownership_periods = []
    all_activity_periods = []

    all_activity_count = 0
    first_activity_count = 0
    second_activity_count = 0
    third_activity_count = 0
    fourth_activity_count = 0
    fifth_activity_count = 0
    sixth_activity_count = 0
    seventh_activity_count = 0
    eighth_activity_count = 0

    first_ownerhsip_count = 0
    second_ownership_count = 0
    third_owernship_count = 0
    all_ownership_count = 0

    for name in name_dicts:
        name_record_ownership_periods = []
        ownership_interval = [-1, -1]
        for interval in name_dicts[name]['intervals']:
            if interval[0] == 0:
                if ownership_interval[0] == -1:
                    ownership_interval[0] = interval[1]
            elif interval[0] == 6:
                if ownership_interval[0] > -1:
                    ownership_interval[1] = interval[2]
            elif interval[0] == -1:
                if ownership_interval[1] > 0:
                    name_record_ownership_periods.append((ownership_interval[0], ownership_interval[1]))
                ownership_interval = [-1, -1]
        if ownership_interval[0] > -1 and ownership_interval[1] > -1:
            name_record_ownership_periods.append((ownership_interval[0], ownership_interval[1]))

        all_ownership_count += len(name_record_ownership_periods)
        if len(name_record_ownership_periods) > 0:
            first_ownerhsip_count += 1
            if len(name_record_ownership_periods) > 1:
                second_ownership_count += len(name_record_ownership_periods) - 1
                if len(name_record_ownership_periods) > 2:
                    third_owernship_count += len(name_record_ownership_periods) - 2

        all_ownership_periods.append((name_dicts, name_record_ownership_periods))

        name_record_activity_periods = []
        activity_interval = [-1, -1]
        for interval in name_dicts[name]['intervals']:
            if interval[0] == 0:
                if activity_interval[0] == -1:
                    activity_interval[0] = interval[1]
            elif interval[0] == -1:
                if activity_interval[0] > -1:
                    name_record_activity_periods.append((activity_interval[0], interval[2]))
                activity_interval = [-1, -1]
        if activity_interval[0] > -1:
            name_record_activity_periods.append((activity_interval[0], 40211))

        all_activity_count += len(name_record_activity_periods)
        if len(name_record_activity_periods) > 0:
            first_activity_count += 1
            if len(name_record_activity_periods) > 1:
                second_activity_count += len(name_record_activity_periods) - 1
                if len(name_record_activity_periods) > 2:
                    third_activity_count += len(name_record_activity_periods) - 2
                    if len(name_record_activity_periods) > 3:
                        fourth_activity_count += len(name_record_activity_periods) - 3
                        if len(name_record_activity_periods) > 4:
                            # TODO: Include debug parameter for this information
                            '''
                            print('High Activity Name: ' + name)
                            print('Total Number of Activity Intervals: ' + str(len(name_record_activity_periods)))
                            print('Activity Intervals:\n' + '\n'.join(
                                [str(inter) for inter in name_dicts[name]['intervals']]))
                            print()
                            '''
                            fifth_activity_count += len(name_record_activity_periods) - 4
                            if len(name_record_activity_periods) > 5:
                                sixth_activity_count += len(name_record_activity_periods) - 5
                                if len(name_record_activity_periods) > 6:
                                    seventh_activity_count += len(name_record_activity_periods) - 6
                                    if len(name_record_activity_periods) > 7:
                                        eighth_activity_count += len(name_record_activity_periods)

        all_activity_periods.append((name_dicts, name_record_activity_periods))

    print('Total Number of Names: ' + str(len(name_dicts)))
    print()

    print('Total Number of Activity Intervals: ' + str(all_activity_count))
    print('Number of First Activity Intervals: ' + str(first_activity_count))
    print('Number of Second Activity Intervals: ' + str(second_activity_count))
    print('Number of Third Activity Intervals: ' + str(third_activity_count))
    print('Number of Fourth Activity Intervals: ' + str(fourth_activity_count))
    print('Number of Fifth Activity Intervals: ' + str(fifth_activity_count))
    print('Number of Sixth Activity Intervals: ' + str(sixth_activity_count))
    print('Number of Seventh Activity Intervals: ' + str(seventh_activity_count))
    print('Number of Eight Activity Intervals: ' + str(eighth_activity_count))
    print()

    print('Total Number of Ownership Intervals: ' + str(all_ownership_count))
    print('Number of First Ownership Intervals: ' + str(first_ownerhsip_count))
    print('Number of Second Ownership Intervals: ' + str(second_ownership_count))
    print('Number of Third Ownership Intervals: ' + str(third_owernship_count))
    print()

    # Activity Analysis
    plot_all_activity_events(all_activity_periods)
    # When are names opened for the first time?
    plot_first_activity_events(all_activity_periods)

    plot_all_activity_length_frequency(all_activity_periods)
    plot_first_activity_length_frequency(all_activity_periods)

    plot_activity_length_cdf(all_activity_periods)

    # Ownership Analysis
    # When did people start ownership intervals?
    plot_all_owernship_events(all_ownership_periods)
    plot_first_ownership_events(all_ownership_periods)

    # How long do people keep their names for?
    plot_all_ownership_length_frequency(all_ownership_periods)
    # How long do people keep their names for the first time?
    plot_first_ownership_length_frequency(all_ownership_periods)

    # CDF of portion of total ownership time by ownership event
    plot_ownership_length_cdf(all_ownership_periods)

    # Transaction Analysis
    # Average block tx count by time cluster
    plot_cluster_average_block_tx_count_over_time(40210, block_headers)
    # Average block tx count by time cluster, pruned to eliminate outliers
    plot_pruned_average_block_tx_count_over_time(40210, block_headers)

    # Block Analysis
    # Average block delay time by time cluster
    plot_cluster_average_block_delays_over_time(40210, block_headers)
    # Average block delay time by time cluster, pruned to eliminate outliers
    plot_pruned_cluster_average_block_delays_over_time(40210, block_headers)

    # TODO: Normal Distribution of block delays, Normal Distribution of transactions per block
    # TODO: Track block size over time (as opposed to just tx count), track difficulty over time
    # TODO: Attempt to track coin ownership
    # TODO: Search for auctions with accounts not funded by the same faucet

    return result_string


def evaluate_name_ownership_periods(name_record, blockchain_info, blockchain):
    blocks_per_day = 144  # blocks
    bid_window = 1 * blocks_per_day  # blocks
    reveal_period = 2 * blocks_per_day  # blocks
    renewal_window = 30 * blocks_per_day  # blocks
    current_block = blockchain_info['chain']['height']

    period_start = None
    period_end = None
    period_tuple_list = []

    name_state = 'available'
    history = name_record['History']
    for event in history:
        action = event['Action']
        # these actions never change name state
        if action == 'Bid' or action == 'Redeem':
            continue
        # handle event actions according to name state
        if name_state == 'available':
            # Only ever the case at the beginning of the history
            # Even if ownership expires later, the state transition would lead directly into bidding
            if action == 'Opened':
                name_state = 'bidding'
        elif name_state == 'bidding':
            if action == 'Opened':
                # The fact that it was ever opened implies there was a bid
                # The fact that there was a bid implies a Reveal period was required
                continue
            elif action == 'Reveal':
                # implies period_start + bid_window < time < period_start + bid_window + reveal_period
                name_state = 'revealing'
        elif name_state == 'revealing':
            if action == 'Opened':
                # Implies period_start+bid_window+reveal_period<time
                name_state = 'bidding'
            elif action == 'Register':
                name_state = 'closed'
                period_start = int(event['Block Height'])
                period_end = int(event['Block Height']) + renewal_window
                if period_end > current_block:
                    period_end = current_block
            elif action == 'Reveal':
                continue
        elif name_state == 'closed':
            if action == 'Opened':
                period_tuple_list.append((period_start, period_end))
                period_start = None
                period_end = None
                name_state = 'bidding'
            elif action == 'Update' or action == 'Renew':
                period_end = int(event['Block Height']) + renewal_window
                if period_end > current_block:
                    period_end = current_block
    if period_start is not None and period_end is not None:
        period_tuple_list.append((period_start, period_end))
    return period_tuple_list


def evaluate_name_activity_periods(name_record, blockchain_info, blockchain):
    blocks_per_day = 144  # blocks
    bid_window = 1 * blocks_per_day  # blocks
    reveal_period = 2 * blocks_per_day  # blocks
    renewal_window = 30 * blocks_per_day  # blocks
    current_block = blockchain_info['chain']['height']

    period_start = None
    period_end = None
    period_tuple_list = []

    name_state = 'available'
    history = name_record['History']
    for event in history:
        action = event['Action']
        # these actions never change name state
        if action == 'Bid' or action == 'Redeem':
            continue
        # handle event actions according to name state
        if name_state == 'available':
            # Only ever the case at the beginning of the history
            # Even if ownership expires later, the state transition
            # would lead directly into bidding
            if action == 'Opened':
                period_start = int(event['Block Height'])
                period_end = period_start + bid_window + reveal_period
                if period_end > current_block:
                    period_end = current_block
                name_state = 'bidding'
        elif name_state == 'bidding':
            if action == 'Opened':
                # The fact that it was ever opened implies there was a bid
                # The fact that there was a bid implies a Reveal period was required
                period_tuple_list.append((period_start, period_end))
                period_start = int(event['Block Height'])
                period_end = period_start + bid_window + reveal_period
                if period_end > current_block:
                    period_end = current_block
            elif action == 'Reveal':
                # implies period_start+bid_window<time<period_start+bid_window+reveal_period
                name_state = 'revealing'
        elif name_state == 'revealing':
            if action == 'Opened':
                # Implies period_start+bid_window+reveal_period<time
                period_tuple_list.append((period_start, period_end))
                period_start = int(event['Block Height'])
                period_end = period_start + bid_window + reveal_period
                if period_end > current_block:
                    period_end = current_block
                name_state = 'bidding'
            elif action == 'Register':
                name_state = 'closed'
                period_end = int(event['Block Height']) + renewal_window
                if period_end > current_block:
                    period_end = current_block
            elif action == 'Reveal':
                continue
        elif name_state == 'closed':
            if action == 'Opened':
                period_tuple_list.append((period_start, period_end))
                period_start = int(event['Block Height'])
                period_end = period_start + bid_window + reveal_period
                if period_end > current_block:
                    period_end = current_block
                name_state = 'bidding'
            elif action == 'Update' or action == 'Renew':
                period_end = int(event['Block Height']) + renewal_window
                if period_end > current_block:
                    period_end = current_block
    period_tuple_list.append((period_start, period_end))
    return period_tuple_list


def plot_all_ownership_length_frequency(all_ownership_periods):
    combined_list = []
    for l_tuple in all_ownership_periods:
        combined_list.extend(l_tuple[1])
    ownership_lengths = []
    for l_tuple in combined_list:
        ownership_lengths.append(l_tuple[1] - l_tuple[0])

    fig, axs = plt.subplots(1, 1)
    axs.hist(ownership_lengths, bins=50)
    axs.set_xlabel('Duration of Ownership in Blocks')
    axs.set_ylabel('Ownership Duration Frequency')
    fig.suptitle('Distribution of All Domain Name Ownership Events by Duration in Blocks')
    plt.savefig('data/results/all_ownership_duration_hist.png')
    plt.close()


def plot_first_ownership_length_frequency(all_ownership_periods):
    combined_first_list = []
    for l_tuple in all_ownership_periods:
        if len(l_tuple[1]) > 0:
            combined_first_list.append(l_tuple[1][0])
    first_ownership_lengths = []
    for l_tuple in combined_first_list:
        first_ownership_lengths.append(l_tuple[1] - l_tuple[0])

    fig, axs = plt.subplots(1, 1)
    axs.hist(first_ownership_lengths, bins=50)
    axs.set_xlabel('Duration of Ownership in Blocks')
    axs.set_ylabel('Ownership Duration Frequency')
    fig.suptitle('Distribution of First Domain Name Ownership Events by Duration in Blocks')
    plt.savefig('data/results/first_ownership_duration_hist.png')
    plt.close()


def plot_first_ownership_events(all_ownership_periods):
    combined_list = []
    for l_tuple in all_ownership_periods:
        if len(l_tuple[1]) > 0:
            combined_list.append(l_tuple[1][0])
    ownership_start_events = []
    for l_tuple in combined_list:
        ownership_start_events.append(l_tuple[0])

    fig, axs = plt.subplots(1, 1)

    axs.hist(ownership_start_events, bins=50)
    axs.set_xlabel('Block Height of Opening Event')
    axs.set_ylabel('Number of Openings at Height')
    fig.suptitle('Distribution of First Domain Name Ownership Events by Block Height')
    plt.savefig('data/results/first_ownership_events_hist.png')
    plt.close()


def plot_all_owernship_events(all_ownership_periods):
    combined_list = []
    for l_tuple in all_ownership_periods:
        combined_list.extend(l_tuple[1])
    ownership_start_events = []
    for l_tuple in combined_list:
        ownership_start_events.append(l_tuple[0])

    fig, axs = plt.subplots(1, 1)

    axs.hist(ownership_start_events, bins=50)
    axs.set_xlabel('Block Height of Opening Event')
    axs.set_ylabel('Number of Openings at Height')
    fig.suptitle('Distribution of All Domain Name Ownership Events by Block Height')
    plt.savefig('data/results/all_ownership_events_hist.png')
    plt.close()


def plot_ownership_length_cdf(all_ownership_periods):
    combined_list = []
    for o_tuple in all_ownership_periods:
        combined_list.extend(o_tuple[1])
    ownership_lengths = []
    for l_tuple in combined_list:
        ownership_lengths.append(l_tuple[1] - l_tuple[0])

    boundary = len(ownership_lengths)
    ownership_lengths.sort(reverse=True)
    lengths_sum = sum(ownership_lengths)
    ownership_time_percentages = [ol / lengths_sum for ol in ownership_lengths]
    time_cumsum = []
    for index in range(boundary):
        partial_sum = sum(ownership_time_percentages[0:index + 1])
        time_cumsum.append(partial_sum)

    plt.plot(range(boundary), time_cumsum)
    plt.title('CDF of Total Ownership Time Summed Across Ownership Events')
    plt.xlabel('Ownership Events')
    plt.ylabel('Cumulative Percentage')
    plt.savefig('data/results/ownership_duration_cdf.png')
    # plt.show()
    plt.close()


def plot_all_activity_length_frequency(all_activity_periods):
    all_activity_events = []
    for activity_tuple in all_activity_periods:
        name_activity_events = activity_tuple[1]
        all_activity_events.extend(name_activity_events)

    activity_start_heights = []
    for activity_event in all_activity_events:
        activity_start_heights.append(activity_event[1] - activity_event[0])

    fig, axs = plt.subplots(1, 1)
    axs.hist(activity_start_heights, bins=50)
    axs.set_xlabel('Duration of Activity in Blocks')
    axs.set_ylabel('Activity Duration Frequency')
    fig.suptitle('Distribution of All Domain Name Activity Events by Duration in Blocks')
    plt.savefig('data/results/all_activity_duration_hist.png')
    plt.close()


def plot_first_activity_length_frequency(all_activity_periods):
    first_activity_events = []
    for activity_tuple in all_activity_periods:
        name_activity_events = activity_tuple[1]
        if len(name_activity_events) > 0:
            first_activity_events.append(name_activity_events[0])

    activity_start_heights = []
    for activity_event in first_activity_events:
        activity_start_heights.append(activity_event[1] - activity_event[0])

    fig, axs = plt.subplots(1, 1)
    axs.hist(activity_start_heights, bins=50)
    axs.set_xlabel('Duration of Activity in Blocks')
    axs.set_ylabel('Activity Duration Frequency')
    fig.suptitle('Distribution of First Domain Name Activity Events by Duration in Blocks')
    plt.savefig('data/results/first_activity_duration_hist.png')
    plt.close()


def plot_all_activity_events(all_activity_periods):
    all_activity_events = []
    for activity_tuple in all_activity_periods:
        name_activity_events = activity_tuple[1]
        all_activity_events.extend(name_activity_events)

    activity_start_heights = []
    for activity_event in all_activity_events:
        activity_start_heights.append(activity_event[0])

    fig, axs = plt.subplots(1, 1)
    axs.hist(activity_start_heights, bins=50)
    axs.set_xlabel('Block Height of Opening Event')
    axs.set_ylabel('Number of Openings at Height')
    fig.suptitle('Distribution of All Domain Name Opening Events by Block Height')
    plt.savefig('data/results/all_activity_events_hist.png')
    plt.close()


def plot_first_activity_events(all_activity_periods):
    first_activity_events = []
    for activity_tuple in all_activity_periods:
        name_activity_events = activity_tuple[1]
        if len(name_activity_events) > 0:
            first_activity_events.append(name_activity_events[0])

    activity_start_heights = []
    for activity_event in first_activity_events:
        activity_start_heights.append(activity_event[0])

    fig, axs = plt.subplots(1, 1)
    axs.hist(activity_start_heights, bins=50)
    axs.set_xlabel('Block Height of Opening Event')
    axs.set_ylabel('Number of Openings at Height')
    fig.suptitle('Distribution of First Domain Name Activity Events by Block Height')
    plt.savefig('data/results/first_activity_events_hist.png')
    plt.close()


def plot_activity_length_cdf(all_activity_periods):
    combined_list = []
    for a_tuple in all_activity_periods:
        combined_list.extend(a_tuple[1])
    activity_lengths = []
    for l_tuple in combined_list:
        activity_lengths.append(l_tuple[1] - l_tuple[0])

    boundary = len(activity_lengths)
    activity_lengths.sort(reverse=True)
    lengths_sum = sum(activity_lengths)
    activity_time_percentages = [al / lengths_sum for al in activity_lengths]
    time_cumsum = []
    for index in range(boundary):
        partial_sum = sum(activity_time_percentages[0:index + 1])
        time_cumsum.append(partial_sum)

    plt.plot(range(boundary), time_cumsum)
    plt.title('CDF of Total Activity Time Summed Across Activity Events')
    plt.xlabel('Activity Events')
    plt.ylabel('Cumulative Percentage')
    plt.savefig('data/results/activity_duration_cdf.png')
    # plt.show()
    plt.close()


def plot_cluster_average_block_delays_over_time(blockchain_height, blockchain):
    x_vals = []
    y_vals = []
    y_sum = 0
    for index in range(0, blockchain_height):
        time_0 = blockchain[str(index)]['time']
        time_1 = blockchain[str(index + 1)]['time']
        time_diff = time_1 - time_0
        y_sum += time_diff
        if (index + 1) % 100 == 0:
            x_vals.append(index + 1)
            y_avg = y_sum / 100
            y_vals.append(y_avg)
            y_sum = 0
    plt.scatter(x_vals, y_vals, alpha=0.5)
    plt.title('Average Delays Between Subsequent Blocks by Cluster')
    plt.xlabel('Block Height')
    plt.ylabel('Delay Time (Seconds)')
    plt.hlines(600, 0, blockchain_height)
    plt.savefig('data/results/avg_block_delay_scatter.png')
    # plt.show()
    plt.close()


def plot_pruned_cluster_average_block_delays_over_time(blockchain_height, blockchain):
    x_vals = []
    y_vals = []
    y_sum = 0
    for index in range(0, blockchain_height):
        time_0 = blockchain[str(index)]['time']
        time_1 = blockchain[str(index + 1)]['time']
        time_diff = time_1 - time_0
        y_sum += time_diff
        if (index + 1) % 100 == 0:
            y_avg = y_sum / 100
            y_sum = 0
            if 300 <= y_avg <= 900:
                x_vals.append(index + 1)
                y_vals.append(y_avg)
    plt.scatter(x_vals, y_vals, alpha=0.5)
    plt.title('Average Delays Between Subsequent Blocks by Cluster, Pruned')
    plt.xlabel('Block Height')
    plt.ylabel('Delay Time (Seconds)')
    plt.hlines(600, 0, blockchain_height)
    plt.savefig('data/results/avg_block_delay_pruned_scatter.png')
    # plt.show()
    plt.close()


def plot_cluster_average_block_tx_count_over_time(blockchain_height, blockchain):
    x_vals = []
    y_vals = []
    y_sum = 0
    for index in range(1, blockchain_height + 1):
        tx_count = blockchain[str(index)]['tx_count']
        y_sum += tx_count
        if index % 100 == 0:
            y_avg = y_sum / 100
            y_sum = 0
            x_vals.append(index)
            y_vals.append(y_avg)
    plt.scatter(x_vals, y_vals, alpha=0.5)
    plt.title('Average Transactions per Block by Cluster')
    plt.xlabel('Block Height')
    plt.ylabel('Avg Txs')
    plt.savefig('data/results/avg_block_tx_scatter.png')
    # plt.show()
    plt.close()


def plot_pruned_average_block_tx_count_over_time(blockchain_height, blockchain):
    x_vals = []
    y_vals = []
    y_sum = 0
    for index in range(1, blockchain_height + 1):
        tx_count = blockchain[str(index)]['tx_count']
        y_sum += tx_count
        if index % 100 == 0:
            y_avg = y_sum / 100
            y_sum = 0
            if y_avg < 5:
                x_vals.append(index)
                y_vals.append(y_avg)
    plt.scatter(x_vals, y_vals, alpha=0.5)
    plt.title('Average Transactions per Block by Cluster, Pruned')
    plt.xlabel('Block Height')
    plt.ylabel('Avg Txs')
    plt.savefig('data/results/avg_block_tx_pruned_scatter.png')
    # plt.show()
    plt.close()
