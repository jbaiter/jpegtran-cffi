yum makecache
yum -y install nasm
python -m pip install -U pip wheel
python -m pip install -U cmake
mkdir binaries
cd binaries
cmake -G"Unix Makefiles" ../libjpeg-turbo
make
cd ..
ls binaries
