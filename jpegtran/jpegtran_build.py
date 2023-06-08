import os
import shutil

from cffi import FFI

with open(os.path.join(os.path.dirname(__file__), 'jpegtran.cdef')) as fp:
    CDEF = fp.read()

SOURCE = """
#include "Epeg.h"
#include "epeg_private.h"
#include "jpeglib.h"
#include "turbojpeg.h"
"""

include_dirs = ["src"]
library_dirs = []

jpegtran = shutil.which("jpegtran")

if jpegtran:
    prefix = os.path.dirname(os.path.dirname(jpegtran))
    include_dirs.append(os.path.join(prefix, "include"))
    library_dirs.append(os.path.join(prefix, "lib"))

ffi = FFI()
ffi.set_source(
    "_jpegtran", SOURCE,
    sources=["src/epeg.c"],
    include_dirs=include_dirs,
    define_macros=[("HAVE_UNSIGNED_CHAR", "1")],
    libraries=["jpeg", "turbojpeg"],
    library_dirs=library_dirs)
ffi.cdef(CDEF)

if __name__ == "__main__":
    ffi.compile()
