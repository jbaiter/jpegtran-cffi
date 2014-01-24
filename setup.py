import os
from setuptools import setup

import jpegtran.lib

if os.path.exists('README.rst'):
    description_long = open('README.rst').read()
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
    version="0.3.1",
    description=("Extremly fast, (mostly) lossless JPEG transformations"),
    description_long=description_long,
    author="Johannes Baiter",
    url="http://github.com/jbaiter/jpegtran-cffi.git",
    author_email="johannes.baiter@gmail.com",
    license='MIT',
    packages=['jpegtran'],
    zip_safe=False,
    ext_modules=[jpegtran.lib.ffi.verifier.get_extension()],
    install_requires=['cffi >= 0.8.1']
)
