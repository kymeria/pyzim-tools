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
from itertools import product, chain
from lzma import compress
from struct import pack


@pytest.fixture(params=list(product([True, False], [True, False], [0, 1, 2, 3, 4])))
def cluster_info(request):
    compressed, extended, nbBlob = request.param
    info = (0b10000 if extended else 0) + (4 if compressed else 0)
    offset_size = 8 if extended else 4

    offset_array = [(nbBlob + 1) * offset_size]
    data_array = []
    for index in range(nbBlob):
        data_array.append(bytes([index]) * index * 10)
        offset_array.append(offset_array[-1] + index * 10)

    pack_format = "<Q" if extended else "<I"
    full_data = b"".join(
        chain((pack(pack_format, off) for off in offset_array), (d for d in data_array))
    )
    if compressed:
        full_data = compress(full_data)
    return bytes([info]) + full_data, compressed, extended, nbBlob


def test_mimeList_content(cluster_info):
    cluster_content, compressed, extended, nbBlob = cluster_info
    c = pyzim.Cluster(cluster_content, 0)
    assert c.compression == (4 if compressed else 0)
    assert c.extended == extended
    assert c.nb_blobs == nbBlob
    for i in range(nbBlob):
        assert c.get_blob_data(i) == bytes([i]) * i * 10
    with pytest.raises(IndexError):
        c.get_blob_data(nbBlob)
