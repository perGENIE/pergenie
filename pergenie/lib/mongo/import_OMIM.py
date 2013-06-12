#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import re
import subprocess
from collections import defaultdict
import urllib
import socket
socket.setdefaulttimeout(30)  # timeout for urlretrieve
import json
import time
import pymongo

class OMIMParser(object):
    """
    The OMIM (Online Mendelian Inheritance in Man, http://omim.org/)
    provides bulk download at http://omim.org/downloads
    """
    def __init__(self, fin, apikey):
        self.fin = fin
        self.apikey = apikey

    def get_all_records(self, func):
        record = {}

        with open(self.fin) as handle:
            for i,line in enumerate(handle):
                line = line.strip()

                # This line is the end of a RECORD
                if line.startswith('*RECORD*') or line.startswith('*THEEND*'):
                    if record:
                        assert record.has_key('NO'), 'line:%s key `NO` not found' % i+1
                        func(record)
                        record = {}
                    continue

                # This line is a title of a FIELD
                r = re.compile('\*FIELD\*\ (\w+)')
                field = r.findall(line)
                if field:
                    field_name = field[0]
                    record[field_name] = defaultdict(list)
                    continue

                # This line is a cotent of a FIELD
                if not line: continue
                if field_name == 'NO':
                    record[field_name] = int(line)

                elif field_name == 'AV':
                    if not record['NO'] in self.AVs:
                        self.omim_av.insert(self.fetch_AllelicVariants(record['NO']))
                        self.AVs.update([record['NO']])
                        record[field_name]['lines'].append(line)

                #     _no = re.findall('\.(\d+)$', line); _no = _no[0] if _no else None
                #     record[field_name]['no']
                #     {'no': _no, }

                else:
                    # TODO: write parser for each FIELD
                    record[field_name]['lines'].append(line)

    def insert_to_mongo(self, host="mongodb://localhost:27017", dbname="pergenie"):
        with pymongo.MongoClient(host=host) as c:
            db = c[dbname]
            omim = db['omim']
            omim_av = db['omim_av']
            if omim.count(): db.drop_collection(omim)
            if omim_av.count(): db.drop_collection(omim_av)
            self.omim_av = omim_av
            self.AVs = set()

            self.get_all_records(omim.insert)
            omim.create_index('NO')
            omim_av.create_index('mimNumber')
            omim_av.create_index('dbSnps')
            omim_av.create_index('rs')
            print >>sys.stderr, 'Total inserted AVs (mongo)', omim_av.count()

            self.count = omim.count()
            print >>sys.stderr, 'count (mongo)', self.count

    # def output_as_csv(self, fout):
    #     pass

    # def insert_to_mysql(self):
    #     pass


    def fetch_AllelicVariants(self, number):
        """
        The main data `omim.txt` does not contain whole information of OMIM.
        About `Allelic Variants`, for example of #Mim Number: 102565,
        the `Table View` for this record is as following:

        http://omim.org/allelicVariant/102565

        --------------------------------------------------------------------------------------------
        102565
        --------------------------------------------------------------------------------------------
        FILAMIN C; FLNC
        --------------------------------------------------------------------------------------------
        Allelic Variants (Selected Examples):

        Number | Phenotype                                 | Mutation                | dbSNP
        .0001  | MYOPATHY, MYOFIBRILLAR, FILAMIN C-RELATED | FLNC, TRP2710TER        | [rs121909518]
        .0002  | MYOPATHY, MYOFIBRILLAR, FILAMIN C-RELATED | FLNC, 12-BP DEL, NT2997 | -
        .0003  | MYOPATHY, DISTAL, 4                       | FLNC, MET251THR         | -
        .0004  | MYOPATHY, DISTAL, 4                       | FLNC, ALA193THR         | -
        --------------------------------------------------------------------------------------------

        Here, column `dbSNP` exists, but `omim.txt` does not contain `dbSNP`.
        So, by using OMIM API, following script fetch `Allelic Variants` records form OMIM,
        then import them into MongoDB.
        """
        url = 'http://api.omim.org/api/entry/allelicVariantList?mimNumber={number}&apiKey={apikey}&format=json'.format(number=number, apikey=self.apikey)
        content = ''.join(urllib.urlopen(url).readlines())
        data = json.loads(content)
        AVs = [x['allelicVariant'] for x in data['omim']['allelicVariantLists'][0]['allelicVariantList']]
        time.sleep(1)

        # Add rsid, like `{"rs": 671}` from `{"dbSnps": "rs671"}`
        for AV in AVs:
            if AV.has_key('dbSnps'):
                rs = [int(n) for n in re.split(',', AV['dbSnps'].replace('rs', ''))]
                AV.update({'rs': rs})

        print >>sys.stderr, 'mimNumber:', number, 'AVs:', len(AVs)

        return AVs

    def check(self):
        """Count by grep."""
        com1 = subprocess.Popen(['grep', '\*RECORD\*', sys.argv[1]], stdout=subprocess.PIPE)
        com2 = subprocess.Popen(['wc', '-l'], stdin=com1.stdout, stdout=subprocess.PIPE)
        out = int(com2.stdout.readline().strip())
        print >>sys.stderr, 'count (grep)', out
        assert self.count == out, 'self.check() failed. self.count does not mutch count by grep'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >>sys.stderr, "USAGE: {0} /path/to/omim.txt OMIM_APIKEY".format(sys.argv[0])
        sys.exit()

    p = OMIMParser(sys.argv[1], sys.argv[2])
    p.insert_to_mongo()
    print >>sys.stderr, 'done'
    p.check()
    print >>sys.stderr, 'ok'
