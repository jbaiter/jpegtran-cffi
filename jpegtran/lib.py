import struct
import sys
from functools import wraps

PY2 = sys.version_info < (3, 0)
if PY2:
    range = xrange

from cffi import FFI
ffi = FFI()

ffi.cdef("""
   // epeg
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

   // jpegtran
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

lib = ffi.verify("""
#include "Epeg.h"
#include "epeg_private.h"
#include "jmorecfg.h"
#include "jpeglib.h"
#include "cdjpeg.h"
#include "transupp.h"
#include "jerror.h"
""", sources=["src/epeg.c", "src/transupp.c", "src/cdjpeg.c"],
    include_dirs=["src"],
    libraries=["jpeg"])


class InvalidExifData(Exception):
    pass


class ExifTagNotFound(Exception):
    pass


class Exif(object):
    def __init__(self, blob):
        self._buf = blob
        # EXIF struct starts after APP1 marker (2 bytes) and size (2 bytes)
        header = self._buf.index(b'\xff\xe1')+4
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
        compression = self._unpack('H', self._get_tag_offset(0x103)+8)
        if compression != 6:
            raise ValueError("Image does not contain a JPEG thumbnail")
        offset = (self._exif_start +
                  self._unpack('I', self._get_tag_offset(0x201)+8))
        size = self._unpack('I', self._get_tag_offset(0x202)+8)
        return self._buf[offset:offset+size]

    def _get_tag_offset(self, tagnum):
        # IFD0 pointer starts after alignment (2 bytes) and tag mark (2 bytes)
        p_ifd = self._unpack('I', self._exif_start+4)+self._exif_start
        while True:
            num_entries = self._unpack('H', p_ifd)
            # Start after number of entries (2 bytes)
            idx = p_ifd + 2
            for _ in range(num_entries):
                tag_num = self._unpack('H', idx)
                # Check if we're at the orientation tag
                if tag_num == tagnum:
                    return idx
                idx += 12
            p_ifd = self._unpack('I', idx)+self._exif_start
            if not p_ifd:
                raise ExifTagNotFound("Could not find EXIF Tag {0}"
                                      .format(tagnum))

    def _thumbnail_offset(self):
        # Number of entries is 2 bytes, each entry is 12 bytes
        ifd0_len = 2+self._unpack('H', self._ifd0)*12
        ifd1 = self._unpack('I', self._ifd0+ifd0_len)+self._exif_start
        num_entries = self._unpack('H', ifd1)
        # Start after number of entries (2 bytes)
        idx = ifd1+2
        for _ in range(num_entries):
            tag_num = self._unpack('H', idx)
            if tag_num == 0x103:
                return idx
            idx += 12

    def _unpack(self, fmt, offset):
        fmt = ('>' if self._motorola else '<')+fmt
        if PY2:
            return struct.unpack_from(fmt, buffer(self._buf), offset)[0]
        else:
            return struct.unpack_from(fmt, self._buf, offset)[0]

    def _pack(self, fmt, offset, value):
        fmt = ('>' if self._motorola else '<')+fmt
        struct.pack_into(fmt, self._buf, offset, value)


def get_transformoptions():
    # Initialize jpeg_transform_info struct
    options = ffi.new("jpeg_transform_info*")
    options.transform = lib.JXFORM_NONE
    options.perfect = int(False)
    options.trim = int(False)
    options.force_grayscale = int(False)
    options.crop = int(False)
    return options


def jpegtran_op(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Setup variables
        in_data_len = len(self._data)
        in_data_p = ffi.new("unsigned char[]", in_data_len)
        inbuf = ffi.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data
        srcerr = ffi.new("struct jpeg_error_mgr*")
        dsterr = ffi.new("struct jpeg_error_mgr*")
        out_data_p = ffi.new("unsigned char**")
        out_data_len = ffi.new("unsigned long*")
        srcinfo = ffi.new("struct jpeg_decompress_struct*")
        srcinfo.err = lib.jpeg_std_error(srcerr)
        dstinfo = ffi.new("struct jpeg_compress_struct*")
        dstinfo.err = lib.jpeg_std_error(dsterr)

        # Read input
        lib.jpeg_create_decompress(srcinfo)
        lib.jpeg_create_compress(dstinfo)
        lib.jpeg_mem_src(srcinfo, in_data_p,
                         ffi.cast("unsigned long", in_data_len))
        lib.jcopy_markers_setup(srcinfo, lib.JCOPYOPT_ALL)
        lib.jpeg_read_header(srcinfo, int(True))

        # Call the wrapped function with the transformoption struct
        transformoption = func(self, *args, **kwargs)

        # Prepare transformation
        lib.jtransform_request_workspace(srcinfo, transformoption)
        src_coefs = lib.jpeg_read_coefficients(srcinfo)
        lib.jpeg_copy_critical_parameters(srcinfo, dstinfo)
        dst_coefs = lib.jtransform_adjust_parameters(
            srcinfo, dstinfo, src_coefs, transformoption
        )
        lib.jpeg_mem_dest(dstinfo, out_data_p, out_data_len)
        lib.jpeg_write_coefficients(dstinfo, dst_coefs)
        lib.jcopy_markers_execute(srcinfo, dstinfo, lib.JCOPYOPT_ALL)

        # Execute transformation
        lib.jtransform_execute_transform(srcinfo, dstinfo, src_coefs,
                                         transformoption)

        # Clean up
        lib.jpeg_finish_compress(dstinfo)
        lib.jpeg_destroy_compress(dstinfo)
        lib.jpeg_finish_decompress(srcinfo)
        lib.jpeg_destroy_decompress(srcinfo)

        # Return output data
        return bytearray(ffi.buffer(out_data_p[0], out_data_len[0])[:])
    return wrapper


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
        img = lib.epeg_memory_open(in_data_p, in_data_len)
        lib.epeg_size_get(img, width, height)
        lib.epeg_close(img)
        return (width[0], height[0])

    @jpegtran_op
    def grayscale(self):
        options = get_transformoptions()
        options.transform = lib.JXFORM_NONE
        options.force_grayscale = int(True)
        return options

    @jpegtran_op
    def rotate(self, angle, perfect=False, trim=False):
        options = get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        if angle == 90:
            options.transform = lib.JXFORM_ROT_90
        elif angle == 180:
            options.transform = lib.JXFORM_ROT_180
        elif angle in (-90, 270):
            options.transform = lib.JXFORM_ROT_270
        else:
            raise ValueError("Invalid angle, must be -90, 90, 180 or 270")
        return options

    @jpegtran_op
    def flip(self, direction, perfect=False, trim=False):
        options = get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        if direction == 'vertical':
            options.transform = lib.JXFORM_FLIP_V
        elif direction == 'horizontal':
            options.transform = lib.JXFORM_FLIP_H
        else:
            raise ValueError("Invalid direction, must be 'vertical' or "
                             "'horizontal'")
        return options

    @jpegtran_op
    def transpose(self, perfect=False, trim=False):
        options = get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        options.transform = lib.JXFORM_TRANSPOSE
        return options

    @jpegtran_op
    def transverse(self, perfect=False, trim=False):
        options = get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        options.transform = lib.JXFORM_TRANSVERSE
        return options

    @jpegtran_op
    def crop(self, x, y, width, height, perfect=False, trim=False):
        options = get_transformoptions()
        options.perfect = int(perfect)
        options.trim = int(trim)
        options.crop = int(True)
        options.crop_width = width
        options.crop_width_set = lib.JCROP_FORCE
        options.crop_height = height
        options.crop_height_set = lib.JCROP_FORCE
        options.crop_xoffset = x
        options.crop_xoffset_set = lib.JCROP_POS
        options.crop_yoffset = y
        options.crop_yoffset_set = lib.JCROP_POS
        return options

    def scale(self, width, height, quality=75):
        in_data_len = len(self._data)
        in_data_p = ffi.new("unsigned char[]", in_data_len)
        inbuf = ffi.buffer(in_data_p, in_data_len)
        inbuf[:] = self._data
        img = lib.epeg_memory_open(in_data_p, in_data_len)
        lib.epeg_decode_size_set(img, width, height)
        lib.epeg_quality_set(img, quality)

        pdata = ffi.new("unsigned char **")
        psize = ffi.new("int*")
        lib.epeg_memory_output_set(img, pdata, psize)
        lib.epeg_encode(img)
        lib.epeg_close(img)
        return bytearray(ffi.buffer(pdata[0], psize[0])[:])
