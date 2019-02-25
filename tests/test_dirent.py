# coding=utf-8

# This file is part of pyzim-tools.
#
# pyzim-tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License.
#
# pyzim-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyzim-tools.  If not, see <https://www.gnu.org/licenses/>.


import pytest
import pyzim


articleDirent_content = (
    bytes([0x02, 0x00])  # mimetype
    + bytes([0x00])  # parameterlen
    + b"A"  # namespace
    + bytes([0x00, 0x00, 0x00, 0x00])  # revision
    + bytes([0x01, 0x00, 0x00, 0x00])  # clusterNumber
    + bytes([0x02, 0x00, 0x00, 0x00])  # blobNumber
    + b"A/foo.html"  # url
    + bytes([0])
    + b"Foo"  # title
    + bytes([0])
    + b"Some garbage"
)


def test_articleDirent():
    d = pyzim.Dirent(articleDirent_content, 0)
    assert d.kind == "article"
    assert d.mimetype == 0x0002
    assert d.parameter_len == 0
    assert d.namespace == b"A"
    assert d.revision == 0
    assert d.clusterNumber == 1
    assert d.blobNumber == 2
    assert d.url == "A/foo.html"
    assert d.title == "Foo"
    assert d.extra_data == b""


redirectDirent_content = (
    bytes([0xFF, 0xFF])  # mimetype
    + bytes([0x00])  # parameterlen
    + b"B"  # namespace
    + bytes([0x00, 0x00, 0x00, 0x00])  # revision
    + bytes([0x01, 0x00, 0x00, 0x01])  # redirection index
    + b"B/bar.html"  # url
    + bytes([0])
    + b"Bar"  # title
    + bytes([0])
    + b"Some garbage"
)


def test_redirectDirent():
    d = pyzim.Dirent(redirectDirent_content, 0)
    assert d.kind == "redirect"
    assert d.mimetype == 0xFFFF
    assert d.parameter_len == 0
    assert d.namespace == b"B"
    assert d.revision == 0
    assert d.redirect_index == 0x01000001
    assert d.url == "B/bar.html"
    assert d.title == "Bar"
    assert d.extra_data == b""


linkDirent_content = (
    bytes([0xFE, 0xFF])  # mimetype
    + bytes([0x00])  # parameterlen
    + b"B"  # namespace
    + bytes([0x00, 0x00, 0x00, 0x00])  # revision
    + b"B/bar.html"  # url
    + bytes([0])
    + b"Bar"  # title
    + bytes([0])
    + b"Some garbage"
)


def test_linkDirent():
    d = pyzim.Dirent(linkDirent_content, 0)
    assert d.kind == "link"
    assert d.mimetype == 0xFFFE
    assert d.parameter_len == 0
    assert d.namespace == b"B"
    assert d.revision == 0
    assert d.url == "B/bar.html"
    assert d.title == "Bar"
    assert d.extra_data == b""


deletedDirent_content = (
    bytes([0xFD, 0xFF])  # mimetype
    + bytes([0x00])  # parameterlen
    + b"B"  # namespace
    + bytes([0x00, 0x00, 0x00, 0x00])  # revision
    + b"B/bar.html"  # url
    + bytes([0])
    + b"Bar"  # title
    + bytes([0])
    + b"Some garbage"
)


def test_deletedDirent():
    d = pyzim.Dirent(deletedDirent_content, 0)
    assert d.kind == "deleted"
    assert d.mimetype == 0xFFFD
    assert d.parameter_len == 0
    assert d.namespace == b"B"
    assert d.revision == 0
    assert d.url == "B/bar.html"
    assert d.title == "Bar"
    assert d.extra_data == b""
