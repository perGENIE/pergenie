# -*- coding: utf-8 -*-

import urllib
import sys

def get_catalog(url, dst):
    """Get latest gwascatalog.txt from NHGRI's web site
    """
    
    # if not url:
    #     url = 'http://www.genome.gov/admin/gwascatalog.txt'

    print >>sys.stderr, '[INFO] Getting from {} ...'.format(url)
    
    # TODO: error handling
    urllib.urlretrieve(url, dst)
