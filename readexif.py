#!/usr/bin/env python3

import os
import re
import sys
import time
from datetime import datetime

import exifread


def progress(message):
    sys.stdout.write(message)
    sys.stdout.flush()

def usage_and_exit():
    print("Usage: fixdates <directory>")
    sys.exit(1)


class File:

    @classmethod
    def factory(cls, path):
        if re.match(r'.*\.(jpg|jpeg)', os.path.basename(path), re.IGNORECASE):
            return FileSupportingExif(path)
        else:
            return cls(path)

    def __init__(self, path):
        self.path = path
        self.fname = os.path.basename(path)

    def mtime(self):  # timestamp
        return os.path.getmtime(self.path)

    def metadata_mtime_timestamp(self):
        raise RuntimeError(f"UNRECOGNIZED TYPE")


class FileSupportingExif(File):

    def metadata_mtime_timestamp(self):
        return self.exif_mtime_timestamp()

    def exif_mtime_timestamp(self):
        tags = self.get_exif_data(self.path)
        if 'EXIF DateTimeOriginal' not in tags:
            raise RuntimeError("EXIF DateTimeOriginal missing from JPEG")

        mtime_datetime = datetime.strptime(str(tags['EXIF DateTimeOriginal']), '%Y:%m:%d %H:%M:%S')
        return time.mktime(mtime_datetime.timetuple())

    def get_exif_data(self, file_path):
        with open(file_path, 'rb') as f:
            # print(f"tags = {tags} ({len(tags)})")
            # for tag in tags.keys():
            #     if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            #         print("Key: %s, value %s" % (tag, tags[tag]))
            return exifread.process_file(f, details=False)


class FixTimesInDirectoryTree:

    def __init__(self, basepath):
        if not os.path.isdir(basepath):
            usage_and_exit()
        self.walk_tree(basepath)

    def walk_tree(self, basepath):
        for dirName, subdirList, fileList in os.walk(basepath):
            progress(f'Found directory: {dirName}\n')
            for fname in fileList:
                progress(f"\t{fname}: ")
                file_path = os.path.join(dirName, fname)
                file = File.factory(file_path)
                try:
                    self.check_file(file)
                except RuntimeError as e:
                    print(str(e))

    def check_file(self, file):
        metadata_mtime = file.metadata_mtime_timestamp()
        file_mtime_timestamp = os.path.getmtime(file.path)

        if metadata_mtime == file_mtime_timestamp:
            progress(" SAME\n")
        else:
            progress(f" {metadata_mtime} vs {file_mtime_timestamp} UPDATE\n")


def set_file_times(path: str, when: datetime):
    print(f"Setting {path} mtime to {when}")
    epoch = time.mktime(when.timetuple())
    os.utime(path, (epoch, epoch))


if len(sys.argv) != 2:
    usage_and_exit()
else:
    FixTimesInDirectoryTree(sys.argv[1])
