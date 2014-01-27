#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,os
import socket
import csv
import tarfile
sys.path.append('../../')
host = socket.gethostname()
if host.endswith('.local'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.develop")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.staging")
import MySQLdb as mdb

from django.conf import settings
from lib.utils.io import get_url_content
from lib.utils import clogging
log = clogging.getColorLogger(__name__)

# population_codes = ['AFR', 'AMR', 'ASN', 'EUR', 'all']
population_codes = ['all']
umich_dst_base = os.path.join(settings.LARGE_REFERENCE_DIR, 'umich_1kg_freq')


def calc_snp_freq():
    """Write out SNP frequency data as CSV
    """

    chroms = [str(i) for i in range(1,23)]  # 1 to 22
    bases = ['A', 'T', 'G', 'C']

    for population in population_codes:
        log.info(population)

        # Get 1000 Genomes Phase1 allele freq. data from Univ., Mich.
        umich_tgz = 'v2.20101123{0}.autosomes.freq.tgz'.format({'AFR': '.AFR',
                                                                'AMR': '.AMR',
                                                                'ASN': '.ASN',
                                                                'EUR': '.EUR',
                                                                'all': ''}[population])
        umich_dst_tgz = os.path.join(umich_dst_base, umich_tgz)

        if not os.path.exists(umich_dst_tgz):
            log.info('Getting data from UMich...')
            get_url_content(url='ftp://share.sph.umich.edu/1000genomes/fullProject/2012.02.14/{0}'.format(umich_tgz), dst=umich_dst_tgz)

        umich_pop_dir = os.path.join(umich_dst_base, population)
        if not os.path.exists(umich_pop_dir):
            log.info('Extracting...')
            arc_file = tarfile.open(umich_dst_tgz)
            arc_file.extractall(umich_dst_base)
            arc_file.close()

        # Calc allele freq. data
        snp_freq_pop = os.path.join(umich_dst_base, population, population + '_allele_freq.csv')
        with file(snp_freq_pop, 'w') as fout:
            for chrom in chroms:
                umich_arc_dst = os.path.join(umich_dst_base, population, '20101123{pop}.chr{chrom}.ac'.format(pop={'AFR': '.AFR',
                                                                                                                   'AMR': '.AMR',
                                                                                                                   'ASN': '.ASN',
                                                                                                                   'EUR': '.EUR',
                                                                                                                   'all': ''}[population],
                                                                                                              chrom=chrom))
                log.info('{0}'.format(umich_arc_dst))

                with file(umich_arc_dst, 'r') as fin:

                    # $ head 20101123.ASN.chr1.ac
                    #
                    # SNP AL1 AL2 AC1 MAC
                    # chr1:10523:D R 2 572 0
                    # rs58108140 G A 497 75
                    # ...

                    for record in csv.DictReader(fin, delimiter=' '):
                        assert len(record) == 5  ##

                        none = '\N'
                        data = {'rs': none,
                                'chrom': none,
                                'pos': none}

                        if record['SNP'].startswith('rs'):
                            data['rs'] = int(record['SNP'].replace('rs', ''))
                        elif record['SNP'].startswith('chr'):
                            if len(record['SNP'].split(':')) != 2: continue  # skip INDELs
                            data['chrom'] = record['SNP'].split(':')[0].replace('chr', '')
                            data['pos'] = int(record['SNP'].split(':')[1])
                            assert data['chrom'] in chroms, record

                        if record['AL2'] == '2' and record['MAC'] == '0': continue  # skip singleton

                        assert data['rs'] or (data['chrom'] and data['pos']), record

                        if not ((record['AL1'] in bases) and (record['AL2'] in bases)):
                            log.debug('skip odd record {0}'.format(record))
                            continue

                        data['al1'] = record['AL1']
                        data['al2'] = record['AL2']
                        data['f_al1'] = round(float(record['AC1']) / float(int(record['AC1']) + int(record['MAC'])), 3)
                        data['f_al2'] = round(float(record['MAC']) / float(int(record['AC1']) + int(record['MAC'])), 3)

                        assert 0.000 <= data['f_al1'] <= 1.000, (record, data)
                        assert 0.000 <= data['f_al2'] <= 1.000, (record, data)
                        assert data['f_al1'] + data['f_al2'] == 1.000, (record, data)
                        # if data['f_al1'] == 0.000 or data['f_al2'] == 0.000:
                        #     log.info('freq 0.000: {0}'.format((record, data)))
                        # if data['f_al1'] == 1.000 or data['f_al2'] == 1.000:
                        #     log.info('freq 1.000: {0}'.format((record, data)))

                        print >>fout, ','.join([str(x) for x in [data['rs'], data['chrom'], data['pos'],
                                                                 data['al1'], data['al2'], data['f_al1'], data['f_al2']]])

    log.info('Done!')


if __name__ == '__main__':
    calc_snp_freq()
