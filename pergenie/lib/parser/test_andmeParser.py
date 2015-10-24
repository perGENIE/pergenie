# -*- coding: utf-8 -*-

import os
import unittest

from andmeParser import andmeParser, andmeParseError


class SimpleTest(unittest.TestCase):
    def setUp(self):
        self.basedir = os.path.dirname(os.path.abspath(__file__))

    def test_success(self):
        p = andmeParser(open(os.path.join(self.basedir, 'test', 'test.23andme.txt'), 'r'))

        self.assertEqual(p.ref_genome_version, 'b37')

        record = p.parse_lines().next()

        self.assertEqual(record['id'], 'rs4477212')
        self.assertEqual(record['rs'], 4477212)
        self.assertEqual(record['chrom'], '1')
        self.assertEqual(record['pos'], 82154)
        self.assertEqual(record['genotype'], 'AA')

    def test_invalid_file(self):
        """case: fin is another file-format"""

        # py27
        # with self.assertRaises(andmeParseError) as cm:
        #     p = andmeParser(open(os.path.join(self.basedir, 'test', 'test.vcf41.vcf'), 'r'))
        #
        # self.assertEqual(cm.exception.error_code, 'Header-lines seem invalid. `# rsid ...` does not exists.')

        # py26
        try:
            p = andmeParser(open(os.path.join(self.basedir, 'test', 'test.vcf41.vcf'), 'r'))
        except andmeParseError as e:
            self.assertEqual(e.error_code, 'Header-lines seem invalid. `# rsid ...` does not exists.')
        else:
            self.fail('should have thrown andmeParseError')

    def test_invalid_header_1(self):
        """case: without whole header-lines"""

        try:
            p = andmeParser(open(os.path.join(self.basedir, 'test', 'test.23andme.invalid-header.1.txt'), 'r'))
        except andmeParseError as e:
            self.assertEqual(e.error_code, 'Header-lines seem invalid. `# rsid ...` does not exists.')
        else:
            self.fail('should have thrown andmeParseError')



    def test_invalid_header_2(self):
        """case: without reference genome informaion in header-lines"""

        try:
            p = andmeParser(open(os.path.join(self.basedir, 'test', 'test.23andme.invalid-header.2.txt'), 'r'))
        except andmeParseError as e:
            self.assertEqual(e.error_code, 'Could not determine reference-genome version from header-lines.')
        else:
            self.fail('should have thrown andmeParseError')



if __name__ == '__main__':
    unittest.main()
