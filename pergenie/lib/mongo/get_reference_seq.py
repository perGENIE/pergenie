# -*- coding: utf-8 -*-

import pyfasta


class MyFasta(object):
    def __init__(self, path_to_fasta):
        self.fa = pyfasta.Fasta(path_to_fasta, key_fn=lambda key: key.split()[0])  # , flatten_inplace=True)

    def get_seq(self, chrom, start, read_len):
        """Get sequence (one-based) of Fasta.

        >>> import os
        >>> fasta_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.fasta')
        >>> fa = MyFasta(fasta_path)
        >>> fa.get_seq(chrom=1, start=1, read_len=1)
        'A'
        >>> fa.get_seq(chrom=1, start=1, read_len=2)
        'AT'
        """

        seq = self.fa.sequence({'chr': str(chrom), 'start': int(start), 'stop': int(start) + int(read_len) - 1}, one_based=True)
        return seq


if __name__ == '__main__':
    import doctest
    doctest.testmod()
