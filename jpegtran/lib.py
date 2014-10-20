import struct
import sys
import weakref
from functools import wraps

PY2 = sys.version_info < (3, 0)
if PY2:
    range = xrange

from cffi import FFI
ffi_epeg = FFI()
ffi_jpeg = None

JPEG8 = False
TURBOJPEG = False

ffi_epeg.cdef("""
   void free(void *);

   typedef ... Epeg_Image;
   Epeg_Image   *epeg_file_open         (const char *file);
   Epeg_Image   *epeg_memory_open       (unsigned char *data, int size);
   void          epeg_size_get          (Epeg_Image *im, int *w, int *h);
   void          epeg_decode_size_set   (Epeg_Image *im, int w, int h);
   void          epeg_quality_set       (Epeg_Image *im, int quality);
   void          epeg_file_output_set   (Epeg_Image *im, const char *file);
   void          epeg_memory_output_set (Epeg_Image *im, unsigned char **data,
                                         int *size);
   int           epeg_encode            (Epeg_Image *im);
   int           epeg_trim              (Epeg_Image *im);
   void          epeg_close             (Epeg_Image *im);
""")
libepeg = ffi_epeg.verify("""
#include "Epeg.h"
#include "epeg_private.h"
#include "jpeglib.h"
""", sources=["src/epeg.c"],
    include_dirs=["src"], define_macros=[("HAVE_UNSIGNED_CHAR", "1")],
    libraries=["jpeg"])

try:
    ffi = FFI()
    ffi.cdef("""
        enum TJXOP {
            TJXOP_NONE,
            TJXOP_HFLIP,
            TJXOP_VFLIP,
            TJXOP_TRANSPOSE,
            TJXOP_TRANSVERSE,
            TJXOP_ROT90,
            TJXOP_ROT180,
            TJXOP_ROT270
        };

        #define TJXOPT_PERFECT  ...
        #define TJXOPT_TRIM     ...
        #define TJXOPT_CROP     ...
        #define TJXOPT_GRAY     ...

        typedef struct {
            int x;
            int y;
            int w;
            int h;
        } tjregion;

        typedef struct tjtransform {
            tjregion r;
            int op;
            int options;
            ...;
        } tjtransform;

        typedef void* tjhandle;


        tjhandle tjInitTransform(void);
        int tjDecompressHeader2(tjhandle handle, unsigned char *jpegBuf,
                                unsigned long jpegSize, int *width,
                                int *height, int *jpegSubsamp);
        int tjTransform(tjhandle handle, unsigned char *jpegBuf,
                        unsigned long jpegSize, int n, unsigned char **dstBufs,
                        unsigned long *dstSizes, tjtransform *transforms,
                        int flags);
        int tjDestroy(tjhandle handle);
        void tjFree(unsigned char *buffer);
        char* tjGetErrorStr(void);
    """)

    libjpeg = ffi.verify("""
    #include "turbojpeg.h"
    """, libraries=["turbojpeg"])
    ffi_jpeg = ffi
    TURBOJPEG = True
