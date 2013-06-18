#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import re

from Bio import PDB
from io import cd
import subprocess

dst_dir = '/tmp/atoms'

class SelectChains(PDB.Select):
    def __init__(self, chain_letters):
        self.chain_letters = chain_letters

    def accept_chain(self, chain):
        print 'chain', chain
        print 'chain.get_id()', chain.get_id()
        return (chain.get_id() in self.chain_letters)

def fetch_pdb(pdb_id)# , chain_letters=None):
    pdb_id = pdb_id.lower()

    if not re.match('^[a-zA-Z0-9]{4}$', pdb_id):
        print >>sys.stderr, 'invalid PDB ID'
        return

    # TODO: or store all pdb file?
    if not os.path.exists(dst_dir): os.mkdir(dst_dir)

    with cd(dst_dir):
        dst = 'pdb' + pdb_id # + '.' + chain_letters.lower()
        # if os.path.exists(dst):
        #     return

        pdbl = PDB.PDBList()
        pdbl.retrieve_pdb_file(pdb_id.upper(), pdir=os.getcwd())

        in_path = os.path.join('pdb' + pdb_id + '.ent')
        parser = PDB.PDBParser()
        structure = parser.get_structure(pdb_id, in_path)

        writer = PDB.PDBIO()
        writer.set_structure(structure)
        writer.save(dst)# , select=SelectChains(chain_letters))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit("USAGE: {0} pdb_id".format(sys.argv[0]))
    fetch_pdb(sys.argv[1])
