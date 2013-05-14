# -*- coding: utf-8 -*-

import sys
import os
import unittest
import pymongo

from common import clean_file_name
import import_variants


class SimpleTest(unittest.TestCase):
    def setUp(self):
        # setup for MongoDB
        self.mongo_port = 27017
        self.connection = pymongo.Connection(port=self.mongo_port)
        self.db = self.connection['pergenie']
        self.basedir = os.path.dirname(os.path.abspath(__file__))
        self.testfile_dir = os.path.join(self.basedir, 'parser', 'test')

    def test_import_23andme_format(self):
        # TODO: current _cleaned is ugly ...
        file_path = os.path.join(self.testfile_dir, 'test.23andme.txt')
        file_name = os.path.basename(file_path)
        file_name_cleaned = clean_file_name(file_name)

        # import test data (23andme format)
        import_variants.import_variants(file_path=file_path,
                                        population='unknown',
                                        file_format='andme',
                                        user_id='test',
                                        mongo_port=self.mongo_port)

        # check if data was imported correctly
        variants = self.db['variants']['test'][file_name_cleaned]
        self.assertEqual(variants.count(), 85)

        # print >>sys.stderr, list(variants.find())
        self.assertEqual(variants.find_one({'rs': 4477212})['rs'], 4477212)
        self.assertEqual(variants.find_one({'rs': 4477212})['genotype'], 'AA')
        self.assertEqual(variants.find_one({'rs': 4477212})['chrom'], '1')
        self.assertEqual(variants.find_one({'rs': 4477212})['pos'], 82154)

        # drop imported collection
        self.db.drop_collection(variants)
        self.assertEqual(variants.count(), 0)

    def test_import_vcf_format(self):
        # TODO: current _cleaned is ugly ...
        file_path = os.path.join(self.testfile_dir, 'test.vcf41.vcf')
        file_name = os.path.basename(file_path)
        file_name_cleaned = clean_file_name(file_name)

        # import test data (VCF format)
        import_variants.import_variants(file_path=file_path,
                                        population='unknown',
                                        file_format='vcf_whole_genome',
                                        user_id='test',
                                        mongo_port=self.mongo_port)

        # check if data was imported correctly
        variants = self.db['variants']['test'][file_name_cleaned]
        self.assertEqual(variants.count(), 2)

        # print >>sys.stderr, list(variants.find())
        self.assertEqual(variants.find_one({'rs': 6054257})['rs'], 6054257)
        self.assertEqual(variants.find_one({'rs': 6054257})['genotype'], 'GG')
        self.assertEqual(variants.find_one({'rs': 6054257})['chrom'], '20')
        self.assertEqual(variants.find_one({'rs': 6054257})['pos'], 14370)

        self.assertEqual(variants.find_one({'rs': 6040355})['rs'], 6040355)
        self.assertEqual(variants.find_one({'rs': 6040355})['genotype'], 'GT')
        self.assertEqual(variants.find_one({'rs': 6040355})['chrom'], '20')
        self.assertEqual(variants.find_one({'rs': 6040355})['pos'], 1110696)

        # drop imported collection
        self.db.drop_collection(variants)
        self.assertEqual(variants.count(), 0)

#     @unittest.expectedFailure
#     def test_fail_foo(self):
#         pass


if __name__ == '__main__':
    unittest.main()
