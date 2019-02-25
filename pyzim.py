
import struct
from lzma import LZMADecompressor, FORMAT_XZ

CTYPES = {}
for t in (('c_uint8', 'B'),
          ('c_char', 'c'),
          ('c_uint16', 'H'),
          ('c_uint32', 'I'),
          ('c_uint64', 'Q')):
    _name, _format = t
    CTYPES[_name] = struct.Struct('<'+_format)


__all__ = ['MimetypeList',
           'UrlPtrList',
           'TitlePtrList',
           'ClusterPtrList',
           'Header',
           'BaseDirent',
           'ArticleDirent',
           'RedirectDirent',
           'LinkDeletedDirent',
           'Cluster'
          ]

class AttributeDescriptor:
    def __init__(self, offset, ctype):
        self.offset = offset
        try:
            self.ctype = CTYPES[ctype]
        except KeyError:
            self.ctype = struct.Struct('<'+ctype)

    def __get__(self, obj, objtype):
        return self.ctype.unpack_from(obj.buf, self.offset)[0]

class MetaBaseStruct(type):
    def __new__(cls, name, bases, attrs):
        fields = attrs.get('_fields_', [])
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
        attrs['csize'] = offset

        return super().__new__(cls, name, bases, attrs)

class MimetypeList:
    def __init__(self, buf):
        self.buf = buf

    def __getitem__(self, index):
        off = 0
        for i in range(index):
            end_off = self.buf.index(bytes([0]), off)
            if end_off == off:
                #empty string, end of the mimelist.
                raise IndexError
            off = end_off+1
        end_off = self.buf.index(bytes([0]), off)
        if end_off == off:
            raise IndexError
        return self.buf[off:end_off].decode('ascii')


    def __len__(self):
       end_buf = self.buf.index(bytes([0, 0]))
       return self.buf.count(bytes([0]), 0, end_buf+1)


class BaseStruct(metaclass=MetaBaseStruct):
    def __init__(self, buf):
        self.buf = buf

class BaseArray:
    def __init__(self, buf):
        self.buf = buf

    def __getitem__(self, index):
        offset = index*self.ctype.size
        try:
            return self.ctype.unpack_from(self.buf, offset)[0]
        except struct.error:
            raise IndexError


class UrlPtrList(BaseArray):
    ctype = CTYPES['c_uint64']

class TitlePtrList(BaseArray):
    ctype = CTYPES['c_uint32']

class ClusterPtrList(BaseArray):
    ctype = CTYPES['c_uint64']

class Header(BaseStruct):
    _fields_ = [
        ('magicNumber', 'c_uint32'),
        ('majorVersion', 'c_uint16'),
        ('minorVersion', 'c_uint16'),
        ('uuid', '16s'),
        ('articleCount', 'c_uint32'),
        ('clusterCount', 'c_uint32'),
        ('urlPtrPos', 'c_uint64'),
        ('titlePtrPos', 'c_uint64'),
        ('clusterPtrPos', 'c_uint64'),
        ('mimeListPos', 'c_uint64'),
        ('mainPage', 'c_uint32'),
        ('layoutPage', 'c_uint32'),
        ('_checksumPos', 'c_uint64'),
    ]

    @property
    def size(self):
        return self.mimeListPos

    @property
    def checksumPos(self):
        if self.mimeListPos < 80:
            raise ValueError("Header has no checksumPos")
        return self._checksumPos
assert(Header.csize == 80)

class BaseDirent(BaseStruct):
    @staticmethod
    def new(buf):
        mimetype = CTYPES['c_uint16'].unpack_from(buf)[0]
        if mimetype == 0xffff:
            return RedirectDirent(buf)
        if mimetype in (0xfffe, 0xfffd):
            return LinkDeletedDirent(buf)
        return ArticleDirent(buf)

    @property
    def url(self):
        off = self.csize
        end_off = self.buf.index(bytes([0]), off)
        return self.buf[off:end_off].decode()

    @property
    def title(self):
        # Start of url
        off = self.csize
        # Start of title
        off = self.buf.index(bytes([0]), off) + 1
        end_off = self.buf.index(bytes([0]), off)
        return self.buf[off:end_off].decode()

    @property
    def extra_data(self):
        # Start of url
        off = self.csize
        # Start of title
        off = self.buf.index(bytes([0]), off) + 1
        # Start of data
        off = self.buf.index(bytes([0]), off) + 1
        return self.buf[off:off+self.parameter_len]

class ArticleDirent(BaseDirent):
    kind = 'article'
    _fields_ = [
        ('mimetype', 'c_uint16'),
        ('parameter_len', 'c_uint8'),
        ('namespace', 'c_char'),
        ('revision', 'c_uint32'),
        ('clusterNumber', 'c_uint32'),
        ('blobNumber', 'c_uint32')
    ]
assert ArticleDirent.csize == 16

class RedirectDirent(BaseDirent):
    kind = 'redirect'
    _fields_ = [
        ('mimetype', 'c_uint16'),
        ('parameter_len', 'c_uint8'),
        ('namespace', 'c_char'),
        ('revision', 'c_uint32'),
        ('redirect_index', 'c_uint32')
    ]
assert RedirectDirent.csize == 12

class LinkDeletedDirent(BaseDirent):
    _fields_ = [
        ('mimetype', 'c_uint16'),
        ('parameter_len', 'c_uint8'),
        ('namespace', 'c_char'),
        ('revision', 'c_uint32')
    ]

    @property
    def kind(self):
        return 'link' if self.mimetype == 0xfffe else 'deleted'
assert LinkDeletedDirent.csize == 8

class NormalBlobOffsetArray(BaseArray):
    ctype = CTYPES['c_uint32']

class ExtendedBlobOffsetArray(BaseArray):
    ctype = CTYPES['c_uint64']

class Cluster(BaseStruct):
    _fields_ = [
        ('info', 'c_uint8')
    ]

    def __init__(self, buf):
        super().__init__(buf)
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
                self._data = decompressor.decompress(self.buf[1:])
            return self._data
        else:
            return self.buf[1:]

    @property
    def offsetArray(self):
        if self._offsetArray is None:
            OffsetArrayType = ExtendedBlobOffsetArray if self.extended else NormalBlobOffsetArray
            self._offsetArray = OffsetArrayType(self.data)
        return self._offsetArray

    @property
    def nb_blobs(self):
        return self.nb_offsets - 1

    @property
    def nb_offsets(self):
        first_offset = self.offsetArray[0]
        ctype = CTYPES['c_uint64'] if self.extended else CTYPES['c_uint32']
        return first_offset//ctype.size

    def get_blob_offset(self, index):
        if index >= self.nb_offsets:
            raise IndexError
        return self.offsetArray[index]

    def get_blob_data(self, index):
        blob_offset = self.get_blob_offset(index)
        end_offset = self.get_blob_offset(index+1)
        return self.data[blob_offset:end_offset]
