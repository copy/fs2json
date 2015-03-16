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

    args = argparse.ArgumentParser(description="Create filesystem JSON")
    args.add_argument("--exclude", 
                      action="append",
                      help="Paths to exclude")
    args.add_argument("path", metavar="path", type=str, 
                      help="Base path to include in JSON")

    args = args.parse_args()

    path = args.path
    exclude = args.exclude or []
    exclude = set(exclude)

    if path[-1] != "/":
        path += "/"

    def onerror(oserror):
        logger.warning(oserror)

    rootdepth = path.count("/")
    files = os.walk(path, onerror=onerror)
    prevpath = []

    mainroot = []
    result = {
        "fsroot": mainroot,
        "version": VERSION,
        "size": 0,
    }
    rootstack = [mainroot]

    def make_node(st, name):
        obj = [None] * 7

        obj[IDX_NAME] = name
        obj[IDX_SIZE] = st.st_size
        obj[IDX_MTIME] = int(st.st_mtime)
        obj[IDX_MODE] = int(st.st_mode)

        obj[IDX_UID] = st.st_uid
        obj[IDX_GID] = st.st_gid

        result["size"] += st.st_size

        # Missing:
        #     int(st.st_atime),
        #     int(st.st_ctime),

        return obj

    logger.info("Creating file tree ...")

    for f in files:
        dirpath, dirnames, filenames = f
        pathparts = dirpath.split("/")
        pathparts = pathparts[rootdepth:]
        fullpath = "/%s/" % "/".join(pathparts)

        if fullpath in exclude:
            dirnames[:] = []
            continue

        depth = 0
        for this, prev in zip(pathparts, prevpath):
            if this != prev:
                break
            depth += 1

        for name in prevpath[depth:]:
            rootstack.pop()

        oldroot = rootstack[-1]

        assert len(pathparts[depth:]) == 1
        openname = pathparts[-1]

        if openname == "":
            root = mainroot
        else:
            root = []
            st = os.stat(dirpath)
            rootobj = make_node(st, openname)
            rootobj[IDX_TARGET] = root
            oldroot.append(rootobj)

        rootstack.append(root)

        for filename in itertools.chain(filenames, dirnames):
            absname = os.path.join(dirpath, filename)

            st = os.lstat(absname)
            isdir = stat.S_ISDIR(st.st_mode)
            islink = stat.S_ISLNK(st.st_mode)

            if isdir and not islink:
                continue

            obj = make_node(st, filename) 

            if islink:
                target = os.readlink(absname)
                obj[IDX_TARGET] = target

            while obj[-1] is None:
                obj.pop()

            root.append(obj)

        prevpath = pathparts

    logger.info("Creating json ...")

    json.dump(result, sys.stdout, check_circular=False, separators=(',', ':'))

if __name__ == "__main__":
    main()
