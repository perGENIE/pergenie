# -*- coding: utf-8 -*-

import os
import unittest
import pymongo

import import_variants

class SimpleTest(unittest.TestCase):
    def setUp(self):
        # set-up for MongoDB
        self.mongo_port = 27017
        connection = pymongo.Connection(port=self.mongo_port)
        self.db = connection['pergenie']

    def test_import_23andme_format(self):

        # TODO: current _cleaned is ugly ...
        file_path = os.path.join('test', 'test.23andme.txt')
        file_name_cleaned = file_path.split('/')[-1].replace('.', '').replace(' ', '')

        # import test data (23andme format)
        import_variants.import_variants(file_path=file_path,
                                        population='unknown',
                                        sex='unknown',
                                        file_format='andme',
                                        user_id='test',
                                        mongo_port=self.mongo_port)

        # check if data was imported correctly
        variants = self.db['variants']['test'][file_name_cleaned]
        self.assertEqual(variants.count(), 85)

        self.assertEqual(variants.find_one({'rs': 4477212})['rs'], 4477212)
        self.assertEqual(variants.find_one({'rs': 4477212})['genotype'], 'AA')

        # drop imported collection
        self.db.drop_collection(variants)
        self.assertEqual(variants.count(), 0)

    def test_import_vcf_format(self):
        # TODO: current _cleaned is ugly ...
        file_path = os.path.join('test', 'test.vcf41.vcf')
        file_name_cleaned = file_path.split('/')[-1].replace('.', '').replace(' ', '')

        # import test data (VCF format)
        import_variants.import_variants(file_path=file_path,
                                        population='unknown',
                                        sex='unknown',
                                        file_format='vcf',
                                        user_id='test',
                                        mongo_port=self.mongo_port)

        # check if data was imported correctly
        variants = self.db['variants']['test'][file_name_cleaned]
        self.assertEqual(variants.count(), 2)

        self.assertEqual(variants.find_one({'rs': 6054257})['rs'], 6054257)
        self.assertEqual(variants.find_one({'rs': 6054257})['genotype'], 'GG')

        self.assertEqual(variants.find_one({'rs': 6040355})['rs'], 6040355)
        self.assertEqual(variants.find_one({'rs': 6040355})['genotype'], 'GT')

        # drop imported collection
        self.db.drop_collection(variants)
        self.assertEqual(variants.count(), 0)


#     @unittest.expectedFailure
#     def test_fail_foo(self):
#         pass


if __name__ == '__main__':
    unittest.main()
