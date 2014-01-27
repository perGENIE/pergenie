#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,os
import socket
import unittest
import csv
import tarfile
sys.path.append('../../')
host = socket.gethostname()
if host.endswith('.local'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.develop")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.staging")

from django.conf import settings
from lib.mysql.snps import Snps
snps = Snps(settings.DATABASES['snps']['HOST'],
            settings.DATABASES['snps']['USER'],
            settings.DATABASES['snps']['PASSWORD'],
            settings.DATABASES['snps']['NAME'])

from lib.utils.io import get_url_content
from lib.utils import clogging
log = clogging.getColorLogger(__name__)

population_codes = ['AFR', 'AMR', 'ASN', 'EUR']
chroms = [str(i) for i in range(1,23)]  # 1 to 22
bases = ['A', 'T', 'G', 'C']

class SimpleTest(unittest.TestCase):
    def setUp(self):
        self.test_snps_not_found = {1: ['A','T']}
        self.test_snps_manual_curation = {519113: ['C','G']}

    def test_snps_not_found(self):
        for population in population_codes:
            for rsid, alleles in self.test_snps_not_found.items():
                found = snps._allele_freq_one(population, rsid)
                self.assertFalse(found)

    def test_match_manual_curation(self):
        for population in population_codes:
            for rsid, alleles in self.test_snps_manual_curation.items():
                found = snps._allele_freq_one(population, rsid)
                self.assertTrue(found)
                self.assertEqual(set([found['alt_1'], found['alt_2']]), set(alleles))

                allele_freqs, uniq_alleles = snps.get_allele_freqs(rsid, population=population)
                self.assertEqual(set(uniq_alleles), set(alleles))

    def test_ASN_match_RAvariome(self):
        RAvariome_snps = {3093024: ['G','A'],
                          7574865: ['G','T'],
                          2230926: ['T','G'],
                          2075876: ['G','A'],
                          805297: ['C','A'],
                          2233434: ['A','G'],
                          10821944: ['T','G'],
                          2847297: ['A','G'],
                          11900673: ['C','T'],
                          2867461: ['G','A'],
                          12529514: ['T','C'],
                          7404928: ['C','T'],
                          4937362: ['C','T'],
                          657075: ['G','A'],
                          1957895: ['T','G'],
                          6496667: ['C','A'],
                          2280381: ['C','T'],
                          2841277: ['C','T'],
                          3781913: ['G','T'],
                          3783637: ['T','C'],
                          3125734: ['C','T']}

        for population in ['ASN']:
            for rsid, alleles in RAvariome_snps.items():
                found = snps._allele_freq_one(population, rsid)
                self.assertTrue(found)
                self.assertEqual(set([found['alt_1'], found['alt_2']]), set(alleles))

                allele_freqs, uniq_alleles = snps.get_allele_freqs(rsid, population=population)
                self.assertEqual(set(uniq_alleles), set(alleles))

if __name__ == '__main__':
    unittest.main()
