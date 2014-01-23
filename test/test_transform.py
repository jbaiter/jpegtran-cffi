import pytest

from jpegtran import JPEGImage


@pytest.fixture
def image():
    with open('test/test.jpg', 'rb') as fp:
        return JPEGImage(blob=fp.read())


def test_get_dimensions(image):
    assert image.width == 480
    assert image.height == 360


def test_get_orientation(image):
    assert image.exif_orientation == 1


def test_set_orientation(image):
    image.exif_orientation = 6
    assert image.exif_orientation == 6


def test_get_exif_thumbnail(image):
    thumb = JPEGImage(blob=image.exif_thumbnail)
    assert thumb.width == 160
    assert thumb.height == 120


def test_exif_autotransform(image):
    image.exif_orientation = 6
    transformed = image.exif_autotransform()
    assert transformed.width == image.height
    assert transformed.height == image.width


def test_rotate(image):
    assert image.rotate(90).height == image.width
    assert image.rotate(180).height == image.height
    assert image.rotate(-90).height == image.width


def test_flip(image):
    flipped = image.flip('vertical')
    assert flipped.height == image.height
    assert flipped.as_blob() != image.as_blob()
    flipped = image.flip('horizontal')
    assert flipped.width == image.width
    assert flipped.as_blob() != image.as_blob()


def test_transpose(image):
    transposed = image.transpose()
    assert transposed.height == image.width
    assert transposed.as_blob() != image.as_blob()


def test_transverse(image):
    transversed = image.transverse()
    assert transversed.height == image.width
    assert transversed.as_blob() != image.as_blob()


def test_crop(image):
    cropped = image.crop(0, 0, 125, 125)
    assert cropped.width == 125
    assert cropped.height == 125


def test_downscale(image):
    scaled = image.downscale(240, 180)
    assert scaled.width == 240
    assert scaled.height == 180
