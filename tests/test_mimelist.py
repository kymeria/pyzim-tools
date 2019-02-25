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
    m = pyzim.MimetypeList(mimeList_content)
    assert len(m) == 3
    assert m[0] == "text/html"
    assert m[1] == "text/plain"
    assert m[2] == "image/png"
    with pytest.raises(IndexError):
        m[3]
