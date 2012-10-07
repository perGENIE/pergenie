#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import argparse
import sys

import pyfasta
import colors


def slice_fasta(fasta, chrom, start, stop):
    return fasta.sequence({'chr': str(chrom), 'start': int(start), 'stop': int(stop)}, one_based=True)

def _main():
    chroms = [str(i+1) for i in range(22)] + ['X', 'Y', 'MT']
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('fasta', help='reference')
    arg_parser.add_argument('chrom')
    arg_parser.add_argument('start')
    arg_parser.add_argument('stop')
    args = arg_parser.parse_args()

    ref_fasta = pyfasta.Fasta(args.fasta, key_fn=lambda key: key.split()[0])  # >1, >2, ..., >X, >Y
    slice = slice_fasta(ref_fasta, args.chrom, args.start, args.stop)
    
    print slice


    
if __name__ == '__main__':
    _main()
