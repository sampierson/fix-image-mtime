#!/usr/bin/env python3

import argparse
import os
import re
import sys
import json
import time
from datetime import datetime

import exifread
# import pyheif


class NoTimestampInsideFileMetadata(RuntimeError):
    pass


def progress(message):
    sys.stdout.write(message)
    sys.stdout.flush()


class File:

    @classmethod
    def factory(cls, path, debug=False):
        if re.match(r'.*\.(jpg|jpeg)$', os.path.basename(path), re.IGNORECASE):
            return FileSupportingExif(path, debug)
        # if re.match(r'.*\.(heic)$', os.path.basename(path), re.IGNORECASE):
        #     return HeicFile(path, debug)
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
        raise RuntimeWarning(f"UNRECOGNIZED TYPE")


class FileSupportingExif(File):

    def metadata_mtime_timestamp(self):
        return self.exif_mtime_timestamp()

    def exif_mtime_timestamp(self):
        tags = self.get_exif_data(self.path)
        if 'EXIF DateTimeOriginal' not in tags:
            print(f"WARNING: {self.path}: EXIF DateTimeOriginal missing from JPEG")
            return None
        try:
            mtime_datetime = datetime.strptime(str(tags['EXIF DateTimeOriginal']), '%Y:%m:%d %H:%M:%S')
        except ValueError as e:
            print(f"WARNING: {self.path}: {str(e)}")
            return None

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


# class HeicFile(File):
#     def metadata_mtime_timestamp(self):
#         x = pyheif.read_heif(self.path)
#         print(x.metadata)
#         import pdb ; pdb.set_trace()
#         raise RuntimeError("not done yet")


class ExifFixer:

    def __init__(self, fix, dump, verbose):
        self.fix = fix
        self.dump = dump
        self.verbose = verbose

    def walk_tree(self, basepath):
        for dirName, subdirList, fileList in os.walk(basepath):
            if self.verbose:
                progress(f'Found directory: {dirName}\n')
            for fname in fileList:
                file_path = os.path.join(dirName, fname)
                file = File.factory(file_path, self.dump)
                try:
                    self.check_file(file)
                except RuntimeWarning as w:
                    if self.verbose:
                        print("WARNING: " + str(w))
                except RuntimeError as e:
                    print("ERROR: " + str(e))

    def check_file(self, file):
        file_mtime_timestamp = os.path.getmtime(file.path)
        metadata_mtime = file.metadata_mtime_timestamp() or self.google_takeout_json_timestamp(file)
        if metadata_mtime is None:
            raise RuntimeError(f"no metadata source date for {file.path}")

        commentary = f"\t{file.path}\t{metadata_mtime}\t{file_mtime_timestamp}"

        if metadata_mtime == file_mtime_timestamp:
            if self.verbose:
                progress(f"{commentary}\tSAME\n")
        else:
            if self.fix:
                progress(f"{commentary}\tUPDATED\n")
                file.set_mtime(metadata_mtime)
            else:
                progress(f"{commentary}\tDIFFERENT\n")

    def google_takeout_json_timestamp(self, file):
        # Google Takeout manouver
        # See if there is a .json file with the data we need
        json_file_path = file.path + ".json"
        if os.path.isfile(json_file_path):
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                return int(data['photoTakenTime']['timestamp'])
        else:
            return None


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--fix', action='store_true', help="change file mtime to match Exif mtime")
parser.add_argument('-d', '--dump', action='store_true', help="dump metadata")
parser.add_argument('-v', '--verbose', action='store_true', help="more details")
parser.add_argument('files_and_dirs', type=str, nargs='+')
args = vars(parser.parse_args())

fixer = ExifFixer(args['fix'], args['dump'], args['verbose'])
for path in args['files_and_dirs']:
    if os.path.isdir(path):
        fixer.walk_tree(path)
    else:
        fixer.check_file(File.factory(path, args['dump']))
