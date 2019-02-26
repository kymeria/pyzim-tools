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


import struct
from lzma import LZMADecompressor, FORMAT_XZ

CTYPES = {}
for t in (
    ("c_uint8", "B"),
    ("c_char", "c"),
    ("c_uint16", "H"),
    ("c_uint32", "I"),
    ("c_uint64", "Q"),
):
    _name, _format = t
    CTYPES[_name] = struct.Struct("<" + _format)


__all__ = [
    "MimetypeList",
    "UrlPtrList",
    "TitlePtrList",
    "ClusterPtrList",
    "Header",
    "Dirent",
    "Cluster",
]


class AttributeDescriptor:
    def __init__(self, offset, ctype):
        self.offset = offset
        try:
            self.ctype = CTYPES[ctype]
        except KeyError:
            self.ctype = struct.Struct("<" + ctype)

    def __get__(self, obj, objtype):
        return self.ctype.unpack_from(obj.buf, obj.offset + self.offset)[0]


class MetaBaseStruct(type):
    def __new__(cls, name, bases, attrs):
        fields = attrs.get("_fields_", [])
        offset = 0
        for field in fields:
            if len(field) == 3:
                name_, ctype, size = field
            else:
                name_, ctype = field
                size = None
            attrs[name_] = AttributeDescriptor(offset, ctype)
            if size is None:
                size = attrs[name_].ctype.size
            offset += size
        attrs["csize"] = offset

        return super().__new__(cls, name, bases, attrs)


class MimetypeList:
    def __init__(self, buf, offset):
        self.buf = buf
        self.offset = offset

    def __getitem__(self, index):
        off = self.offset
        for i in range(index):
            end_off = self.buf.find(bytes([0]), off)
            if end_off == off:
                # empty string, end of the mimelist.
                raise IndexError
            off = end_off + 1
        end_off = self.buf.find(bytes([0]), off)
        if end_off == off:
            raise IndexError
        return self.buf[off:end_off].decode("ascii")

    def __len__(self):
        end_buf = self.buf.find(bytes([0, 0]), self.offset)
        return self.buf.count(bytes([0]), self.offset, end_buf + 1)


class BaseStruct(metaclass=MetaBaseStruct):
    def __init__(self, buf, offset):
        self.buf = buf
        self.offset = offset


class BaseArray:
    def __init__(self, buf, offset):
        self.buf = buf
        self.offset = offset

    def __getitem__(self, index):
        offset = self.offset + index * self.ctype.size
        try:
            return self.ctype.unpack_from(self.buf, offset)[0]
        except struct.error:
            raise IndexError


class UrlPtrList(BaseArray):
    ctype = CTYPES["c_uint64"]


class TitlePtrList(BaseArray):
    ctype = CTYPES["c_uint32"]


class ClusterPtrList(BaseArray):
    ctype = CTYPES["c_uint64"]


class Header(BaseStruct):
    _fields_ = [
        ("magicNumber", "c_uint32"),
        ("majorVersion", "c_uint16"),
        ("minorVersion", "c_uint16"),
        ("uuid", "16s"),
        ("articleCount", "c_uint32"),
        ("clusterCount", "c_uint32"),
        ("urlPtrPos", "c_uint64"),
        ("titlePtrPos", "c_uint64"),
        ("clusterPtrPos", "c_uint64"),
        ("mimeListPos", "c_uint64"),
        ("mainPage", "c_uint32"),
        ("layoutPage", "c_uint32"),
        ("_checksumPos", "c_uint64"),
    ]

    @property
    def size(self):
        return self.mimeListPos

    @property
    def checksumPos(self):
        if self.mimeListPos < 80:
            raise ValueError("Header has no checksumPos")
        return self._checksumPos


assert Header.csize == 80


