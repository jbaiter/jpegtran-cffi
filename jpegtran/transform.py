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
        self._width = None
        self._height = None

    @property
    def width(self):
        if self._width is None:
            self._width, self._height = (lib.Transformation(self.data)
                                         .get_dimensions())
        return self._width

    @property
    def height(self):
        if self._height is None:
            self._width, self._height = (lib.Transformation(self.data)
        return self._height

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

    def scale(self, width, height, quality=75):
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
