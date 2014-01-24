=============
jpegtran-cffi
=============
.. image:: https://travis-ci.org/jbaiter/jpegtran-cffi.png?branch=master
   :target: https://travis-ci.org/jbaiter/jpegtran-cffi
   :alt: Build status

jpegtran-cffi is a Python package for fast JPEG transformations.  Compared to
other, more general purpose image processing libraries like `wand-py`_  or
`PIL/Pillow`_, transformations are generally more than twice as fast (see
`Benchmarks`_). In addition, all operations except for scaling are lossless,
since the image is not being re-compressed in the process. This is due to the
fact that all transformation operations work directly with the JPEG data.

This is achieved by using multiple C routines from the Enlightenment project's
`epeg library`_ (for scaling) and *jpegtran* from the Independent JPEG Group's
`libjpeg`_ library (for all other operations). These routines are called from
Python through the `CFFI`_ module, i.e. no external processes are launched.

The package also includes rudimentary support for getting and setting the EXIF
orientation tag, automatically transforming the image according to it and
obtaining the JFIF thumbnail image.

jpegtran-cffi was developed as part of a web interface for the `spreads`_
project, where a large number of images from digital cameras had to be prepared
for display by a Raspberry Pi. With the Pi's rather slow ARMv6 processor, both
Wand and PIL were too slow to be usable.

.. _wand-py: http://wand-py.org
.. _PIL/PIllow: http://pillow.readthedocs.org
.. _Benchmarks: http://jpegtran-cffi.readthedocs.org/en/latest/#benchmarks
.. _epeg library: https://github.com/mattes/epeg
.. _libjpeg: http://en.wikipedia.org/wiki/Libjpeg
.. _CFFI: http://cffi.readthedocs.orgs
.. _spreads: http://spreads.readthedocs.org

Requirements
============
- CPython 2.6, 2.7, 3.3 or PyPy
- cffi
- libjpeg8 with headers (earlier versions will not work)

Installation
============

::

    $ pip install jpegtran-cffi

Usage
=====
::

    from jpegtran import JPEGImage

    img = JPEGImage('image.jpg')

    # JPEGImage can also be initialized from a bytestring
    blob = requests.get("http://example.com/image.jpg").content
    from_blob = JPEGImage(blob=blob)

    # Reading various image parameters
    print img.width, img.height  # "640 480"
    print img.exif_orientation  # "1" (= "normal")

    # If present, the JFIF thumbnail can be obtained as a bytestring
    thumb = img.exif_thumbnail

    # Transforming the image
    img.scale(320, 240).save('scaled.jpg')
    img.rotate(90).save('rotated.jpg')
    img.crop(0, 0, 100, 100).save('cropped.jpg')

    # Transformations can be chained
    data = (img.scale(320, 240)
                .rotate(90)
                .flip('horizontal')
                .as_blob())

    # jpegtran can transform the image automatically according to the EXIF
    # orientation tag
    photo = JPEGImage(blob=requests.get("http://example.com/photo.jpg").content)
    print photo.orientation  # "6" (= 270°)
    print photo.width, photo.height # "4320 3240"
    corrected = photo.exif_autotransform()
    print corrected.orientation  # "1" (= "normal")
    print corrected.width, corrected.height  # "3240 4320"


For more details, refer to the `API Reference`_.

.. _API Reference: http://jpegtran-cffi.readthedocs.org/en/latest/#api-reference

License
=======
The MIT License (MIT)

Copyright (c) 2014 Johannes Baiter <johannes.baiter@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
