

import pytest
from pyzim import *

sampleZim_content = bytes([
0x5a, 0x49, 0x4d, 0x04, 0x05, 0x00, 0x00, 0x00, 0x19, 0xfd,
0x91, 0x00, 0x73, 0x2b, 0xcf, 0xb6, 0x34, 0x06, 0x55, 0x19,
0xac, 0x2e, 0x03, 0xc4, 0x03, 0x00, 0x00, 0x00, 0x01, 0x00,
0x00, 0x00, 0x66, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x7e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xce, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x50, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
0xff, 0xff, 0x27, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x74, 0x65, 0x78, 0x74, 0x2f, 0x68, 0x74, 0x6d, 0x6c, 0x00,
0x74, 0x65, 0x78, 0x74, 0x2f, 0x70, 0x6c, 0x61, 0x69, 0x6e,
0x00, 0x00, 0x8a, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0xa0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xb8, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x41, 0x75, 0x74, 0x6f, 0x00, 0x00,
0xff, 0xff, 0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x41, 0x75, 0x74, 0x6f, 0x6d, 0x6f, 0x62, 0x69,
0x6c, 0x65, 0x00, 0x00, 0x01, 0x00, 0x00, 0x42, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
0x41, 0x75, 0x74, 0x6f, 0x00, 0x00, 0xd6, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x04, 0xfd, 0x37, 0x7a, 0x58, 0x5a,
0x00, 0x00, 0x01, 0x69, 0x22, 0xde, 0x36, 0x02, 0x00, 0x21,
0x01, 0x10, 0x00, 0x00, 0x00, 0xa8, 0x70, 0x8e, 0x86, 0xe0,
0x00, 0x1c, 0x00, 0x18, 0x5e, 0x00, 0x06, 0x00, 0x34, 0xfb,
0xde, 0x91, 0x72, 0xa3, 0x80, 0x34, 0xfc, 0x31, 0x87, 0x1f,
0xe6, 0xaa, 0x61, 0x04, 0x70, 0x25, 0xb1, 0x84, 0xdc, 0x00,
0x00, 0xe1, 0x66, 0xf9, 0xe7, 0x00, 0x01, 0x30, 0x1d, 0x01,
0xef, 0xc6, 0x9c, 0x90, 0x42, 0x99, 0x0d, 0x01, 0x00, 0x00,
0x00, 0x00, 0x01, 0x59, 0x5a, 0x6c, 0xd7, 0x5d, 0xbe, 0x78,
0x95, 0x3c, 0x79, 0xd9, 0x50, 0x54, 0x03, 0x4b, 0x57, 0x26,
0xc4])


def test_header():
    h = Header(sampleZim_content)
    assert h.clusterCount == 1
    assert h.articleCount == 3


def test_dirent():
    h = Header(sampleZim_content)
    urls = UrlPtrList(h.buf[h.urlPtrPos:])
    d0 = BaseDirent.new(h.buf[urls[0]:])
    assert d0.namespace == b'A'
    assert d0.url == 'Auto'
    assert d0.title == ''
    assert d0.kind == 'article'
    assert d0.clusterNumber == 0
    assert d0.blobNumber == 0
    d1 = BaseDirent.new(h.buf[urls[1]:])
    assert d1.namespace == b'A'
    assert d1.url == 'Automobile'
    assert d1.title == ''
    assert d1.kind == 'redirect'
    assert d1.redirect_index == 0
    d2 = BaseDirent.new(h.buf[urls[2]:])
    assert d2.namespace == b'B'
    assert d2.url == 'Auto'
    assert d2.title == ''
    assert d2.kind == 'article'
    assert d2.clusterNumber == 0
    assert d2.blobNumber == 1


def test_cluster():
    h = Header(sampleZim_content)
    urls = UrlPtrList(h.buf[h.urlPtrPos:])
    clusterOffsets = ClusterPtrList(h.buf[h.clusterPtrPos:])
    d0 = BaseDirent.new(h.buf[urls[0]:])
    cOffset = clusterOffsets[d0.clusterNumber]
    c = Cluster(h.buf[cOffset:])
    assert c.compression == 4
    assert c.extended == 0
    assert c.get_blob_data(d0.blobNumber) == b"<h1>Auto</h1>"

    d2 = BaseDirent.new(h.buf[urls[2]:])
    cOffset = clusterOffsets[d2.clusterNumber]
    c = Cluster(h.buf[cOffset:])
    assert c.compression == 4
    assert c.extended == 0
    assert c.get_blob_data(d2.blobNumber) == b"Auto"

