from django.conf import settings
import sys, os

def pdb2var(pdb_name):
    records = []
    record = ''

    with open(os.path.join(settings.BASE_DIR, 'data', 'large_dbs', 'pdb',pdb_name+'.pdb'), 'r') as f:
        for line in f:
            if not line.startswith('ATOM'): continue

            line = line[0:70]
            line = line.strip('\n ')
            assert not '\n' in line
            assert not '"' in line

            record += line + '\\n'
            if len(record) < 1000: continue

            records.append(record)
            record = ''

        records.append(record)

    return records
