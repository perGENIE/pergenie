#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pymongo

path_to_23adnme_snps = '/Users/numa/Dropbox/py/perGENIE/pergenie/data/large_dbs/23andme-api/snps.data'  # FIX to path of yours.


def import_23andme_snps():
    print >>sys.stderr, 'Importing 23andMe SNPs...'

    with pymongo.MongoClient() as c:
        db = c['pergenie']
        andme_snps = db['andme_snps']

        # Ensure old collections does not exist
        if andme_snps.find_one():
            db.drop_collection(andme_snps)
            assert andme_snps.count() == 0

        with open(path_to_23adnme_snps, 'rb') as fin:
            for line in fin:
                # Skip header lines
                if line.startswith('#'): continue
                if line.startswith('index'): continue

                index, snp, chrom, pos = line.strip().split('\t')
                rs = int(snp.replace('rs', '')) if snp.startswith('rs') else None

                # Insert record as {'index': 0, , 'snp': 'rs41362547', 'rs': 41362547, 'chrom': 'MT', 'pos': 10044}
                record = dict(index=int(index), snp=snp, rs=rs, chrom=chrom, pos=int(pos))
                andme_snps.insert(record)

        print >>sys.stderr, 'count: {}'.format(andme_snps.count())

        print >>sys.stderr, 'Creating indices...'
        andme_snps.create_index([('index', pymongo.ASCENDING)])
        andme_snps.create_index([('rs', pymongo.ASCENDING)])
        # andme_snps.create_index([('chrom', pymongo.ASCENDING), ('pos', pymongo.ASCENDING)])

    print >>sys.stderr, 'done.'

if __name__ == '__main__':
    import_23andme_snps()
