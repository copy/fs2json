#!/usr/bin/env python
from argparse import ArgumentParser
from functools import partial
from json import load
from multiprocessing.pool import Pool
from os import makedirs, chown, chmod
from os.path import exists, isfile, join
from subprocess import check_call, CalledProcessError
from time import sleep

WORKERS = 3
SLEEP = 2


def parse_arguments():
    """
    Parse the arguments for json2fs
    :return obj args: The parsed arguments
    """
    parser = ArgumentParser(
        description="Reconstruct a filesystem from a fs2json JSON file: Example: \n"
                    "    ./json2fs.py fs.json https://i.copy.sh/arch/ /var/www/v86/arch"
    )
    parser.add_argument(
        'json_path', type=str, help='The JSON file to convert back into a FS'
    )
    parser.add_argument(
        'origin', type=str, help='URL to get the files from'
    )
    parser.add_argument(
        'new_fs_path', type=str, help='Directory to restore the filesystem to'
    )
    return parser.parse_args()


def parse_json(json_path):
    """
    Parse the json file and return a dict
    :param str json_path: Path to the JSON file to parse
    :return dict parsed_json: Parsed JSON as a dict
    """
    with open(json_path, 'r') as f:
        return load(f)


def assert_version(parsed_json):
    """
    Assert the fs2json file is the right version
    :return dict parsed_json: Parsed JSON as a dict
    :return None | raises AssertionError:
    """
    if parsed_json['version'] != 2:
        raise AssertionError(
            "This script can only reconstruct fs2json v2 files, "
            "this is {}".format(parsed_json['version'])
        )


def prepare_reconstruction(parsed_json, new_fs_path, origin):
    """
    Prepare the file downloads and dir creation
    :param dict parsed_json: Parsed JSON as a dict
    :param str new_fs_path: The path of the new fs
    :param str origin: The URL to get the files from
    :return generator reconstruction_strategy: The work required
    for the reconstruction
    """
    def loop(item, path='/'):
        if len(item) == 7:
            # If there are 7 items in the list, it's a dir
            return map(partial(loop, path=path + item[0] + '/'), item[6])
        else:
            # Otherwise it's a file and we can download it
            return {
                'new_fs_path': new_fs_path,
                'origin': origin,
                'dir': path,
                'path': item[0],
                'mode': item[3],
                'uid': item[4],
                'gid': item[5]
            } if isinstance(item, list) else None

    def flatten(work):
        for item in work:
            if isinstance(item, dict):
                yield item
            else:
                for sub_item in item:
                    if sub_item and isinstance(sub_item, dict):
                        yield sub_item

    return filter(any, flatten(map(partial(loop, path='/'), parsed_json['fsroot'])))


def download_file(item):
    """
    Download a file
    :param dict item: The item to reconstruct
    :return None:
    """
    to_download = join(item['new_fs_path'], item['dir'].lstrip('/'), item['path'].lstrip('/'))
    if isfile(to_download):
        print("Already have {}".format(to_download))
    else:
        download_command = (
            'wget', '-nc',
            '{}{}{}'.format(
                item['origin'].rstrip('/') + '/', item['dir'].lstrip('/'),
                item['path']
            ), '-P', join(item['new_fs_path'], item['dir'].lstrip('/')),
        )

        def download(retry=True):
            try:
                check_call(download_command)
            except CalledProcessError:
                print(
                    "Failed to download {}".format(download_command)
                )
                if retry:
                    print("Retrying once")
                    download(retry=False)
        download()
        sleep(SLEEP)


def set_permissions(item):
    """
    Set the permissions of a file
    :param dict item: The item to reconstruct
    :return None:
    """
    file_to_set_permissions_for = join(item['new_fs_path'], item['dir'].lstrip('/'), item['path'].lstrip('/'))
    if isfile(file_to_set_permissions_for):
        try:
            chown(file_to_set_permissions_for, item['uid'], item['gid'])
            # Only care about the lower 3 bits
            mode = int(item['mode']) & 0o777
            chmod(file_to_set_permissions_for, mode)
        except OSError:
            print("Failed to set permissions on {}".format(file_to_set_permissions_for))


def reconstruct_file(item):
    """
    Reconstruct a file
    :param dict item: The item to reconstruct
    :return None:
    """
    try:
        new_dir = join(item['new_fs_path'], item['dir'])
        if not exists(new_dir):
            makedirs(new_dir)
        download_file(item)
        set_permissions(item)

    except KeyboardInterrupt:
        print("Received keyboard interrupt. Stopping download.")
        raise Exception("Keyboard interrupt")


def perform_reconstruction(reconstruction_strategy):
    """
    Create the dirs and download the files
    :param generator reconstruction_strategy: The work to perform
    :return None:
    """
    pool = Pool(WORKERS)
    try:
        pool.map(reconstruct_file, reconstruction_strategy)
    except KeyboardInterrupt:
        pool.terminate()
    finally:
        pool.close()


def json2fs(json_path, origin, new_fs_path):
    """
    Perform the reconstruction of a fs2json file to a filesystem.

    :param str json_path: The JSON file to convert into a filesystem
    :param str origin: The URL to get the files from
    :param str new_fs_path: The path of the new fs
    :return None:
    """
    parsed_json = parse_json(json_path)
    assert_version(parsed_json)
    reconstruction_strategy = prepare_reconstruction(
        parsed_json, new_fs_path, origin
    )
    perform_reconstruction(reconstruction_strategy)


def main():
    """
    fs2json but the other way around.
    Download a filesystem from a json file.
    :return None:
    """
    args = parse_arguments()
    json2fs(args.json_path, args.origin, args.new_fs_path)


if __name__ == '__main__':
    main()
