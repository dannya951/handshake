import requests


def get_from_curl(address):
    r = requests.get(address, allow_redirects=True)
    r.raise_for_status()
    data = r.text
    return data


def get_from_curl_with_data(address, data):
    r = requests.post(address, data, allow_redirects=True)
    r.raise_for_status()
    data = r.text
    return data


def read_lines_from_file(filename):
    data_lines = []
    with open(filename, 'r') as f:
        for line in f:
            stripped_line = line.rstrip()
            data_lines.append(stripped_line)
    data = '\n'.join(data_lines)
    return data


def read_from_file(filename):
    data = None
    with open(filename, 'r') as f:
        data = f.read()
    return data


def write_to_file(filename, data):
    with open(filename, 'w') as f:
        f.write(data)
    return


def append_to_file(filename, data):
    with open(filename, 'a') as f:
        f.write(data)
    return


def clear_file(filename):
    write_to_file(filename, '')
    return
