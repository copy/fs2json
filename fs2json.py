
import json
import os
import stat
import sys

# include trailing slash
PATH = "/mnt/"

EXCLUDE = set([
    "/boot/",
    #"/dev/",
    "/lost+found/",
    #"/proc/",
    #"/run/",
    #"/sys/",
    #"/tmp/",
])

TYPE_DIR = 0
TYPE_FILE = 1
TYPE_LINK = 2

DEFAULT_MODE = 0o644

def onerror(oserror):
    raise oserror

rootdepth = PATH.count("/")
files = os.walk(PATH, onerror=onerror)
prevpath = []

mainroot = []
result = {
    "fsroot": mainroot,
}
rootstack = [mainroot]

def make_node(st, name):
    obj = {
        "name": name,
        "size": st.st_size,
        #"atime": int(st.st_atime),
        #"ctime": int(st.st_ctime),
        "mtime": int(st.st_mtime),
    }

    if st.st_mode != DEFAULT_MODE:
        obj["mode"] = st.st_mode

    if st.st_gid:
        obj["gid"] = st.st_gid
    if st.st_uid:
        obj["uid"] = st.st_uid

    return obj


for f in files:
    dirpath, dirnames, filenames = f
    pathparts = dirpath.split("/")
    pathparts = pathparts[rootdepth:]
    fullpath = "/%s/" % "/".join(pathparts)

    if fullpath in EXCLUDE:
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
        rootobj["type"] = TYPE_DIR
        rootobj["children"] = root
        oldroot.append(rootobj)

    rootstack.append(root)

    for filename in filenames + dirnames:
        absname = os.path.join(dirpath, filename)
        islink = os.path.islink(absname)
        isdir = os.path.isdir(absname)

        if isdir and not islink:
            continue

        st = os.lstat(absname)
        obj = make_node(st, filename) 

        if islink:
            target = os.readlink(absname)
            obj["type"] = TYPE_LINK
            obj["target"] = target
        else:
            obj["type"] = TYPE_FILE

        root.append(obj)

    prevpath = pathparts


json.dump(result, sys.stdout, check_circular=False, separators=(',', ':'))

