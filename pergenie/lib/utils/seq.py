from pergenie.fasta import reference_genome_fasta
from .genome import chr_id2chrom

def reference_allele(chr_id, chr_pos):
    if chr_id and chr_pos:
        ref = reference_genome_fasta.slice_fasta(chr_id2chrom(chr_id), chr_pos, chr_pos)
    else:
        ref = ''

    return ref
