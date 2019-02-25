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


mimeList_content = (
    b"text/html"
    + bytes([0])
    + b"text/plain"
    + bytes([0])
    + b"image/png"
    + bytes([0])
    + bytes([0])
    + b"Some garbage"
)


def test_mimeList_content():
    m = pyzim.MimetypeList(mimeList_content, 0)
    assert len(m) == 3
    assert m[0] == "text/html"
    assert m[1] == "text/plain"
    assert m[2] == "image/png"
    with pytest.raises(IndexError):
        m[3]
