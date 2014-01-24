=============
jpegtran-cffi
=============
.. image:: https://travis-ci.org/jbaiter/jpegtran-cffi.png?branch=master
   :target: https://travis-ci.org/jbaiter/jpegtran-cffi
   :alt: Build status

A Python package for blazingly fast JPEG transformations. Compared to other,
more general purpose image processing libraries like `wand-py`_  or
`PIL/Pillow`_, the performance gain can, depending on the transformation, be
somewhere in the range of 80% to 375% (see *Benchmarks*). In addition to
that, all operations except for scaling are lossless, since the image is not
being re-compressed in the process. This is due to the fact that all
transformation operations work directly with the JPEG data.

This is achieved by using multiple C routines from Carsten Haitzler's `epeg`_
(scaling) and *jpegtran* from the Independent JPEG Group's `libjpeg` library
(for all other operations). These routines are called from Python through the
`CFFI` library, i.e. no external commands are launched via `subprocess`.

The package also includes rudimentary support for getting and setting the EXIF
orientation tag, automatically transforming the image according to it and
obtaining the JFIF thumbnail image.

.. _wand-py: http://wand-py.org
.. _PIL/PIllow: http://pillow.readthedocs.org
.. _epeg: https://github.com/mattes/epeg
.. _libjpeg: http://en.wikipedia.org/wiki/Libjpeg

Requirements
============
- cffi
- libjpeg8 with headers (earlier versions will not work)

Installation
============
Via pip::

    $ pip install jpegtran-cffi

From source::

    $ pip install cffi  # cffi has to be installed before running setup.py
    $ python setup.py install

Usage
=====
Before each transformation, you have to create a ``JPEGImage`` object. This can
be either initialized with a filename (``fname``) or a bytestring or bytearray
with the JPEG data (``blob``).

On the resulting object, the following transformations are supported:

``rotate(angle)``
    Rotate by -90, 90, 180 or 270 degrees. If the image has an EXIF orientation
    tag, it will automatically be set to ``1`` (i.e no rotation) in the
    resulting image.

``flip(direction)``
    Flip either in ``vertical`` or ``horizontal`` direction

``transpose()``
    "Tranpose" the image

``transverse()``
    "Transverse" the image

``crop(x, y, width, height)``
    Crop a rectangle with ``width`` and ``height`` starting from ``x`` pixels
    on the right and ``y`` pixels from the top

``exif_autotransform()``
    Automatically transform the image according to its EXIF orientation tag.
    This will apply one or more of the above methods to transform the image so
    its image data corresponds to the tag value. In the resulting image,  the
    tag will be set to ``1``.

``downscale(width, height, quality=75)``
    Resize the image to ``width`` by ``height`` pixels. Since this is a lossy
    operation, the optional ``quality`` parameter can be used to set the JPEG
    quality of the output. Note that this method can only be used to downscale
    images, upscaling is not supported.


The result of each of these operations retuns a new ``JPEGImage`` object with
the transformed data. You can get the data as a bytestring via the
``as_blob()`` method or save it to a file with the ``save(fname)`` method.

Note that this allows operations to be chained, e.g. to create a
rectangular 200x200 thumbnail from a 1200x2400 pixel JPEG::

    thumb_data = (JPEGImage(fname='original.jpg')
                      .scale(200, 400)
                      .crop(0, 100, 200, 200)
                      .as_blob())

Example Output
==============
.. figure:: http://i.imgur.com/30LlkLu.jpg
    :alt: wand-py thumbnail

    Wand-Py ``Image.sample(200, 150)``, filtering was nearest neighbour

.. figure:: http://i.imgur.com/Jnv46jx.jpg
    :alt: PIL thumbnail

    PIL ``Image.resize((200, 150))``

.. figure:: http://i.imgur.com/pnW9QaE.jpg
    :alt: jpegtran-cffi thumbnail

    jpegtran-cffi ``JPEGImage.scale(200, 150, quality=75)``

http://imgur.com/a/JvAtM


Benchmarks
==========
All operations were done on the following 2560x1920 8bit RGB JPEG:
http://upload.wikimedia.org/wikipedia/commons/8/82/Mandel_zoom_05_tail_part.jpg

Machine specs:

- CPU: 4x i7-3770@3.40GHz
- RAM: 16GB
- Storage: 7200rpm HDD

Package versions:

- PIL/Pillow: 2.3.0
- wand-py: 0.3.5
- jpegtran-cffi: 0.1

+-----------------------+------------+-----------+---------------+
|       Operation       |  wand-py   |    PIL    | jpegtran-cffi |
+=======================+============+===========+===============+
|   scale to 250x150    | 102ms/200% | 90ms/165% |     34ms      |
+-----------------------+------------+-----------+---------------+
|   rotate by 90° CW    | 317ms/124% | 258ms/82% |     141ms     |
+-----------------------+------------+-----------+---------------+
| Crop 500x500 from 0,0 | 190ms/375% | 92ms/130% |     40ms      |
+-----------------------+------------+-----------+---------------+

Both wand-py and PIL were run with the fastest scaling algorithm available, for
wand-py this meant using ``Image.sample`` instead of ``Image.resize`` and for
PIL the nearest-neighbour filter was used for the ``Image.resize`` call.


License
=======
The MIT License (MIT)

Copyright (c) 2014 Johannes Baiter <johannes.baiter@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