except:
    ffi = FFI()
    ffi.cdef("""
    void free(void *);

    typedef int boolean;
    typedef ... jvirt_barray_ptr;
    typedef enum {
        JXFORM_NONE,
        JXFORM_FLIP_H,
        JXFORM_FLIP_V,
        JXFORM_TRANSPOSE,
        JXFORM_TRANSVERSE,
        JXFORM_ROT_90,
        JXFORM_ROT_180,
        JXFORM_ROT_270
    } JXFORM_CODE;
    typedef enum {
        JCROP_UNSET,
        JCROP_POS,
        JCROP_NEG,
        JCROP_FORCE
    } JCROP_CODE;
    typedef struct {
        JXFORM_CODE transform;
        boolean perfect;
        boolean trim;
        boolean force_grayscale;
        boolean crop;
        unsigned int crop_width;
        JCROP_CODE crop_width_set;
        unsigned int crop_height;
        JCROP_CODE crop_height_set;
        unsigned int crop_xoffset;
        JCROP_CODE crop_xoffset_set;
        unsigned int crop_yoffset;
        JCROP_CODE crop_yoffset_set;
        ...;
    } jpeg_transform_info;
    struct jpeg_common_struct {
        struct jpeg_error_mgr* err;
        ...;
    };
    struct jpeg_decompress_struct {
        struct jpeg_error_mgr* err;
        ...;
    };
    struct jpeg_compress_struct {
        struct jpeg_error_mgr* err;
        ...;
    };
    typedef struct jpeg_compress_struct* j_compress_ptr;
    typedef struct jpeg_decompress_struct* j_decompress_ptr;
    typedef struct jpeg_common_struct* j_common_ptr;
    struct jpeg_error_mgr {
        void (*reset_error_mgr)  (j_common_ptr cinfo);
        void (*emit_message)     (j_common_ptr cinfo, int msg_level);
        int  trace_level;
        long num_warnings;
        int msg_code;
        ...;
    };
    struct jpeg_error_mgr* jpeg_std_error (struct jpeg_error_mgr* err);

    // jpeglib
    void    jpeg_mem_src               (j_decompress_ptr,
                                        unsigned char * inbuffer,
                                        unsigned long insize);
    void     jpeg_create_decompress    (j_decompress_ptr);
    boolean     jpeg_finish_decompress    (j_decompress_ptr);
    void     jpeg_destroy_decompress   (j_decompress_ptr);
    void    jpeg_mem_dest              (j_compress_ptr,
                                        unsigned char ** outbuffer,
                                        unsigned long * outsize);
    void     jpeg_create_compress      (j_compress_ptr);
    void     jpeg_finish_compress      (j_compress_ptr);
    void     jpeg_destroy_compress     (j_compress_ptr);

    // transupp
    typedef enum {
        JCOPYOPT_NONE,
        JCOPYOPT_COMMENTS,
        JCOPYOPT_ALL
    } JCOPY_OPTION;
    void     jcopy_markers_setup       (j_decompress_ptr, JCOPY_OPTION);
    void     jcopy_markers_execute     (j_decompress_ptr,
                                        j_compress_ptr, JCOPY_OPTION);
    int      jpeg_read_header          (j_decompress_ptr, boolean);
    jvirt_barray_ptr* jpeg_read_coefficients (j_decompress_ptr);
    void     jpeg_write_coefficients   (j_compress_ptr,
                                        jvirt_barray_ptr*);
    void     jpeg_copy_critical_parameters (j_decompress_ptr,
                                            j_compress_ptr);
    boolean     jtransform_request_workspace (j_decompress_ptr,
                                            jpeg_transform_info*);
    jvirt_barray_ptr* jtransform_adjust_parameters (j_decompress_ptr,
                                                    j_compress_ptr,
                                                    jvirt_barray_ptr*,
                                                    jpeg_transform_info*);
    void     jtransform_execute_transform (j_decompress_ptr,
                                            j_compress_ptr,
                                            jvirt_barray_ptr*,
                                            jpeg_transform_info*);
    """)

    libjpeg = ffi.verify("""
    #include "jconfig.h"
    #include "jmorecfg.h"
    #include "jpeglib.h"
    #include "transupp.h"
    #include "jerror.h"
    """, sources=["src/transupp.c"],
        include_dirs=["src"],
        libraries=["jpeg"])
    ffi_jpeg = ffi
    JPEG8 = True


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
        if not '>' in fmt and not '<' in fmt:
            fmt = ('>' if self._motorola else '<')+fmt
        if PY2:
            return struct.unpack_from(fmt, buffer(self._buf), offset)[0]
        else:
            return struct.unpack_from(fmt, self._buf, offset)[0]

    def _pack(self, fmt, offset, value):
        if not '>' in fmt and not '<' in fmt:
            fmt = ('>' if self._motorola else '<')+fmt
        struct.pack_into(fmt, self._buf, offset, value)


def _jpeg8_cleanup(buffer):
    libjpeg.free(buffer[0])


