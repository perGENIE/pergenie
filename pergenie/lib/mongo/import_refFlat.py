#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pymongo

def import_refFlat(path_to_refFlat, MONGO_URI="mongodb://localhost:27017"):
    """
    refFlat:

    string  geneName;           "Name of gene as it appears in Genome Browser."
    string  name;               "Name of gene"
    string  chrom;              "Chromosome name"
    char[1] strand;             "+ or - for strand"
    uint    txStart;            "Transcription start position"
    uint    txEnd;              "Transcription end position"
    uint    cdsStart;           "Coding region start"
    uint    cdsEnd;             "Coding region end"
    uint    exonCount;          "Number of exons"
    uint[exonCount] exonStarts; "Exon start positions"
    uint[exonCount] exonEnds;   "Exon end positions"
    """

    print >>sys.stderr, 'Importing refFlat...'

    with pymongo.MongoClient(host=MONGO_URI) as c:
        db = c['pergenie']
        refFlat = db['refFlat']

        # Ensure old collections does not exist
        if refFlat.find_one():
            db.drop_collection(refFlat)
            assert refFlat.count() == 0

        fields = [('gene', _string),
                  ('gene_id', _string),
                  ('chrom', _chrom),
                  ('strand', _strand),
                  ('txStart', _integer),
                  ('txEnd', _integer),
                  ('cdsStart', _integer),
                  ('cdsEnd', _integer),
                  ('exonCount', _integer),
                  ('exonStarts', _integers),
                  ('exonEnds', _integers)]

        with open(path_to_refFlat, 'rb') as fin:
            for line in fin:
                raw_record =  line.strip().split('\t')
                record = dict()

                for i, (field, _type) in enumerate(fields):
                    record[field] = _type(raw_record[i])

                assert len(record['exonStarts']) == len(record['exonEnds'])

                refFlat.insert(record)

        print >>sys.stderr, 'count: {0}'.format(refFlat.count())

        print >>sys.stderr, 'Creating indices...'
        refFlat.create_index([('gene', pymongo.ASCENDING)])
        refFlat.create_index([('chrom', pymongo.ASCENDING), ('txStart', pymongo.ASCENDING), ('txEnd', pymongo.ASCENDING)])

    print >>sys.stderr, 'done.'

def _string(s):
    return s

def _integer(s):
    return int(s)

def _integers(s):
    return [int(x) for x in s.split(',') if x]

def _chrom(s):
    chrom = s.replace('chr', '')
    if not chrom in [str(i+1) for i in range(22)] + ['X', 'Y']:
        print >>sys.stderr, 'chrom?', s

    return chrom

def _strand(s):
    assert s in ['+', '-']
    return s


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >>sys.stderr, """USAGE: {0} /path/to/refFlat.txt

        refFlat.txt for hg19 is available at:
        http://hgdownload.cse.ucsc.edu/goldenPath/hg19/database/refFlat.txt.gz""".format(sys.argv[0])
        sys.exit()
    import_refFlat(sys.argv[1])
