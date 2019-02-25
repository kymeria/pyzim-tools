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
    c = pyzim.Cluster(cluster_content)
    assert c.compression == (4 if compressed else 0)
    assert c.extended == extended
    assert c.nb_blobs == nbBlob
    for i in range(nbBlob):
        assert c.get_blob_data(i) == bytes([i]) * i * 10
    with pytest.raises(IndexError):
        c.get_blob_data(nbBlob)