def jpegtran_op_jpeg8(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Setup variables
        in_data_len = len(self._data)
        in_data_p = ffi_jpeg.new("unsigned char[]", in_data_len)
        inbuf = ffi_jpeg.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data
        srcerr = ffi_jpeg.new("struct jpeg_error_mgr*")
        dsterr = ffi_jpeg.new("struct jpeg_error_mgr*")
        out_data_p = ffi_jpeg.gc(ffi_jpeg.new("unsigned char**"),
                                 _jpeg8_cleanup)
        out_data_len = ffi_jpeg.new("unsigned long*")
        srcinfo = ffi_jpeg.new("struct jpeg_decompress_struct*")
        srcinfo.err = libjpeg.jpeg_std_error(srcerr)
        dstinfo = ffi_jpeg.new("struct jpeg_compress_struct*")
        dstinfo.err = libjpeg.jpeg_std_error(dsterr)

        # Read input
        libjpeg.jpeg_create_decompress(srcinfo)
        libjpeg.jpeg_create_compress(dstinfo)
        libjpeg.jpeg_mem_src(srcinfo, in_data_p,
                             ffi_jpeg.cast("unsigned long", in_data_len))
        libjpeg.jcopy_markers_setup(srcinfo, libjpeg.JCOPYOPT_ALL)
        libjpeg.jpeg_read_header(srcinfo, int(True))

        # Call the wrapped function with the transformoption struct
        transformoption = func(self, *args, **kwargs)

        # Prepare transformation
        libjpeg.jtransform_request_workspace(srcinfo, transformoption)
        src_coefs = libjpeg.jpeg_read_coefficients(srcinfo)
        libjpeg.jpeg_copy_critical_parameters(srcinfo, dstinfo)
        dst_coefs = libjpeg.jtransform_adjust_parameters(
            srcinfo, dstinfo, src_coefs, transformoption
        )
        libjpeg.jpeg_mem_dest(dstinfo, out_data_p, out_data_len)
        libjpeg.jpeg_write_coefficients(dstinfo, dst_coefs)
        libjpeg.jcopy_markers_execute(srcinfo, dstinfo, libjpeg.JCOPYOPT_ALL)

        # Execute transformation
        libjpeg.jtransform_execute_transform(srcinfo, dstinfo, src_coefs,
                                             transformoption)

        # Clean up
        libjpeg.jpeg_finish_compress(dstinfo)
        libjpeg.jpeg_destroy_compress(dstinfo)
        libjpeg.jpeg_finish_decompress(srcinfo)
        libjpeg.jpeg_destroy_decompress(srcinfo)

        # Return output data
        _weak_keydict[out_data_p[0]] = out_data_p
        return bytearray(ffi_jpeg.buffer(out_data_p[0], out_data_len[0])[:])
    return wrapper


def _turbojpeg_cleanup(buffers):
    libjpeg.tjFree(buffers[0])


def jpegtran_op_turbojpeg(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Setup variables
        in_data_len = len(self._data)
        in_data_p = ffi_jpeg.new("unsigned char[]", in_data_len)
        inbuf = ffi_jpeg.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data

        out_bufs = ffi_jpeg.gc(ffi_jpeg.new("unsigned char**"), _turbojpeg_cleanup)
        out_bufs[0] = ffi_jpeg.NULL
        out_sizes = ffi_jpeg.new("unsigned long*")

        tjhandle = ffi_jpeg.gc(libjpeg.tjInitTransform(), libjpeg.tjDestroy)

        # Call the wrapped function with the transformoption struct
        transformoption = func(self, *args, **kwargs)

        # Execute transformation
        rv = libjpeg.tjTransform(tjhandle, in_data_p, in_data_len, 1,
                                 out_bufs, out_sizes, transformoption, 0)
        if rv < 0:
            raise Exception("Transformation failed: {0}"
                            .format(ffi_jpeg.string(libjpeg.tjGetErrorStr())))

        _weak_keydict[out_bufs[0]] = out_bufs
        return bytearray(ffi_jpeg.buffer(out_bufs[0], out_sizes[0])[:])
    return wrapper


def _epeg_free_buffer(buffer):
    libepeg.free(buffer[0])


class BaseTransformation(object):
    def __init__(self, blob):
        self._data = blob


    def get_dimensions(self):
        width = ffi_epeg.new("int*")
        height = ffi_epeg.new("int*")
        in_data_len = len(self._data)
        in_data_p = ffi_epeg.new("unsigned char[]", in_data_len)
        inbuf = ffi_epeg.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data
        img = ffi_epeg.gc(libepeg.epeg_memory_open(in_data_p, in_data_len), libepeg.epeg_close)
        libepeg.epeg_size_get(img, width, height)
        return (width[0], height[0])

    def scale(self, width, height, quality=75):
        in_data_len = len(self._data)
        in_data_p = ffi_epeg.new("unsigned char[]", in_data_len)
        inbuf = ffi_epeg.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data
        img = ffi_epeg.gc(libepeg.epeg_memory_open(in_data_p, in_data_len), libepeg.epeg_close)
        libepeg.epeg_decode_size_set(img, width, height)
        libepeg.epeg_quality_set(img, quality)

        pdata = ffi_epeg.gc(ffi_epeg.new("unsigned char **"), _epeg_free_buffer)
        psize = ffi_epeg.new("int*")
        libepeg.epeg_memory_output_set(img, pdata, psize)
        libepeg.epeg_encode(img)

        _weak_keydict[pdata[0]] = pdata
        return bytearray(ffi_epeg.buffer(pdata[0], psize[0])[:])


class TransformationJpeg8(BaseTransformation):
    def _get_transformoptions(self):
        # Initialize jpeg_transform_info struct
        options = ffi_jpeg.new("jpeg_transform_info*")
        options.transform = libjpeg.JXFORM_NONE
        options.perfect = int(False)
        options.trim = int(False)
        options.force_grayscale = int(False)
        options.crop = int(False)
        return options

    @jpegtran_op_jpeg8
    def grayscale(self):
        options = self._get_transformoptions()
        options.transform = libjpeg.JXFORM_NONE
        options.force_grayscale = int(True)
        return options

    @jpegtran_op_jpeg8
    def rotate(self, angle, perfect=False, trim=False):
        options = self._get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        if angle == 90:
            options.transform = libjpeg.JXFORM_ROT_90
        elif angle == 180:
            options.transform = libjpeg.JXFORM_ROT_180
        elif angle in (-90, 270):
            options.transform = libjpeg.JXFORM_ROT_270
        else:
            raise ValueError("Invalid angle, must be -90, 90, 180 or 270")
        return options

    @jpegtran_op_jpeg8
    def flip(self, direction, perfect=False, trim=False):
        options = self._get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        if direction == 'vertical':
            options.transform = libjpeg.JXFORM_FLIP_V
        elif direction == 'horizontal':
            options.transform = libjpeg.JXFORM_FLIP_H
        else:
            raise ValueError("Invalid direction, must be 'vertical' or "
                             "'horizontal'")
        return options

    @jpegtran_op_jpeg8
    def transpose(self, perfect=False, trim=False):
        options = self._get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        options.transform = libjpeg.JXFORM_TRANSPOSE
        return options

    @jpegtran_op_jpeg8
    def transverse(self, perfect=False, trim=False):
        options = self._get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        options.transform = libjpeg.JXFORM_TRANSVERSE
        return options

    @jpegtran_op_jpeg8
    def crop(self, x, y, width, height, perfect=False, trim=False):
        options = self._get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        options.crop = int(True)
        options.crop_width = width
        options.crop_width_set = libjpeg.JCROP_FORCE
        options.crop_height = height
        options.crop_height_set = libjpeg.JCROP_FORCE
        options.crop_xoffset = x
        options.crop_xoffset_set = libjpeg.JCROP_POS
        options.crop_yoffset = y
        options.crop_yoffset_set = libjpeg.JCROP_POS
        return options


class TransformationTurboJpeg(BaseTransformation):
    def _get_transformoptions(self, perfect=False, trim=False):
        # Initialize jpeg_transform_info struct
        options = ffi_jpeg.new("tjtransform*")
        options.op = libjpeg.TJXOP_NONE
        options.options = 0
        if perfect:
            options.options |= libjpeg.TJXOPT_PERFECT
        if trim:
            options.options |= libjpeg.TJXOPT_TRIM
        return options

    @jpegtran_op_turbojpeg
    def grayscale(self):
        options = self._get_transformoptions()
        options.options = libjpeg.TJXOPT_GRAY
        return options

    @jpegtran_op_turbojpeg
    def rotate(self, angle):
        options = self._get_transformoptions()
        if angle == 90:
            options.op = libjpeg.TJXOP_ROT90
        elif angle == 180:
            options.op = libjpeg.TJXOP_ROT180
        elif angle in (-90, 270):
            options.op = libjpeg.TJXOP_ROT270
        else:
            raise ValueError("Invalid angle, must be -90, 90, 180 or 270")
        return options

    @jpegtran_op_turbojpeg
    def flip(self, direction):
        options = self._get_transformoptions()
        if direction == 'vertical':
            options.op = libjpeg.TJXOP_VFLIP
        elif direction == 'horizontal':
            options.op = libjpeg.TJXOP_HFLIP
        else:
            raise ValueError("Invalid direction, must be 'vertical' or "
                             "'horizontal'")
        return options

    @jpegtran_op_turbojpeg
    def transpose(self):
        options = self._get_transformoptions()
        options.op = libjpeg.TJXOP_TRANSPOSE
        return options

    @jpegtran_op_turbojpeg
    def transverse(self):
        options = self._get_transformoptions()
        options.op = libjpeg.TJXOP_TRANSVERSE
        return options

    @jpegtran_op_turbojpeg
    def crop(self, x, y, width, height):
        options = self._get_transformoptions()
        options.r = ffi_jpeg.new("tjregion*")[0]
        options.r.w = width
        options.r.h = height
        options.r.x = x
        options.r.y = y
        options.options = libjpeg.TJXOPT_CROP
        return options

Transformation = None
if JPEG8:
    Transformation = TransformationJpeg8
elif TURBOJPEG:
    Transformation = TransformationTurboJpeg
else:
    raise OSError("Neither jpeg8 or turbojpeg transformators could be"
                  "initialized, make sure you have either of them installed.")
