# -*- coding: utf-8 -*-

import csv
import re

class WeblioEng2Ja(object):
    def __init__(self, path_to_eng2ja, path_to_eng2ja_plus):
        self.eng2ja = {}

        with open(path_to_eng2ja, 'rb') as fin:
            for record in csv.DictReader(fin, delimiter='/'):
                self.eng2ja[record['eng']] = record['ja']
        with open(path_to_eng2ja_plus, 'rb') as fin:
            for record in csv.DictReader(fin, delimiter='/'):
                self.eng2ja[record['eng']] = record['ja']

    def test(self):
        print '{0}: {1}'.format("Alzheimer's desease", self.eng2ja.get("Alzheimer's desease"))
        print '{0}: {1}'.format('アルツハイマー病', self.eng2ja.get('アルツハイマー病'))

    def get(self, raw_query):
        raw_result = self.eng2ja.get(raw_query)
        if raw_result:
            return raw_result
        else:
            return self.eng2ja.get(raw_query.lower())

    def split_get(self, raw_query):
        result = ""
        split_query = raw_query.split()
        for query in split_query:
            if self.get(query):
                result += self.get(query)
        return result

    def try_get(self, raw_query):
        if self.get(raw_query):
            return self.get(raw_query)
        else:
            return self.split_get(raw_query)
