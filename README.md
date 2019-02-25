# pyzim-tools

## What is pyzim-tools ?

`pyzim-tools` is a small set of tools to introspect and debug a zim file.
(https://wiki.openzim.org/wiki/Main_Page)

It doesn't depends of [libzim](https://github.com/openzim/libzim) and may not
follow the official spec.
Despite I also work for the [openzim](https://github.com/openzim) and
[kiwix](https://github.com/kiwix) projects, `pyzim-tools` is
a personal project and is not affiliated with those projects.

It is intended for personal use and you should probably not use it in
production.

You are welcome to report bug, feature request or pull request but I do not
guaranty any bug fix or integration of your code.

## What is the license ?

This code is GPLv3.0

## How to use it ?


To install pyzim-tools (probably in a virtualenv) :

```bash
pip3 install https://github.com/kymeria/pyzim-tools/zipball/master
```

Then in python :
```python
import pyzim
import mmap
with open('icd10_fr_all_2012-01.zim', 'r+b') as f:
    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        h = pyzim.Header(mm)
        print(h.articleCount) # 290
        urlPtrList = pyzim.UrlPtrList(h.buf[h.urlPtrPos:])
        clusterPtrList = pyzim.ClusterPtrList(h.buf[h.clusterPtrPos :])
        d = pyzim.BaseDirent.new(h.buf[urlPtrList[100]:])
        print(d.url) # 'CIM-10: groupe H10-H13.html'
        print(d.title) # 'CIM-10: groupe H10-H13'
        cluster = pyzim.Cluster(h.buf[clusterPtrList[d.clusterNumber]:])
        print(cluster.get_blob_data(d.blobNumber)) # b'<!DOCTYPE HTML SYSTEM "HTML32.DTD" >\n<html>\n<head>\n<title>CIM-10: groupe...`
```

Also have a look in the tests directory.
