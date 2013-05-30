#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pymongo

path_to_regulomedb = '/Users/numa/Dropbox/py/perGENIE/pergenie/data/large_dbs/regulomedb/RegulomeDB.dbSNP132.Category1.txt'


def import_regulomedb():
    print >>sys.stderr, 'Importing ...'

    with pymongo.MongoClient() as c:
        db = c['pergenie']
        regulomedb = db['regulomedb']

        # Ensure old collections does not exist
        if regulomedb.find_one():
            db.drop_collection(regulomedb)
            assert regulomedb.count() == 0

        with open(path_to_regulomedb, 'rb') as fin:
            for line in fin:
                chrom, pos, rs, anotation, score = line.strip().split('\t')

                chrom = chrom.replace('chr', '')
                assert (chrom in [str(i+1) for i in range(22)] + ['X', 'Y'])  # no MT ?

                assert rs.startswith('rs')
                rs = int(rs.replace('rs', ''))

                anotation = anotation.split(',')

                record = dict(chrom=chrom, pos=int(pos), rs=rs, anotation=anotation, score=score)

                regulomedb.insert(record)

        print >>sys.stderr, 'count:', regulomedb.count()

        print >>sys.stderr, 'Creating indices...'
        regulomedb.create_index([('rs', pymongo.ASCENDING)])
        regulomedb.create_index([('chrom', pymongo.ASCENDING), ('pos', pymongo.ASCENDING)])

    print >>sys.stderr, 'done.'

if __name__ == '__main__':
    import_regulomedb()
