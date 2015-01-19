# fs2json
Create a json file from a folder. Read [fs2json.py](fs2json.py). Will output something like (formatted for readability):

```json
{
   "fsroot" : [
      {
         "type" : 1,
         "gid" : 1000,
         "name" : "bar",
         "uid" : 1000,
         "mtime" : 1421709361,
         "mode" : 33188,
         "size" : 4
      },
      {
         "gid" : 1000,
         "name" : "bof",
         "uid" : 1000,
         "mode" : 41471,
         "size" : 12,
         "type" : 2,
         "target" : "test/foo/bof",
         "mtime" : 1421709395
      },
      {
         "mtime" : 1421709371,
         "type" : 0,
         "children" : [
            {
               "gid" : 1000,
               "name" : "bof",
               "type" : 1,
               "size" : 4,
               "mode" : 33188,
               "mtime" : 1421709371,
               "uid" : 1000
            },
            {
               "gid" : 1000,
               "name" : "bar",
               "uid" : 1000,
               "children" : [],
               "mode" : 16877,
               "size" : 4096,
               "type" : 0,
               "mtime" : 1421709348
            }
         ],
         "uid" : 1000,
         "mode" : 16877,
         "size" : 4096,
         "gid" : 1000,
         "name" : "foo"
      }
   ]
}
```
