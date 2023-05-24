import urllib.request
from argparse import ArgumentParser
from pathlib import Path
from zipfile import ZipFile

urls = {
    "amd64": "https://www.nasm.us/pub/nasm/releasebuilds/2.14.02/win64/nasm-2.14.02-win64.zip",
    "x86": "https://www.nasm.us/pub/nasm/releasebuilds/2.14.02/win32/nasm-2.14.02-win32.zip",
}


def main():
    parser = ArgumentParser()
    parser.add_argument("arch", type=str.lower, choices=urls.keys())
    parser.add_argument("--zip-name", default="nasm.zip")
    args = parser.parse_args()

    url = urls[args.arch]
    urllib.request.urlretrieve(url, args.zip_name)

    with ZipFile(args.zip_name, "r") as zip:
        zip.extractall()

    assert Path("nasm-2.14.02").exists()


if __name__ == "__main__":
    main()
