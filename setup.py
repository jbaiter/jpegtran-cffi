import os
import sys
from setuptools import setup


if os.path.exists('README.rst'):
    if sys.version_info > (3,):
        long_description = open('README.rst', encoding="utf-8").read()
    else:
        long_description = open('README.rst').read()
else:
    long_description = """
A Python package for blazingly fast JPEG transformations. Compared to other,
more general purpose image processing libraries like `wand-py`_  or
`PIL/Pillow`_, the performance gain can, depending on the transformation, be
somewhere in the range of 150% to 500% (see *Benchmarks*). In addition to
that, all operations except for scaling are lossless, since the image is not
being re-compressed in the process. This is due to the fact that all
transformation operations work directly with the JPEG data.
"""

setup(
    name='jpegtran-cffi',
    version="0.5.3.dev",
    description=("Extremly fast, (mostly) lossless JPEG transformations"),
    long_description=long_description,
    author="Johannes Baiter",
    url="http://github.com/jbaiter/jpegtran-cffi.git",
    author_email="johannes.baiter@gmail.com",
    license='MIT',
    packages=['jpegtran'],
    package_data={'jpegtran': ['jpegtran.cdef']},
    install_requires=['cffi >= 1.0'],
    cffi_modules=["jpegtran/jpegtran_build.py:ffi"]
)
