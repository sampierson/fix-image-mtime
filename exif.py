#!/usr/bin/env python3

import argparse
import os
import re
import sys
import time
from datetime import datetime

import exifread


def progress(message):
    sys.stdout.write(message)
    sys.stdout.flush()


class File:

    @classmethod
    def factory(cls, path, debug=False):
        if re.match(r'.*\.(jpg|jpeg)', os.path.basename(path), re.IGNORECASE):
            return FileSupportingExif(path, debug)
        else:
            return cls(path, debug)

    def __init__(self, path, debug=False):
        self.path = path
        self.fname = os.path.basename(path)
        self.debug = debug

    def mtime(self):  # timestamp
        return os.path.getmtime(self.path)

    def set_mtime(self, timestamp):
        print(f"Setting {self.path} mtime to {timestamp}")
        # epoch = time.mktime(when.timetuple())
        os.utime(self.path, (timestamp, timestamp))

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
            tags = exifread.process_file(f, details=False)
            if self.debug:
                print(f"{file_path}:")
                for tag in tags.keys():
                    if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                        print("\tKey: %s, value %s" % (tag, tags[tag]))
            return tags


class ExifFixer:

    def __init__(self, fix, dump):
        self.fix = fix
        self.dump = dump

    def walk_tree(self, basepath):
        for dirName, subdirList, fileList in os.walk(basepath):
            progress(f'Found directory: {dirName}\n')
            for fname in fileList:
                progress(f"\t{fname}: ")
                file_path = os.path.join(dirName, fname)
                file = File.factory(file_path, self.dump)
                try:
                    self.check_file(file)
                except RuntimeError as e:
                    print(str(e))

    def check_file(self, file):
        metadata_mtime = file.metadata_mtime_timestamp()
        file_mtime_timestamp = os.path.getmtime(file.path)

        progress(f"{file.path}\t{metadata_mtime}\t{file_mtime_timestamp}")
        if metadata_mtime == file_mtime_timestamp:
            progress("\tSAME\n")
        else:
            if self.fix:
                progress(f"\tUPDATED\n")
                file.set_mtime(metadata_mtime)
            else:
                progress("\tDIFFERENT\n")


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fix', action='store_true', help="change file mtime to match Exif mtime")
parser.add_argument('-d', '--dump', action='store_true', help="dump metadata")
parser.add_argument('files_and_dirs', type=str, nargs='+')
args = vars(parser.parse_args())

fixer = ExifFixer(args['fix'], args['dump'])
for path in args['files_and_dirs']:
    if os.path.isdir(path):
        fixer.walk_tree(path)
    else:
        fixer.check_file(File.factory(path, args['dump']))
