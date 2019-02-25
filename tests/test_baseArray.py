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


# fmt: off
array_content = bytes([
0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06 ,0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16 ,0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f,
0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26 ,0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f,
0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36 ,0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3D, 0x3e, 0x3f,
0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46 ,0x47, 0x48, 0x49, 0x4a, 0x4b, 0x4c, 0x4d, 0x4e, 0x4f,
0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56 ,0x57, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e, 0x5f
])
# fmt: on


def test_baseArray_uint8():
    class Array8(pyzim.BaseArray):
        ctype = pyzim.CTYPES["c_uint8"]

    a = Array8(array_content)
    for i in range(0x60):
        assert a[i] == i
    with pytest.raises(IndexError):
        a[0x60]


def test_baseArray_uint16():
    class Array16(pyzim.BaseArray):
        ctype = pyzim.CTYPES["c_uint16"]

    a = Array16(array_content)
    max_index = 0x60 // 2
    for i in range(max_index):
        v = ((i * 2 + 1) << 8) + i * 2
        assert a[i] == v
    with pytest.raises(IndexError):
        a[max_index]


def test_baseArray_uint32():
    class Array32(pyzim.BaseArray):
        ctype = pyzim.CTYPES["c_uint32"]

    a = Array32(array_content)
    max_index = 0x60 // 4
    for i in range(max_index):
        v = ((i * 4 + 3) << 24) + ((i * 4 + 2) << 16) + ((i * 4 + 1) << 8) + i * 4
        assert a[i] == v
    with pytest.raises(IndexError):
        a[max_index]


def test_baseArray_uint64():
    class Array64(pyzim.BaseArray):
        ctype = pyzim.CTYPES["c_uint64"]

    a = Array64(array_content)
    max_index = 0x60 // 8
    for i in range(max_index):
        v = (
            ((i * 8 + 7) << 56)
            + ((i * 8 + 6) << 48)
            + ((i * 8 + 5) << 40)
            + ((i * 8 + 4) << 32)
            + ((i * 8 + 3) << 24)
            + ((i * 8 + 2) << 16)
            + ((i * 8 + 1) << 8)
            + i * 8
        )
        assert a[i] == v
    with pytest.raises(IndexError):
        a[max_index]
