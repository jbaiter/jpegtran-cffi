import re

import lib


class JPEGImage(object):
    def __init__(self, fname=None, blob=None):
        if (not fname and not blob) or (fname and blob):
            raise Exception("Must initialize with either fname or blob.")
        if fname is not None:
            with open(fname, 'rb') as fp:
                self.data = bytearray(fp.read())
        elif blob is not None:
            self.data = bytearray(blob)

    @property
    def width(self):
        return lib.Transformation(self.data).get_dimensions()[0]

    @property
    def height(self):
        return lib.Transformation(self.data).get_dimensions()[1]

    @property
    def exif_thumbnail(self):
        return lib.Exif(self.data).thumbnail

    @property
    def exif_orientation(self):
        return lib.Exif(self.data).orientation

    @exif_orientation.setter
    def exif_orientation(self, value):
        if not 0 < value < 9:
            raise ValueError("Orientation value must be between 1 and 8")
        lib.Exif(self.data).orientation = value

    def exif_autotransform(self):
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
        if angle % 90:
            raise ValueError("angle must be a multiple of 90.")
        self.data = lib.Transformation(self.data).rotate(angle)
        # Set EXIF orientation to 'Normal' (== no rotation)
        lib.Exif(self.data).orientation = 1
        return self

    def flip(self, direction):
        if direction not in ('horizontal', 'vertical'):
            raise ValueError("direction must be either 'vertical' or "
                             "'horizontal'")
        self.data = lib.Transformation(self.data).flip(direction)
        return self

    def transpose(self):
        self.data = lib.Transformation(self.data).transpose()
        return self

    def transverse(self):
        self.data = lib.Transformation(self.data).transverse()
        return self

    def crop(self, x, y, width, height):
        self.data = lib.Transformation(self.data).crop(x, y, width, height)
        return self

    def downscale(self, width, height, quality=75):
        if width > self.width or height > self.height:
            raise ValueError("jpegtran can only downscale JPEGs")
        self.data = lib.Transformation(self.data).scale(width, height, quality)
        return self

    def save(self, fname):
        if not re.match(r'^.*\.jp[e]*g$', fname.lower()):
            raise ValueError("fname must refer to a JPEG file, i.e. end with "
                             "'.jpg' or '.jpeg'")
        with open(fname, 'w') as fp:
            fp.write(self.data)

    def as_blob(self):
        return self.data
