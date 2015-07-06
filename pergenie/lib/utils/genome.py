def chr_id2chrom(chr_id):
    return {23: 'X', 24: 'Y', 25: 'M'}.get(chr_id, str(chr_id))
