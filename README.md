# fs2json

```
usage: fs2json.py [-h] [--exclude path] [--out [out]] path

Create filesystem JSON. Example:
    ./fs2json.py --exclude /boot/ --out fs.json /mnt/

positional arguments:
  path            Base path to include in JSON

optional arguments:
  -h, --help      show this help message and exit
  --exclude path  Path to exclude (relative to base path). Can be specified multiple times.
  --out [out]     File to write to (defaults to stdout)
```


This script will output something like (formatted for readability):

```json
{
    "fsroot": [
        ["bar", 4, 1421709361, 33188, 1000, 1000],
        ["bof", 12, 1421709395, 41471, 1000, 1000, "test/foo/bof"],
        ["foo", 4096, 1421709371, 16877, 1000, 1000, [
            ["bof", 4, 1421709371, 33188, 1000, 1000],
            ["bar", 4096, 1421709348, 16877, 1000, 1000, []]
        ]]
    ],
    "size": 8212,
    "version": 2
}
```

The current format is `[name, mode, mtime, size, uid, gid, target]`
