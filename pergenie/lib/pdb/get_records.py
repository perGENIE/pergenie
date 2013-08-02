import sys, os
import gzip
import re

from django.conf import settings
from lib.utils.io import cd
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


def get_records(pdb_id):
    pdb_id = pdb_id.lower()

    if not re.match('^[a-zA-Z0-9]{4}$', pdb_id):
        log.error('invalid PDB ID: %s' % pdb_id)
        return

    with cd(settings.PATH_TO_PDB):
        pdb_file = os.path.join(pdb_id[1:3], 'pdb' + pdb_id + '.ent.gz')
        if not os.path.exists(pdb_file):
            log.error('pdb file does not exist: %s' % pdb_id)

        return gzip.open(pdb_file, 'r')
