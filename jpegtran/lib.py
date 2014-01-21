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
#include "jpeglib.h"
#include "cdjpeg.h"
#include "transupp.h"
#include "jerror.h"
""", sources=["src/epeg.c", "src/transupp.c", "src/cdjpeg.c"],
    include_dirs=["src"],
    libraries=["jpeg"])


class Transformation(object):
    def __init__(self, blob):
        self.in_data_p = ffi.new("unsigned char[]", len(blob))
        inbuf = ffi.buffer(self.in_data_p, len(blob))
        inbuf[:] = blob
        self.in_data_len = len(inbuf)

    def _prepare(self):
        self.srcerr = ffi.new("struct jpeg_error_mgr*")
        self.dsterr = ffi.new("struct jpeg_error_mgr*")
        self.out_data_p = ffi.new("unsigned char**")
        self.out_data_len = ffi.new("unsigned long*")
        self.srcinfo = ffi.new("struct jpeg_decompress_struct*")
        self.srcinfo.err = lib.jpeg_std_error(self.srcerr)
        self.dstinfo = ffi.new("struct jpeg_compress_struct*")
        self.dstinfo.err = lib.jpeg_std_error(self.dsterr)
        self.transformoption = ffi.new("jpeg_transform_info*")
        self.transformoption.transform = lib.JXFORM_NONE
        self.transformoption.perfect = int(False)
        self.transformoption.trim = int(False)
        self.transformoption.force_grayscale = int(False)
        self.transformoption.crop = int(False)
        lib.jpeg_create_decompress(self.srcinfo)
        lib.jpeg_create_compress(self.dstinfo)
        lib.jpeg_mem_src(self.srcinfo, self.in_data_p,
                         ffi.cast("unsigned long", self.in_data_len))
        lib.jcopy_markers_setup(self.srcinfo, lib.JCOPYOPT_COMMENTS)
        lib.jpeg_read_header(self.srcinfo, int(True))

    def _transform(self, perfect=False, trim=False):
        #import ipdb; ipdb.set_trace()
        self.transformoption.perfect = int(perfect)
        self.transformoption.trim = int(trim)
        lib.jtransform_request_workspace(self.srcinfo, self.transformoption)
        self.src_coefs = lib.jpeg_read_coefficients(self.srcinfo)
        lib.jpeg_copy_critical_parameters(self.srcinfo, self.dstinfo)
        self.dst_coefs = lib.jtransform_adjust_parameters(
            self.srcinfo, self.dstinfo, self.src_coefs, self.transformoption
        )
        lib.jpeg_mem_dest(self.dstinfo, self.out_data_p, self.out_data_len)
        lib.jpeg_write_coefficients(self.dstinfo, self.dst_coefs)
        lib.jcopy_markers_execute(self.srcinfo, self.dstinfo,
                                  lib.JCOPYOPT_COMMENTS)
        lib.jtransform_execute_transform(self.srcinfo, self.dstinfo,
                                         self.src_coefs,
                                         self.transformoption)
        lib.jpeg_finish_compress(self.dstinfo)
        lib.jpeg_destroy_compress(self.dstinfo)
        lib.jpeg_finish_decompress(self.srcinfo)
        lib.jpeg_destroy_decompress(self.srcinfo)
        return ffi.buffer(self.out_data_p[0], self.out_data_len[0])[:]

    def grayscale(self):
        self._prepare()
        self.transformoption.transform = lib.JXFORM_NONE
        self.transformoption.force_grayscale = int(True)
        return self._transform()

    def rotate(self, angle, perfect=False, trim=False):
        self._prepare()
        if angle == 90:
            self.transformoption.transform = lib.JXFORM_ROT_90
        elif angle == 180:
            self.transformoption.transform = lib.JXFORM_ROT_180
        elif angle in (-90, 270):
            self.transformoption.transform = lib.JXFORM_ROT_270
        else:
            raise ValueError("Invalid angle, must be -90, 90, 180 or 2170")
        return self._transform(perfect, trim)

    def flip(self, direction, perfect=False, trim=False):
        self._prepare()
        if direction == 'vertical':
            self.transformoption.transform = lib.JXFORM_FLIP_V
        elif direction == 'horizontal':
            self.transformoption.transform = lib.JXFORM_FLIP_H
        else:
            raise ValueError("Invalid direction, must be 'vertical' or "
                             "'horizontal'")
        return self._transform(perfect, trim)

    def transpose(self, perfect=False, trim=False):
        self._prepare()
        self.transformoption.transform = lib.JXFORM_TRANSPOSE
        return self._transform(perfect, trim)

    def transverse(self, perfect=False, trim=False):
        self._prepare()
        self.transformoption.transform = lib.JXFORM_TRANSVERSE
        return self._transform(perfect, trim)

    def crop(self, x, y, width, height, perfect=False, trim=False):
        self._prepare()
        self.transformoption.crop = int(True)
        self.transformoption.crop_width = width
        self.transformoption.crop_width_set = lib.JCROP_FORCE
        self.transformoption.crop_height = height
        self.transformoption.crop_height_set = lib.JCROP_FORCE
        self.transformoption.crop_xoffset = x
        self.transformoption.crop_xoffset_set = lib.JCROP_POS
        self.transformoption.crop_yoffset = y
        self.transformoption.crop_yoffset_set = lib.JCROP_POS
        return self._transform(perfect, trim)

    def scale(self, width, height, quality=75):
        img = lib.epeg_memory_open(self.in_data_p, self.in_data_len)
        lib.epeg_decode_size_set(img, width, height)
        lib.epeg_quality_set(img, quality)

        pdata = ffi.new("unsigned char **")
        psize = ffi.new("int*")
        lib.epeg_memory_output_set(img, pdata, psize)
        lib.epeg_encode(img)
        lib.epeg_close(img)
        return ffi.buffer(pdata[0], psize[0])[:]
