# fs2json
Create a json file from a folder. Read [fs2json.py](fs2json.py). Will output something like (formatted for readability):

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
