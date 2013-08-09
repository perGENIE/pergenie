# -*- coding: utf-8 -*-

import csv
import re


class VCFParseError(Exception):
    def __init__(self, error_code):
        self.error_code = error_code
    def __str__(self):
        return repr(self.error_code)


class VCFParser(object):
    def __init__(self, fin):
        self.handle = fin
        self.delimiter = '\t'

        # Parse header-lines
        for line in self.handle:
            line = line.rstrip()

            if line.startswith('##'):
                pass
            elif line.startswith('#CHROM'):
                line = line.replace('#CHROM', 'CHROM')
                self.fieldnames = line.split(self.delimiter)
                break
            else:
                raise VCFParseError, 'Header-lines seem invalid. `#CHROM ...` does not exists.'

        # Determine sample-names
        if self.fieldnames[0:9] != ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT']:
            raise VCFParseError, 'Header-lines seem invalid. Probably delimiter is not tab.'
        else:
            self.sample_names = self.fieldnames[9:]

    def parse_lines(self):
        data = {}
        for record in csv.DictReader(self.handle,
                                     fieldnames=self.fieldnames,
                                     delimiter=self.delimiter):

            data['chrom'] = _chrom(record['CHROM'])
            data['pos'] = _integer(record['POS'])
            data['ID'] = _string(record['ID'])
            data['rs'] = _rsid(record['ID'])

            data['REF'] = _string(record['REF'])
            data['ALT'] = _alt(record['ALT'])
            data['genotype'] = {}

            data['QUAL'] = _string(record['QUAL'])
            data['FILTER'] = _string(record['FILTER'])
            data['INFO'] = _string(record['INFO'])

            format_keys = record['FORMAT'].split(':')
            for sample in self.sample_names:
                data[sample] = dict(zip(format_keys, record[sample].split(':')))

                # add `genotype` like 'GG'
                data['genotype'][sample] = _GT2genotype(data['REF'],
                                                        data['ALT'],
                                                        data[sample]['GT'])

            yield data


def _integer(text):
    return int(text)


def _string(text):
    return text

def _chrom(text):
    if text.startswith('chr'):
        text = text.replace('chr', '')

    if text in [str(i+1) for i in range(22)] + ['X', 'Y', 'MT', 'M']:
        return text
    else:
        return None

def _alt(text):
    """
    >>> _alt('G,T,A')
    ['G', 'T', 'A']
    """
    alt = text.split(',')
    return alt


def _rsid(text):
    """
    >>> _rsid('rs100')
    100
    """

    # TODO: simply split by `;` maybe buggy ...
    rs_raw = text.split(';')[0]  # case: rs100;rs123

    rs_regex = re.compile('rs(\d+)')
    rs_match = rs_regex.match(rs_raw)

    if rs_match:
        rsid = rs_match.group(1)
    else:
        return None

    try:
        return int(rsid)
    except ValueError:
        return None


def _GT2genotype(REF, ALT, GT):
    """parse GT (GenoType) in Genotype fields.

    >>> REF = 'G'
    >>> ALT = ['A']
    >>> GT = '0|0'
    >>> _GT2genotype(REF, ALT, GT)
    'GG'
    """

    # / : genotype unphased
    # | : genotype phased

    g1, g2 = re.split('/|\|', GT)

    # 0 : reference allele (what is in the REF field)
    # 1 : first allele listed in ALT
    # 2 : second allele list in ALT
    # and so on.

    bases = [REF] + ALT

    genotype = bases[int(g1)] + bases[int(g2)]

    return genotype


if __name__=='__main__':
    import doctest
    doctest.testmod()
