from pyzim import bisect
import pytest


def test_bisect():
    def comp(i):
        return i - 5

    assert bisect(comp, 0, 10) == 5
    assert bisect(comp, 5, 10) == 5
    with pytest.raises(IndexError):
        bisect(comp, 5, 5)
        bisect(comp, 0, 5)
