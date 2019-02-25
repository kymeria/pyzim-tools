
from struct import Struct
from lzma import LZMADecompressor

CTYPES = {}
for t in (('c_uint8', 'B'),
          ('c_char', 'c'),
          ('c_uint16', 'H'),
          ('c_uint32', 'I'),
          ('c_uint64', 'Q')):
    _name, _format = t
    CTYPES[_name] = Struct('<'+_format)

class AttributeDescriptor:
    def __init__(self, offset, ctype):
        self.offset = offset
        try:
            self.ctype = CTYPES[ctype]
        except KeyError:
            self.ctype = Struct('<'+ctype)

    def __get__(self, obj, objtype):
        return self.ctype.unpack_from(obj.buf, self.offset)[0]

class MetaBaseStruct(type):
    def __new__(cls, name, bases, attrs):
        fields = attrs.get('_fields_', [])
        offset = 0
        for field in fields:
            if len(field) == 3:
               name, ctype, size = field
            else:
               name, ctype = field
               size = None
            attrs[name] = AttributeDescriptor(offset, ctype)
            if size is None:
                size = attrs[name].ctype.size
            offset += size
        attrs['size'] = offset

        return super().__new__(cls, name, bases, attrs)

class mimeTypeList:
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


class BaseStruct(metaclass=MetaBaseStruct):
    def __init__(self, buf):
        self.buf = buf

class BaseArray:
    def __init__(self, buf):
        self.buf = buf

    def __getitem__(self, index):
        offset = index*self.ctype.size
        return self.ctype.unpack_from(self.buf, offset)[0]


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
        ('checksumPos', 'c_uint64'),
    ]
assert(Header.size == 80)


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
        off = self.size
        end_off = self.buf.index(bytes([0]), off)
        return self.buf[off:end_off].decode()

    @property
    def title(self):
        # Start of url
        off = self.size
        # Start of title
        off = self.buf.index(bytes([0]), off) + 1
        end_off = self.buf.index(bytes([0]), off)
        return self.buf[off:end_off].decode()

    @property
    def extra_data(self):
        # Start of url
        off = self.size
        # Start of title
        off = self.buf.index(bytes([0]), off) + 1
        # Start of data
        off = self.buf.index(bytes([0]), off) + 1
        return self.buf[off:off+self.parameter_len]

class ArticleDirent(BaseDirent):
    _fields_ = [
        ('mimetype', 'c_uint16'),
        ('parameter_len', 'c_uint8'),
        ('namespace', 'c_char'),
        ('revision', 'c_uint32'),
        ('clusterNumber', 'c_uint32'),
        ('blobNumber', 'c_uint32')
    ]
assert ArticleDirent.size == 16

class RedirectDirent(BaseDirent):
    _fields_ = [
        ('mimetype', 'c_uint16'),
        ('parameter_len', 'c_uint8'),
        ('namespace', 'c_char'),
        ('revision', 'c_uint32'),
        ('redirect_index', 'c_uint32')
    ]
assert RedirectDirent.size == 12

class LinkDeletedDirent(BaseDirent):
    _fields_ = [
        ('mimetype', 'c_uint16'),
        ('parameter_len', 'c_uint8'),
        ('namespace', 'c_char'),
        ('revision', 'c_uint32')
    ]
assert LinkDeletedDirent.size == 8


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
        return bool(self.info & 0b0001000)

    @property
    def data(self):
        if self.compression == 4:
            if self._data is None:
                decompressor = LZMADecompressor()
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

sample_zim =  bytes([
0x5a, 0x49, 0x4d, 0x04, 0x05, 0x00, 0x00, 0x00, 0x19, 0xfd,
0x91, 0x00, 0x73, 0x2b, 0xcf, 0xb6, 0x34, 0x06, 0x55, 0x19,
0xac, 0x2e, 0x03, 0xc4, 0x03, 0x00, 0x00, 0x00, 0x01, 0x00,
0x00, 0x00, 0x66, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x7e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xce, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x50, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
0xff, 0xff, 0x27, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x74, 0x65, 0x78, 0x74, 0x2f, 0x68, 0x74, 0x6d, 0x6c, 0x00,
0x74, 0x65, 0x78, 0x74, 0x2f, 0x70, 0x6c, 0x61, 0x69, 0x6e,
0x00, 0x00, 0x8a, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0xa0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xb8, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x41, 0x75, 0x74, 0x6f, 0x00, 0x00,
0xff, 0xff, 0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x41, 0x75, 0x74, 0x6f, 0x6d, 0x6f, 0x62, 0x69,
0x6c, 0x65, 0x00, 0x00, 0x01, 0x00, 0x00, 0x42, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
0x41, 0x75, 0x74, 0x6f, 0x00, 0x00, 0xd6, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x04, 0xfd, 0x37, 0x7a, 0x58, 0x5a,
0x00, 0x00, 0x01, 0x69, 0x22, 0xde, 0x36, 0x02, 0x00, 0x21,
0x01, 0x10, 0x00, 0x00, 0x00, 0xa8, 0x70, 0x8e, 0x86, 0xe0,
0x00, 0x1c, 0x00, 0x18, 0x5e, 0x00, 0x06, 0x00, 0x34, 0xfb,
0xde, 0x91, 0x72, 0xa3, 0x80, 0x34, 0xfc, 0x31, 0x87, 0x1f,
0xe6, 0xaa, 0x61, 0x04, 0x70, 0x25, 0xb1, 0x84, 0xdc, 0x00,
0x00, 0xe1, 0x66, 0xf9, 0xe7, 0x00, 0x01, 0x30, 0x1d, 0x01,
0xef, 0xc6, 0x9c, 0x90, 0x42, 0x99, 0x0d, 0x01, 0x00, 0x00,
0x00, 0x00, 0x01, 0x59, 0x5a, 0x6c, 0xd7, 0x5d, 0xbe, 0x78,
0x95, 0x3c, 0x79, 0xd9, 0x50, 0x54, 0x03, 0x4b, 0x57, 0x26,
0xc4])


if __name__ == "__main__":
    h = Header(sample_zim)
    m = mimeTypeList(h.buf[h.mimeListPos:])
    print(m[0])
    print(m[1])

    urls = UrlPtrList(h.buf[h.urlPtrPos:])
    clusterOffsets = ClusterPtrList(h.buf[h.clusterPtrPos:])
    for i in range(h.articleCount):
        d = BaseDirent.new(h.buf[urls[i]:])
        print('----')
        print(d.namespace, d.url, d.title)
        if type(d) == ArticleDirent:
            print(d.clusterNumber, d.blobNumber)
            clusterOffset = clusterOffsets[d.clusterNumber]
            print(clusterOffset)
            cluster = Cluster(h.buf[clusterOffset:])
            print(cluster.info, cluster.compression, cluster.extended)
            print(cluster.get_blob_data(d.blobNumber))
