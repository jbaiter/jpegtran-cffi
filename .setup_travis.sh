#!/bin/bash
if [ $JPEGLIB -eq "jpeg8" ]; then
    apt-get -y remove libjpeg-turbo8-dev
    apt-get -y install libjpeg8-dev
elif [ $JPEGLIB -eq "turbojpeg" ]; then
    apt-get -y remove libjpeg8-dev
    apt-get -y install libjpeg-turbo8-dev
fi
