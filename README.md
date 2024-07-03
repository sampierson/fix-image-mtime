# Exif

Tool to fix file mtimes to match Exif metadata `DateTimeOriginal`.

## Setup

```shell script
brew install pyenv pyenv-virtualenv
pyenv install 3.9.0
pyenv virtualenv 3.9.0 fix-image-mtime
pip install -r requirements.txt
```

## Running

```shell script
./exif.py tmp/*.jpg
./exif.py --fix tmp/*.jpg
```

## WIP Add HEIC Support

Found a potential library to parse HEIC files : pyheif.
Looks like EXIF information is embedded inside HEIC tags, need a way to parse it out.
Perhaps crack open ExifRead and use one of its methods.
