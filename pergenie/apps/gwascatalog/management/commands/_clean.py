# -*- coding: utf-8 -*-

def clean_catalog(source, destination):
    """Clean up gwascatalog.
    """

    with open(destination, 'w') as fout:
        with open(source) as fin:
            for source_line in fin:
                source_line = source_line.strip()
                dest_line = ''.join([c if 0 <= ord(c) <= 128 else ' ' for c in source_line])

                print >>fout, dest_line
