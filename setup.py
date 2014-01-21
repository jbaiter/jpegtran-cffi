from setuptools import setup

import jpegtran.lib

setup(
    name='jpegtran-cffi',
    version="0.01",
    description=("Very fast lossless (except for scaling) JPEG "
                 "transformations"),
    author="Johannes Baiter",
    url="http://github.com/jbaiter/jpegtran-cffi.git",
    author_email="johannes.baiter@gmail.com",
    license='MIT',
    packages=['jpegtran'],
    zip_safe=False,
    ext_modules=[jpegtran.lib.ffi.verifier.get_extension()],
    install_requires=['cffi >= 0.8.1']
)
