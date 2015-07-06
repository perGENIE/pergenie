from django.conf import settings

from lib.utils.mutate_fasta import MutateFasta


reference_genome_fasta = MutateFasta(settings.REFERENCE_GENOME_FASTA)
