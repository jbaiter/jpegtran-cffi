import os
import sys
from setuptools import setup


if os.path.exists('README.rst'):
    description_long = open('README.rst', encoding="utf-8").read()
else:
    description_long = """
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
    version="0.6a1",
    description=("Extremly fast, (mostly) lossless JPEG transformations"),
    description_long=description_long,
    author="Johannes Baiter",
    url="http://github.com/jbaiter/jpegtran-cffi.git",
    author_email="johannes.baiter@gmail.com",
    license='MIT',
    python_requires=">=3.5",
    packages=['jpegtran'],
    package_data={'jpegtran': ['jpegtran.cdef']},
    setup_requires=['cffi >= 1.0'],
    install_requires=['cffi >= 1.0'],
    cffi_modules=["jpegtran/jpegtran_build.py:ffi"]
)
