import hashlib
import jpegtran

def get_img():
    return jpegtran.JPEGImage(fname='lenna.jpg')

def get_sha1(jpgimg):
    return hashlib.sha1(jpgimg.as_blob()).hexdigest()

assert get_sha1(get_img().rotate(90)) == "2220b32db6543d9d9c0f02ea36a19681e4aba497"
assert get_sha1(get_img().rotate(-90)) == "6e0aaca41d7976cd0f06c0292147151832073139"
assert get_sha1(get_img().rotate(180)) == "1ec52d179137a5d44736c1cfc71cee465e2f4c8c"
assert get_sha1(get_img().rotate(270)) == "6e0aaca41d7976cd0f06c0292147151832073139"
assert get_sha1(get_img().flip('vertical')) == "00c863cb45ad2cc3310a4046520167e929804b7f"
assert get_sha1(get_img().flip('horizontal')) == "6601a9221fd341fe1c0d933f3bbbe9fa6d9f638e"
assert get_sha1(get_img().transpose()) == "5dcba374296c5dbf76e1bf5242c04cd31cc573d3"
assert get_sha1(get_img().transverse()) == "c9ab0acee34471473de959c3d82dc0fa9cf5bd8c"
assert get_sha1(get_img().crop(0, 0, 256, 256)) == "2d2fdd87865887a16f47dd6d184746cc77d9e82c"
