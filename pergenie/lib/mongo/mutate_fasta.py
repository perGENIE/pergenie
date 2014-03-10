#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys, os
from pyfasta import Fasta

class MutateFasta(object):
    def __init__(self, fasta):
        self.fasta = Fasta(fasta, key_fn=lambda key: key.split()[0])
        # self.chroms = [str(i+1) for i in range(22)] + ['X', 'Y']  # , 'MT']

    def generate_seq(self, records, offset=None):
        if not records and not offset: return

        seq = ''
        chrom = offset[0] if offset else records[0]['chrom']
        prev_pos = offset[1] if offset else 0
        last_pos = offset[2] if offset else len(self.fasta[chrom])

        for r in records:
            ref = self._slice_fasta(r['chrom'], r['pos'], r['pos'])

            if not r['chrom'] == chrom: continue
            if not (r['ref'] and r['alt']): continue
            if not r['ref'][0] == ref: continue

            mut_type, sub_seq = self._classify_mut(r['ref'], r['alt'])

            if mut_type == 'snv':
                seq += self._slice_fasta(chrom, prev_pos + 1, r['pos'] - 1)
                seq += sub_seq
                prev_pos = r['pos']

            elif mut_type == 'del':
                seq += self._slice_fasta(chrom, prev_pos + 1, r['pos'])
                prev_pos += len(sub_seq)

            elif mut_type == 'ins':
                seq += self._slice_fasta(chrom, prev_pos + 1, r['pos'])
                seq += sub_seq
                prev_pos = r['pos']

        # Reminder
        if prev_pos + 1 <= last_pos:
            seq += self._slice_fasta(chrom, prev_pos + 1, last_pos)

        return seq

    def generate_contexted_seq(self, r):
        cons = []
        chrom = r['chrom']

        # TODO: support - strand genes. (currently only supports + strand genes...)

        # NOTE: refFlat is stored in 0-based coordinate

        # 5'UTR + 1st Exon
        cons.append([self._slice_fasta(chrom, r['txStart'] + 1, r['cdsStart']), 'utr'])
        cons.append([self._slice_fasta(chrom, r['cdsStart'] + 1, r['exonEnds'][0]), 'exon'])

        if r['exonCount'] > 1:
            cons.append([self._slice_fasta(chrom, r['exonEnds'][0] + 1, r['exonStarts'][1]), 'intron'])

            # Exons
            for i,con in enumerate(r['exonStarts']):
                if i == 0 or i+1 == r['exonCount']: continue

                cons.append([self._slice_fasta(chrom, r['exonStarts'][i] + 1, r['exonEnds'][i]), 'exon'])
                cons.append([self._slice_fasta(chrom, r['exonEnds'][i] + 1, r['exonStarts'][i+1]), 'intron'])

            # last Exon + 3'UTR
            cons.append([self._slice_fasta(chrom, r['exonStarts'][r['exonCount']-1] + 1, r['cdsEnd']), 'exon'])

        cons.append([self._slice_fasta(chrom, r['cdsEnd'] + 1, r['txEnd']), 'utr'])

        return cons

    def _slice_fasta(self, chrom, start, stop):
        return self.fasta.sequence({'chr': str(chrom), 'start': int(start), 'stop': int(stop)}, one_based=True)

    def _classify_mut(self, ref, alt):
        """
        >>> _classify_mut('A','G')
        ('snv', 'G')
        >>> _classify_mut('G','GAA')
        ('ins', 'AA')
        >>> _classify_mut('TTA','T')
        ('del', 'TA')
        """

        if len(ref) == len(alt) == 1:
            return 'snv', alt
        elif len(ref) < len(alt):
            assert ref[0] == alt[0], '{0} {1}'.format(ref, alt)
            return 'ins', alt[1:]
        elif len(ref) > len(alt):
            assert ref[0] == alt[0], '{0} {1}'.format(ref, alt)
            return 'del', ref[1:]


def _main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--fasta', help='path to reference genome')
    args = arg_parser.parse_args()

    m = MutateFasta(fasta=args.fasta)

    records = [{'chrom': '1', 'pos': 5, 'ref': 'N', 'alt': 'A'},
               {'chrom': '1', 'pos': 6, 'ref': 'N', 'alt': 'T'}]
    seq = m.generate_seq(records, offset=['1', 0, 8])
    print seq

    records = []
    seq = m.generate_seq(records, offset=['1', 0, 8])
    print seq

if __name__ == '__main__':
    _main()
