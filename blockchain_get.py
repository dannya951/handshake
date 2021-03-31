import pathlib
from tornado import httpclient, ioloop
from os import path, remove


async def write(path_name, chunk):
    with open(path_name, 'ab') as gzt:
        gzt.write(chunk)


async def get(url, path_name):
    client = httpclient.AsyncHTTPClient(force_instance=True, max_buffer_size=314572800)
    try:
        if path.exists(path_name) and path.isfile(path_name):
            remove(path_name)
        iol = ioloop.IOLoop.current()
        print('Starting fetch operation.')
        response = await client.fetch(url, streaming_callback=lambda chunk: iol.spawn_callback(write, path_name, chunk))
        # response = await client.fetch(url, streaming_callback=lambda chunk: write(path_name, chunk))
        print('Finished fetch operation.')
    except Exception as e:
        # print('Error: ' + str(e))
        raise e


def main():
    url = 'http://localhost:8080/blockchain'
    current_path = str(pathlib.Path(__file__).parent.absolute())
    gztar_name = 'blockchain'
    path_name = '/'.join([current_path, '.'.join([gztar_name, 'tar', 'gz'])])
    ioloop.IOLoop.current().run_sync(lambda: get(url, path_name))


if __name__ == '__main__':
    main()