# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import time
import urllib
import hashlib
import socket
socket.setdefaulttimeout(30)  # timeout for urlretrieve
try:
    import cPickle as pickle
except ImportError:
    import pickle

from lib.utils import clogging
log = clogging.getColorLogger(__name__)


def pickle_dump_obj(obj, fout_name):
    with open(fout_name, 'wb') as fout:
        pickle.dump(obj, fout, protocol=2)


def pickle_load_obj(fin_name):
    with open(fin_name, 'rb') as fin:
        obj = pickle.load(fin)
    return obj


def touch(filename, times=None):
    """Touch <filename>"""

    with file(filename, 'a'):
        os.utime(filename, times)


def get_url_content(url, dst, if_not_exists=False, md5=''):
    """Get content form url"""

    if if_not_exists and os.path.exists(dst):
        log.info('Already exists.')
        return

    # TODO: error handling
    while True:
        urllib.urlretrieve(url, dst, reporthook=reporthook)
        if is_finished:
            sys.stdout.write("\n")
            break

    if md5:
        assert md5 == md5_checksum(dst)


def md5_checksum(filename):
    """Returns md5 checksum of a file

    http://stackoverflow.com/a/3431838
    """

    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()


def reporthook(count, block_size, total_size):
    global start_time
    global is_finished
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                     (percent, progress_size / (1024 * 1024), speed, duration))
    sys.stdout.flush()
    is_finished = count * block_size >= total_size


# try:
#     import pyPdf

#     def get_pdf_content(path):
#         """Get PDF-content from .pdf

#         ref: http://code.activestate.com/recipes/511465/
#         """

#         content = []

#         pdf = pyPdf.PdfFileReader(file(path, "rb"))
#         for i in range(0, pdf.getNumPages()):
#             content.append(pdf.getPage(i).extractText())

#         return content

# except ImportError:
#     pass

class cd:
    def __init__(self, newPath):
        self.newPath = newPath

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def count_file_lines(file_path):
    cmd = ['wc', '-l', file_path]
    lines = int(subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].split()[0])
    return lines
