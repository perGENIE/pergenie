import sys
import re
import subprocess
from collections import defaultdict
import pymongo

class OMIMParser(object):
    """
    TODO: parse `AV (Allelic variants)`
    TODO: can i get mutation information? need to parse like `LYS97TER`

    TODO: omim.txt does not contain the information of dbSNP in `Table View` of `Allelic Variants`
          so, we need to get this using API.
    """
    def __init__(self, fin):
        self.fin = fin

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

                # elif field_name == 'AV':
                #     _no = re.findall('\.(\d+)$', line); _no = _no[0] if _no else None
                #     record[field_name]['no']
                #     {'no': _no, }

                else:
                    # TODO: write parser for each FIELD
                    record[field_name]['lines'].append(line)

    def insert_to_mongo(self, host="mongodb://localhost:27017"):
        with pymongo.MongoClient(host=host) as c:
            omim = c['pergenie']['omim']
            if omim.count(): c['pergenie'].drop_collection(omim)

            self.get_all_records(omim.insert)
            omim.create_index('NO')

            self.count = omim.count()
            print 'count (mongo)', self.count

    # def insert_to_mysql(self, record):
    #     pass

    # def output_as_csv(self, record):
    #     pass

    def check(self):
        """Count by grep."""
        com1 = subprocess.Popen(['grep', '\*RECORD\*', sys.argv[1]], stdout=subprocess.PIPE)
        com2 = subprocess.Popen(['wc', '-l'], stdin=com1.stdout, stdout=subprocess.PIPE)
        out = int(com2.stdout.readline().strip())
        print 'count (grep)', out
        assert self.count == out, 'self.check() failed. self.count does not mutch count by grep'


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >>sys.stderr, "USAGE: {0} /path/to/omim.txt".format(sys.argv[0])
        sys.exit()

    p = OMIMParser(sys.argv[1])
    p.insert_to_mongo()
    print 'done'
    p.check()
    print 'ok'
