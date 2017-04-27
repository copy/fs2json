#!/usr/bin/env python

import argparse
import json
import os
import stat
import sys
import itertools
import logging

VERSION = 2

IDX_NAME = 0
IDX_SIZE = 1
IDX_MTIME = 2
IDX_MODE = 3
IDX_UID = 4
IDX_GID = 5

# target for symbolic links
# child nodes for directories
# nothing for files
IDX_TARGET = 6


def main():
    logging.basicConfig(format="%(message)s")
    logger = logging.getLogger("fs2json")
    logger.setLevel(logging.DEBUG)

    args = argparse.ArgumentParser(
        description="Create filesystem JSON. Example:\n"
                    "    ./fs2json.py --exclude /boot/ --out fs.json /mnt/",
        formatter_class=argparse.RawTextHelpFormatter
    )
    args.add_argument("--exclude", 
                      action="append",
                      metavar="path",
                      help="Path to exclude (relative to base path). Can be specified multiple times.")
    args.add_argument("--out", 
                      metavar="out",
                      nargs="?", 
                      type=argparse.FileType("w"),
                      help="File to write to (defaults to stdout)",
                      default=sys.stdout)
    args.add_argument("path", 
                      metavar="path", 
                      help="Base path to include in JSON")

    args = args.parse_args()

    path = os.path.normpath(args.path)
    path += "/"
    exclude = args.exclude or []
    exclude = [os.path.join("/", os.path.normpath(p)) for p in exclude]
    exclude = set(exclude)

    def onerror(os_error):
        logger.warning(os_error)

    root_depth = path.count("/")
    files = os.walk(path, onerror=onerror)
    prev_path = []

    main_root = []
    result = {
        "fsroot": main_root,
        "version": VERSION,
        "size": 0,
    }
    root_stack = [main_root]

    def make_node(st, name):
        node = [None] * 7

        node[IDX_NAME] = name
        node[IDX_SIZE] = st.st_size
        node[IDX_MTIME] = int(st.st_mtime)
        node[IDX_MODE] = int(st.st_mode)

        node[IDX_UID] = st.st_uid
        node[IDX_GID] = st.st_gid

        result["size"] += st.st_size

        # Missing:
        #     int(st.st_atime),
        #     int(st.st_ctime),

        return node

    logger.info("Creating file tree ...")

    for f in files:
        dir_path, dir_names, file_names = f
        path_parts = dir_path.split("/")
        path_parts = path_parts[root_depth:]
        fullpath = os.path.join("/", *path_parts)

        if fullpath in exclude:
            dir_names[:] = []
            continue

        depth = 0
        for this, prev in zip(path_parts, prev_path):
            if this != prev:
                break
            depth += 1

        for _ in prev_path[depth:]:
            root_stack.pop()

        old_root = root_stack[-1]

        assert len(path_parts[depth:]) == 1
        open_name = path_parts[-1]

        if open_name == "":
            root = main_root
        else:
            root = []
            st = os.stat(dir_path)
            root_obj = make_node(st, open_name)
            root_obj[IDX_TARGET] = root
            old_root.append(root_obj)

        root_stack.append(root)

        for filename in itertools.chain(file_names, dir_names):
            abs_name = os.path.join(dir_path, filename)

            st = os.lstat(abs_name)
            isdir = stat.S_ISDIR(st.st_mode)
            islink = stat.S_ISLNK(st.st_mode)

            if isdir and not islink:
                continue

            obj = make_node(st, filename)

            if islink:
                target = os.readlink(abs_name)
                obj[IDX_TARGET] = target

            while obj[-1] is None:
                obj.pop()

            root.append(obj)

        prev_path = path_parts

    logger.info("Creating json ...")

    json.dump(result, args.out, check_circular=False, separators=(',', ':'))

if __name__ == "__main__":
    main()
