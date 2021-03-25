import struct
import sys
import weakref
from functools import wraps

from _jpegtran import ffi, lib


PY2 = sys.version_info < (3, 0)
if PY2:
    range = xrange


_weak_keydict = weakref.WeakKeyDictionary()


class ExifException(Exception):
    pass


class InvalidExifData(ExifException):
    pass


class ExifTagNotFound(ExifException):
    pass


class NoExifDataFound(ExifException):
    pass


class Exif(object):
    def __init__(self, blob):
        self._buf = blob
        # EXIF struct starts after APP1 marker (2 bytes) and size (2 bytes)
        try:
            header = self._buf.index(b'\xff\xe1')+4
        except ValueError:
            raise NoExifDataFound("Could not find EXIF data")
        if not self._buf[header:header+6] == b'Exif\x00\x00':
            raise InvalidExifData("Invalid start of EXIF data")
        # EXIF data begins after EXIF header (6 bytes)
        self._exif_start = header + 6
        alignstr = self._buf[self._exif_start:self._exif_start+2]
        if alignstr == b'II':
            self._motorola = False
        elif alignstr == b'MM':
            self._motorola = True
        else:
            raise InvalidExifData("Invalid byte alignment: {0}"
                                  .format(alignstr))
        self._ifd0 = self._unpack('I', self._exif_start+4)+self._exif_start

    @property
    def orientation(self):
        # Orientation data follows after tag (2 bytes), format (2 bytes) and
        # number of components (4 bytes)
        return self._unpack('H', self._get_tag_offset(0x112)+8)

    @orientation.setter
    def orientation(self, value):
        if not 0 < value < 9:
            raise ValueError("Orientation value must be between 1 and 8")
        self._pack('H', self._get_tag_offset(0x112)+8, value)

    @property
    def thumbnail(self):
        offset = (self._exif_start +
                  self._unpack('I', self._get_tag_offset(0x201)+8))
        size = self._unpack('I', self._get_tag_offset(0x202)+8)
        if self._buf[:2] != b'\xff\xd8':
            raise ValueError("Thumbnail is not in JPEG format.")
        return self._buf[offset:offset+size]

    @thumbnail.setter
    def thumbnail(self, data):
        offset = (self._exif_start +
                  self._unpack('I', self._get_tag_offset(0x201)+8))
        old_size = self._unpack('I', self._get_tag_offset(0x202)+8)
        app1_size_offset = self._buf.index(b'\xff\xe1')+2
        app1_size = self._unpack('>H', app1_size_offset)
        # Strip everything between the JFIF APP1 and the quant table
        try:
            jfif_start = data.index(b'\xff\xe0')
            quant_start = data.index(b'\xff\xdb')
            stripped_data = data[0:jfif_start] + data[quant_start:]
        except ValueError:
            stripped_data = data
        self._pack('>H', app1_size_offset,
                   app1_size+(len(stripped_data)-old_size))
        self._pack('I', self._get_tag_offset(0x202)+8, len(stripped_data))
        self._buf[offset:offset+old_size] = stripped_data

    def _get_tag_offset(self, tagnum):
        # IFD0 pointer starts after alignment (2 bytes) and tag mark (2 bytes)
        p_ifd = self._unpack('I', self._exif_start+4)+self._exif_start
        while True:
            num_entries = self._unpack('H', p_ifd)
            # Start after number of entries (2 bytes)
            idx = p_ifd + 2
            for _ in range(num_entries):
                tag_num = self._unpack('H', idx)
                # Check if we're at the desired tag
                if tag_num == tagnum:
                    return idx
                idx += 12
            p_ifd = self._unpack('I', idx)
            if p_ifd == 0:  # This means there are no more IFDs
                raise ExifTagNotFound("Could not find EXIF Tag {0}"
                                      .format(tagnum))
            p_ifd += self._exif_start

    def _unpack(self, fmt, offset):
        if '>' not in fmt and '<' not in fmt:
            fmt = ('>' if self._motorola else '<')+fmt
        if PY2:
            return struct.unpack_from(fmt, buffer(self._buf), offset)[0]
        else:
            return struct.unpack_from(fmt, self._buf, offset)[0]

    def _pack(self, fmt, offset, value):
        if '>' not in fmt and '<' not in fmt:
            fmt = ('>' if self._motorola else '<')+fmt
        struct.pack_into(fmt, self._buf, offset, value)


def _turbojpeg_cleanup(buffers):
    lib.tjFree(buffers[0])


