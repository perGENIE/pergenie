import string


CHROMS = [i+1 for i in range(22)] + ['X', 'Y', 'M']
CHROM_CHOICES = zip(CHROMS, CHROMS)


def chr_id2chrom(chr_id):
    return {23: 'X', 24: 'Y', 25: 'M'}.get(chr_id, str(chr_id))


def reverse_complement(text):
    nucleic_acid_codes = string.maketrans("ATGCRYKMBVDHatgcrykmbvdh", "TACGYRMKVBHDtacgyrmkvbhd")
    return text.translate(nucleic_acid_codes)
