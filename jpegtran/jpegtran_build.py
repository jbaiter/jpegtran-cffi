import os

from cffi import FFI

with open(os.path.join(os.path.dirname(__file__), 'jpegtran.cdef')) as fp:
    CDEF = fp.read()

SOURCE = """
#include "Epeg.h"
#include "epeg_private.h"
#include "jpeglib.h"
#include "turbojpeg.h"
"""

ffi = FFI()
ffi.set_source(
    "_jpegtran", SOURCE,
    sources=["src/epeg.c"],
    include_dirs=["src"],
    define_macros=[("HAVE_UNSIGNED_CHAR", "1")],
    libraries=["jpeg", "turbojpeg"])
ffi.cdef(CDEF)

if __name__ == "__main__":
    ffi.compile()