def jpegtran_op(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Setup variables
        in_data_len = len(self._data)
        in_data_p = ffi.new("unsigned char[]", in_data_len)
        inbuf = ffi.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data

        out_bufs = ffi.gc(ffi.new("unsigned char**"), _turbojpeg_cleanup)
        out_bufs[0] = ffi.NULL
        out_sizes = ffi.new("unsigned long*")

        tjhandle = ffi.gc(lib.tjInitTransform(), lib.tjDestroy)

        # Call the wrapped function with the transformoption struct
        transformoption = func(self, *args, **kwargs)
        if transformoption.options & lib.TJXOPT_PROGRESSIVE:
            flag = 16384
        else:
            flag = 0

        # Execute transformation
        rv = lib.tjTransform(tjhandle, in_data_p, in_data_len, 1,
                             out_bufs, out_sizes, transformoption, flag)
        if rv < 0:
            raise Exception("Transformation failed: {0}"
                            .format(ffi.string(lib.tjGetErrorStr())))

        _weak_keydict[out_bufs[0]] = out_bufs
        return bytearray(ffi.buffer(out_bufs[0], out_sizes[0])[:])
    return wrapper


def _epeg_free_buffer(buffer):
    lib.free(buffer[0])


class Transformation(object):
    def __init__(self, blob):
        self._data = blob

    def get_dimensions(self):
        width = ffi.new("int*")
        height = ffi.new("int*")
        in_data_len = len(self._data)
        in_data_p = ffi.new("unsigned char[]", in_data_len)
        inbuf = ffi.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data
        img = ffi.gc(lib.epeg_memory_open(in_data_p, in_data_len),
                     lib.epeg_close)
        lib.epeg_size_get(img, width, height)
        return (width[0], height[0])

    def scale(self, width, height, quality=75):
        in_data_len = len(self._data)
        in_data_p = ffi.new("unsigned char[]", in_data_len)
        inbuf = ffi.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data
        img = ffi.gc(lib.epeg_memory_open(in_data_p, in_data_len),
                     lib.epeg_close)
        lib.epeg_decode_size_set(img, width, height)
        lib.epeg_quality_set(img, quality)

        pdata = ffi.gc(ffi.new("unsigned char **"), _epeg_free_buffer)
        psize = ffi.new("int*")
        lib.epeg_memory_output_set(img, pdata, psize)
        lib.epeg_encode(img)

        _weak_keydict[pdata[0]] = pdata
        return bytearray(ffi.buffer(pdata[0], psize[0])[:])

    def _get_transformoptions(self, perfect=False, trim=False):
        # Initialize jpeg_transform_info struct
        options = ffi.new("tjtransform*")
        options.op = lib.TJXOP_NONE
        options.options = 0
        if perfect:
            options.options |= lib.TJXOPT_PERFECT
        if trim:
            options.options |= lib.TJXOPT_TRIM
        return options

    @jpegtran_op
    def grayscale(self):
        options = self._get_transformoptions()
        options.options = lib.TJXOPT_GRAY
        return options

    @jpegtran_op
    def rotate(self, angle):
        options = self._get_transformoptions()
        if angle == 90:
            options.op = lib.TJXOP_ROT90
        elif angle == 180:
            options.op = lib.TJXOP_ROT180
        elif angle in (-90, 270):
            options.op = lib.TJXOP_ROT270
        else:
            raise ValueError("Invalid angle, must be -90, 90, 180 or 270")
        return options

    @jpegtran_op
    def flip(self, direction):
        options = self._get_transformoptions()
        if direction == 'vertical':
            options.op = lib.TJXOP_VFLIP
        elif direction == 'horizontal':
            options.op = lib.TJXOP_HFLIP
        else:
            raise ValueError("Invalid direction, must be 'vertical' or "
                             "'horizontal'")
        return options

    @jpegtran_op
    def transpose(self):
        options = self._get_transformoptions()
        options.op = lib.TJXOP_TRANSPOSE
        return options

    @jpegtran_op
    def transverse(self):
        options = self._get_transformoptions()
        options.op = lib.TJXOP_TRANSVERSE
        return options

    @jpegtran_op
    def crop(self, x, y, width, height):
        options = self._get_transformoptions()
        options.r = ffi.new("tjregion*")[0]
        options.r.w = width
        options.r.h = height
        options.r.x = x
        options.r.y = y
        options.options = lib.TJXOPT_CROP
        return options

    @jpegtran_op
    def progressive(self, copynone=False):
        options = self._get_transformoptions()
        options.options = lib.TJXOPT_PROGRESSIVE
        if copynone:
            options.options |= lib.TJXOPT_COPYNONE
        return options

    @jpegtran_op
    def copynone(self):
        options = self._get_transformoptions()
        options.options = lib.TJXOPT_COPYNONE
        return options
