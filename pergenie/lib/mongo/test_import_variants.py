# -*- coding: utf-8 -*-

import os
import unittest
import pymongo

import import_variants

class SimpleTest(unittest.TestCase):
    """doc"""

    def setUp(self):
        self.mongo_port = 27017
        connection = pymongo.Connection(port=self.mongo_port)
        self.db = connection['pergenie']

        self.file_path = os.path.join('test', 'test_23andme.txt')
        self.file_name_cleaned = self.file_path.split('/')[-1].replace('.', '').replace(' ', '')

    def test_import_23andme_format(self):
        # import test data (23andme format)
        import_variants.import_variants(file_path=self.file_path,
                                        population='unknown',
                                        sex='unknown',
                                        file_format='andme',
                                        user_id='test',
                                        mongo_port=self.mongo_port)

        # check if data was imported correctly
        variants = self.db['variants']['test'][self.file_name_cleaned]
        self.assertEqual(variants.count(), 85)

        # drop imported collection
        self.db.drop_collection(variants)
        self.assertEqual(variants.count(), 0)

#     def test_import_vcf_format(self):
#         pass


#     @unittest.expectedFailure
#     def test_fail_foo(self):
#         pass


if __name__ == '__main__':
    unittest.main()
