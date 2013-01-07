# -*- coding: utf-8 -*-

import os

try:
   import cPickle as pickle
except ImportError:
   import pickle

import pyPdf


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


def get_url_content(url, dst):
    """Get content form url"""
    
    # TODO: error handling
    urllib.urlretrieve(url, dst)


def get_pdf_content(path):
    """Get PDF-content from .pdf
    
    ref: http://code.activestate.com/recipes/511465/
    """

    content = []

    pdf = pyPdf.PdfFileReader(file(path, "rb"))
    for i in range(0, pdf.getNumPages()):
        content.append(pdf.getPage(i).extractText())

    return content

