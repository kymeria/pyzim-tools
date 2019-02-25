

import pytest
import pyzim


articleDirent_content = (
bytes([0x02, 0x00]) + #mimetype
bytes([0x00]) + #parameterlen
b"A" + #namespace
bytes([0x00, 0x00, 0x00, 0x00]) + #revision
bytes([0x01, 0x00, 0x00, 0x00]) + #clusterNumber
bytes([0x02, 0x00, 0x00, 0x00]) + #blobNumber
b"A/foo.html" + bytes([0]) +
b"Foo" + bytes([0]) +
b"Some garbage")

def test_articleDirent():
    d = pyzim.BaseDirent.new(articleDirent_content)
    assert d.kind == 'article'
    assert d.mimetype == 0x0002
    assert d.parameter_len == 0
    assert d.namespace == b'A'
    assert d.revision == 0
    assert d.clusterNumber == 1
    assert d.blobNumber == 2
    assert d.url == "A/foo.html"
    assert d.title == "Foo"
    assert d.extra_data == b""


redirectDirent_content = (
bytes([0xff, 0xff]) + #mimetype
bytes([0x00]) + #parameterlen
b"B" + #namespace
bytes([0x00, 0x00, 0x00, 0x00]) + #revision
bytes([0x01, 0x00, 0x00, 0x01]) + #redirection index
b"B/bar.html" + bytes([0]) +
b"Bar" + bytes([0]) +
b"Some garbage")

def test_redirectDirent():
    d = pyzim.BaseDirent.new(redirectDirent_content)
    assert d.kind == 'redirect'
    assert d.mimetype == 0xffff
    assert d.parameter_len == 0
    assert d.namespace == b'B'
    assert d.revision == 0
    assert d.redirect_index == 0x01000001
    assert d.url == "B/bar.html"
    assert d.title == "Bar"
    assert d.extra_data == b""

linkDirent_content = (
bytes([0xfe, 0xff]) + #mimetype
bytes([0x00]) + #parameterlen
b"B" + #namespace
bytes([0x00, 0x00, 0x00, 0x00]) + #revision
b"B/bar.html" + bytes([0]) +
b"Bar" + bytes([0]) +
b"Some garbage")

def test_linkDirent():
    d = pyzim.BaseDirent.new(linkDirent_content)
    assert d.kind == 'link'
    assert d.mimetype == 0xfffe
    assert d.parameter_len == 0
    assert d.namespace == b'B'
    assert d.revision == 0
    assert d.url == "B/bar.html"
    assert d.title == "Bar"
    assert d.extra_data == b""


deletedDirent_content = (
bytes([0xfd, 0xff]) + #mimetype
bytes([0x00]) + #parameterlen
b"B" + #namespace
bytes([0x00, 0x00, 0x00, 0x00]) + #revision
b"B/bar.html" + bytes([0]) +
b"Bar" + bytes([0]) +
b"Some garbage")

def test_deletedDirent():
    d = pyzim.BaseDirent.new(deletedDirent_content)
    assert d.kind == 'deleted'
    assert d.mimetype == 0xfffd
    assert d.parameter_len == 0
    assert d.namespace == b'B'
    assert d.revision == 0
    assert d.url == "B/bar.html"
    assert d.title == "Bar"
    assert d.extra_data == b""


