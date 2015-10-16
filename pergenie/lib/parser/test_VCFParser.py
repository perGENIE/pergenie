# -*- coding: utf-8 -*-

import os
import unittest

from VCFParser import VCFParser, VCFParseError


class SimpleTest(unittest.TestCase):
    def setUp(self):
        self.basedir = os.path.dirname(os.path.abspath(__file__))

    def test_success(self):
        v = VCFParser(open(os.path.join(self.basedir, 'test', 'test.vcf41.vcf'), 'r'))

        self.assertEqual(v.sample_names, ['NA00001', 'NA00002', 'NA00003'])

        record = v.parse_lines().next()

        self.assertEqual(record['chrom'], '20')
        self.assertEqual(record['pos'], 14370)
        self.assertEqual(record['ID'], 'rs6054257')
        self.assertEqual(record['rs'], 6054257)
        self.assertEqual(record['REF'], 'G')
        self.assertEqual(record['ALT'], ['A'])

        self.assertEqual(record['NA00001'], {'GT': '0|0',
                                             'GQ': '48',
                                             'DP': '1',
                                             'HQ': '51,51'})
        self.assertEqual(record['NA00002'], {'GT': '1|0',
                                             'GQ': '48',
                                             'DP': '8',
                                             'HQ': '51,51'})
        self.assertEqual(record['NA00003'], {'GT': '1/1',
                                             'GQ': '43',
                                             'DP': '5',
                                             'HQ': '.,.'})

        self.assertEqual(record['genotype'], {'NA00001': 'GG',
                                              'NA00002': 'AG',
                                              'NA00003': 'AA'})

    def test_invalid_header(self):
        """case: without `#CHROM ...` line"""

        # py27
        # with self.assertRaises(VCFParseError) as cm:
        #     v = VCFParser(open(os.path.join(self.basedir, 'test', 'test.vcf41.invalid-header.vcf'), 'r'))
        #
        # self.assertEqual(cm.exception.error_code, 'Header-lines seem invalid. `#CHROM ...` does not exists.')

        # py26
        try:
            v = VCFParser(open(os.path.join(self.basedir, 'test', 'test.vcf41.invalid-header.vcf'), 'r'))
        except VCFParseError as e:
            self.assertEqual(e.error_code, 'Header-lines seem invalid. `#CHROM ...` does not exists.')
        else:
            self.fail('should have thrown VCFParseError')

    def test_invalid_header_2(self):
        """case: without whole header-lines"""

        try:
            v = VCFParser(open(os.path.join(self.basedir, 'test', 'test.vcf41.invalid-header.2.vcf'), 'r'))
        except VCFParseError as e:
            self.assertEqual(e.error_code, 'Header-lines seem invalid. `#CHROM ...` does not exists.')
        else:
            self.fail('should have thrown VCFParseError')

    def test_invalid_header_3(self):
        """case: delimiter is not [tab]"""

        try:
            v = VCFParser(open(os.path.join(self.basedir, 'test', 'test.vcf41.invalid-header.3.vcf'), 'r'))
        except VCFParseError as e:
            self.assertEqual(e.error_code, 'Header-lines seem invalid. Probably delimiter is not tab.')
        else:
            self.fail('should have thrown VCFParseError')


if __name__ == '__main__':
    unittest.main()