class Dirent(BaseStruct):
    def __new__(cls, buf, offset):
        mimetype = CTYPES["c_uint16"].unpack_from(buf[offset:offset+2])[0]
        if mimetype == 0xFFFF:
            return super(Dirent, cls).__new__(RedirectDirent)
        if mimetype in (0xFFFE, 0xFFFD):
            return super(Dirent, cls).__new__(LinkDeletedDirent)
        return super(Dirent, cls).__new__(ArticleDirent)

    @property
    def url(self):
        off = self.offset + self.csize
        end_off = self.buf.find(bytes([0]), off)
        return self.buf[off:end_off].decode()

    @property
    def title(self):
        # Start of url
        off = self.offset + self.csize
        # Start of title
        off = self.buf.find(bytes([0]), off) + 1
        end_off = self.buf.find(bytes([0]), off)
        return self.buf[off:end_off].decode()

    @property
    def extra_data(self):
        # Start of url
        off = self.offset + self.csize
        # Start of title
        off = self.buf.find(bytes([0]), off) + 1
        # Start of data
        off = self.buf.find(bytes([0]), off) + 1
        return self.buf[off : off + self.parameter_len]


class ArticleDirent(Dirent):
    kind = "article"
    _fields_ = [
        ("mimetype", "c_uint16"),
        ("parameter_len", "c_uint8"),
        ("namespace", "c_char"),
        ("revision", "c_uint32"),
        ("clusterNumber", "c_uint32"),
        ("blobNumber", "c_uint32"),
    ]


assert ArticleDirent.csize == 16


class RedirectDirent(Dirent):
    kind = "redirect"
    _fields_ = [
        ("mimetype", "c_uint16"),
        ("parameter_len", "c_uint8"),
        ("namespace", "c_char"),
        ("revision", "c_uint32"),
        ("redirect_index", "c_uint32"),
    ]


assert RedirectDirent.csize == 12


class LinkDeletedDirent(Dirent):
    _fields_ = [
        ("mimetype", "c_uint16"),
        ("parameter_len", "c_uint8"),
        ("namespace", "c_char"),
        ("revision", "c_uint32"),
    ]

    @property
    def kind(self):
        return "link" if self.mimetype == 0xFFFE else "deleted"


assert LinkDeletedDirent.csize == 8


class NormalBlobOffsetArray(BaseArray):
    ctype = CTYPES["c_uint32"]


class ExtendedBlobOffsetArray(BaseArray):
    ctype = CTYPES["c_uint64"]


class Cluster(BaseStruct):
    _fields_ = [("info", "c_uint8")]

    def __init__(self, buf, offset):
        super().__init__(buf, offset)
        self._data = None
        self._offsetArray = None

    @property
    def compression(self):
        return self.info & 0b00001111

    @property
    def extended(self):
        return bool(self.info & 0b00010000)

    @property
    def data(self):
        if self.compression == 4:
            if self._data is None:
                decompressor = LZMADecompressor(format=FORMAT_XZ)
                offset = self.offset + 1
                self._data = b""
                while decompressor.needs_input:
                    idata = self.buf[offset:offset+1024]
                    self._data += decompressor.decompress(idata)
                    offset += 1024
            return self._data, 0
        else:
            return self.buf, self.offset+1

    @property
    def offsetArray(self):
        if self._offsetArray is None:
            OffsetArrayType = (
                ExtendedBlobOffsetArray if self.extended else NormalBlobOffsetArray
            )
            self._offsetArray = OffsetArrayType(*self.data)
        return self._offsetArray

    @property
    def nb_blobs(self):
        return self.nb_offsets - 1

    @property
    def nb_offsets(self):
        first_offset = self.offsetArray[0]
        ctype = CTYPES["c_uint64"] if self.extended else CTYPES["c_uint32"]
        return first_offset // ctype.size

    def get_blob_offset(self, index):
        if index >= self.nb_offsets:
            raise IndexError
        return self.offsetArray[index]

    def get_blob_data(self, index):
        blob_offset = self.get_blob_offset(index)
        end_offset = self.get_blob_offset(index + 1)
        data, offset = self.data
        return data[offset+blob_offset:offset+end_offset]
