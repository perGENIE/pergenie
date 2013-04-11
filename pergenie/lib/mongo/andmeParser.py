# -*- coding: utf-8 -*-

import csv
import re


class andmeParseError(Exception):
    def __init__(self, error_code):
        self.error_code = error_code
    def __str__(self):
        return repr(self.error_code)


class andmeParser(object):
    def __init__(self, fin):
        self.handle = fin
        self.delimiter = '\t'

        self.ref_genome_version = None

        # Parse header-lines
        for line in self.handle:
            line = line.rstrip()

            # Determine reference genome version
            if 'build 36' in line:
                self.ref_genome_version = 'b36'
            elif 'build 37' in line:
                self.ref_genome_version = 'b37'

            #
            if line.startswith('# rsid'):
                line = line.replace('# rsid', 'rsid')
                self.fieldnames = line.split(self.delimiter)
                break
            elif line.startswith('#'):
                pass
            else:
                raise andmeParseError, 'Header-lines seem invalid. `# rsid ...` does not exists.'

        if self.fieldnames != ['rsid', 'chromosome', 'position', 'genotype']:
            raise andmeParseError, 'Header-lines seem invalid. Probably delimiter is not tab.'

        if not self.ref_genome_version:
            raise andmeParseError, 'Could not determine reference-genome version from header-lines.'


    def parse_lines(self):
        data = {}
        for record in csv.DictReader(self.handle,
                                     fieldnames=self.fieldnames,
                                     delimiter=self.delimiter):

            data['id'] = _string(record['rsid'])
            data['rs'] = _rsid(record['rsid'])

            data['chrom'] = _string(record['chromosome'])
            data['pos'] = _integer(record['position'])
            data['genotype'] = _string(record['genotype'])

            yield data


def _integer(text):
    return int(text)

def _string(text):
    return text

def _rsid(text):
    """
    >>> _rsid('rs100')
    100
    """

    # TODO: simply split by `;` maybe buggy ...
    rs_raw = text.split(';')[0]  # case: rs100;rs123

    rs_regex = re.compile('rs(\d+)')
    rsid = rs_regex.match(rs_raw).group(1)

    try:
        return int(rsid)
    except ValueError:
        return None


if __name__=='__main__':
    import doctest
    doctest.testmod()
