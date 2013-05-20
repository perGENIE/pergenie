# -*- coding: utf-8 -*-

import sys, os
from pymongo import MongoClient, ASCENDING, ASCENDING

def import_strand_db(path_to_reference_dir, port=27017):
    """Import Genotyping chips strand files.

    * This function is independent from Django.
    * source: http://www.well.ox.ac.uk/~wrayner/strand/

      * Illumina: `HumanOmni2.5M-b37-v2.strand`

      ```
      GA008510 Y 13311305 100 + AG
      ```

      * Affymetrix: `GenomewideSNP_6.na31-b37-strand.txt`

      ```
      SNP_A-1780419 rs6576700 1 84875173 -
      ```

      * Perlegen:

    """

    with MongoClient(port=port) as c:
        db = c['strand_db']
        venders = ['Affymetrix', 'Illumina', 'Perlegen']

        for vender in venders:
            if db[vender].find_one(): db.drop_collection(vender)
            assert db[vender].count() == 0

        # Affymetrix
        with open(os.path.join(path_to_reference_dir, 'GenomewideSNP_6.na31-b37-strand.txt'), 'rb') as fin:
            affy = db['Affymetrix']
            count = 0

            for line in fin:
                record = line.strip().split('\t')

                if record[0] == 'Probe Set ID': continue

                try:
                    _probe_set_id, rs, chrom, pos, strand = record
                except ValueError:
                    print >>sys.stderr, record
                    continue

                try:
                    pos = int(pos)
                except ValueError:
                    if pos == '---':
                        pos = None
                    else:
                        print >>sys.stderr, record
                        continue

                try:
                    rs = int(rs.replace('rs', ''))
                except ValueError:
                    print >>sys.stderr, record
                    continue

                if not strand in ('+', '-'):
                    continue

                affy.insert({'chrom': chrom, 'pos': pos, 'strand': strand, 'rs': rs})
                count += 1

            affy.create_index([('chr', ASCENDING), ('pos', ASCENDING)])
            affy.create_index([('rs', ASCENDING)])
            print 'Affymetrix done.', count

        # Illumina
        with open(os.path.join(path_to_reference_dir, 'HumanOmni2.5M-b37-v2.strand'), 'rb') as fin:
            illumina = db['Illumina']
            count = 0

            for line in fin:
                record = line.strip().split('\t')

                _probe_set_id, chrom, pos, _prob, strand, _alleles = record
                try:
                    pos = int(pos)
                except ValueError:
                    print >>sys.stderr, record
                    continue

                assert strand in ('+', '-')

                illumina.insert({'chrom': chrom, 'pos': pos, 'strand': strand})
                count += 1

            illumina.create_index([('chr', ASCENDING), ('pos', ASCENDING)])
            print 'Illumina done.', count
