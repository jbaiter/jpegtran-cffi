import re

import jpegtran.lib as lib


class JPEGImage(object):
    def __init__(self, fname=None, blob=None):
        """ Initialize the image with either a filename or a string or
        bytearray containing the JPEG image data.

        :param fname:   Filename of JPEG file
        :type fname:    str
        :param blob:    JPEG image data
        :type blob:     str/bytearray

        """
        if (not fname and not blob) or (fname and blob):
            raise Exception("Must initialize with either fname or blob.")
        if fname is not None:
            with open(fname, 'rb') as fp:
                self.data = bytearray(fp.read())
        elif blob is not None:
            self.data = bytearray(blob)

    @property
    def width(self):
        """ Width of the image in pixels. """
        return lib.Transformation(self.data).get_dimensions()[0]

    @property
    def height(self):
        """ Height of the image in pixels. """
        return lib.Transformation(self.data).get_dimensions()[1]

    @property
    def exif_thumbnail(self):
        """ EXIF thumbnail.

        :return:  EXIF thumbnail in JPEG format
        :rtype:   str

        """
        try:
            return lib.Exif(self.data).thumbnail
        except (ValueError, lib.ExifTagNotFound, lib.InvalidExifData):
            return None

    @property
    def exif_orientation(self):
        """ Exif orientation value as a number between 1 and 8.

        Property is read/write
        """
        try:
            return lib.Exif(self.data).orientation
        except (lib.ExifTagNotFound, lib.InvalidExifData):
            return None

    @exif_orientation.setter
    def exif_orientation(self, value):
        if not 0 < value < 9:
            raise ValueError("Orientation value must be between 1 and 8")
        lib.Exif(self.data).orientation = value

    def exif_autotransform(self):
        """ Automatically transform the image according to its EXIF orientation
        tag.

        :return:  transformed image
        :rtype:   jpegtran.JPEGImage

        """
        orient = self.exif_orientation
        if orient is None:
            raise Exception("Could not find EXIF orientation")
        elif orient == 1:
            return self
        elif orient == 2:
            return self.flip('horizontal')
        elif orient == 3:
            return self.rotate(180)
        elif orient == 4:
            return self.flip('vertical')
        elif orient == 5:
            return self.transpose()
        elif orient == 6:
            return self.rotate(90)
        elif orient == 7:
            return self.transverse()
        elif orient == 8:
            return self.rotate(270)

    def rotate(self, angle):
        """ Rotate the image.

        :param angle:   rotation angle
        :type angle:    -90, 90, 180 or 270
        :return:        rotated image
        :rtype:         jpegtran.JPEGImage

        """
        if angle not in (-90, 90, 180, 270):
            raise ValueError("Angle must be -90, 90, 180 or 270.")
        img = JPEGImage(blob=lib.Transformation(self.data).rotate(angle))
        # Set EXIF orientation to 'Normal' (== no rotation)
        lib.Exif(img.data).orientation = 1
        return img

    def flip(self, direction):
        """ Flip the image in horizontal or vertical direction.

        :param direction: Flipping direction
        :type direction:  'vertical' or 'horizontal'
        :return:        flipped image
        :rtype:         jpegtran.JPEGImage

        """
        if direction not in ('horizontal', 'vertical'):
            raise ValueError("Direction must be either 'vertical' or "
                             "'horizontal'")
        return JPEGImage(blob=lib.Transformation(self.data).flip(direction))

    def transpose(self):
        """ Transpose the image (across  upper-right -> lower-left axis)

        :return:        transposed image
        :rtype:         jpegtran.JPEGImage

        """
        return JPEGImage(blob=lib.Transformation(self.data).transpose())

    def transverse(self):
        """ Transverse transpose the image (across  upper-left -> lower-right
        axis)

        :return:        transverse transposed image
        :rtype:         jpegtran.JPEGImage

        """
        return JPEGImage(blob=lib.Transformation(self.data).transverse())

    def crop(self, x, y, width, height):
        """ Crop a rectangular area from the image.

        :param x:       horizontal coordinate of upper-left corner
        :type x:        int
        :param y:       vertical coordinate of upper-left corner
        :type y:        int
        :param width:   width of area
        :type width.    int
        :param height:  height of area
        :type height:   int
        :return:        cropped image
        :rtype:         jpegtran.JPEGImage

        """
        valid_crop = (x < self.width and y < self.height and
                      x+width < self.width and y+height < self.height)
        if not valid_crop:
            raise ValueError("Crop parameters point outside of the image")
        return JPEGImage(blob=lib.Transformation(self.data)
                         .crop(x, y, width, height))

    def downscale(self, width, height, quality=75):
        """ Downscale the image.

        :param width:   Scaled image width
        :type width:    int
        :param height:  Scaled image height
        :type height:   int
        :param quality: JPEG quality of scaled image (default: 75)
        :type quality:  int
        :return:        downscaled image
        :rtype:         jpegtran.JPEGImage

        """
        if width > self.width or height > self.height:
            raise ValueError("jpegtran can only downscale JPEGs")
        return JPEGImage(blob=lib.Transformation(self.data)
                         .scale(width, height, quality))

    def save(self, fname):
        """ Save the image to a file

        :param fname:   Path to file
        :type fname:    unicode

        """
        if not re.match(r'^.*\.jp[e]*g$', fname.lower()):
            raise ValueError("fname must refer to a JPEG file, i.e. end with "
                             "'.jpg' or '.jpeg'")
        with open(fname, 'w') as fp:
            fp.write(self.data)

    def as_blob(self):
        """ Get the image data as a string

        :return:    Image data
        :rtype:     str

        """
        return str(self.data)
