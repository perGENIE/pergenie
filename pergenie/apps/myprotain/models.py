from django.conf import settings
import sys, os

from lib.utils.fetch_pdb import fetch_pdb

def pdb2var(pdb_id):
    records = []
    record = ''

    fetch_pdb(pdb_id)
    fin_path = os.path.join('/tmp/atoms', 'pdb'+pdb_id.lower()+'.atom')

    with open(fin_path, 'r') as fin:
        for line in fin:
            line = line[0:70]
            line = line.strip('\n ')
            assert not '\n' in line
            assert not '"' in line
            record += line + '\\n'

            if len(record) > 1000:
                records.append(record)
                record = ''

        records.append(record)

    return records
