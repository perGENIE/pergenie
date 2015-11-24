import re
from decimal import Decimal

from errors import GwasCatalogParseError
from lib.utils.genome import reverse_complement
from lib.utils import clogging
log = clogging.getColorLogger(__name__)

PATTERN = re.compile(r'[ATGC]+')
AMBIGOUS = '?'


def get_database_strand_allele(allele, reported_freq, database_freq, freq_diff_thrs=0.1):
    """Returns alleles on the same strand with respect to given
    allele frequency data.

    If given allele does not match A/T/G/C pattern, return `?` as ambigous allele.

    >>> get_database_strand_allele('N', 0.1, {'A': 0.1, 'G': 0.9}, 0.1)
    '?'

    If database_freq is not given, we can't validate allele starnd, so return `?`

    >>> get_database_strand_allele('A', 0.1, None, 0.1)
    '?'

    - Case 1: Alleles in database_freq is biallelic and A/G, T/C pattern.

    If allele in database_freq, return allele as it is.

    >>> get_database_strand_allele('A', 0.1, {'A': 0.1, 'G': 0.9}, 0.1)
    'A'
    >>> get_database_strand_allele('T', 0.1, {'T': 0.1, 'C': 0.9}, 0.1)
    'T'

    Else if reversed allele is in database_freq, return reversed allele.

    >>> get_database_strand_allele('T', 0.1, {'A': 0.1, 'G': 0.9}, 0.1)
    'A'
    >>> get_database_strand_allele('A', 0.1, {'T': 0.1, 'C': 0.9}, 0.1)
    'T'

    - Case 2: Alleles in database_freq is biallelic and A/T, G/C pattern,
    or database_freq is not biallelic, e.g., A/T/C, A/T/G/C.
    In such cases, we need to check the consistency of allele
    frequencies between database and reported.

    - Case 2-1: reported_freq is available.

    If allele is exist in database_freq and difference of allele freq
    betweern database_freq and reported_freq is within threshold,
    return allele as it is.

    >>> get_database_strand_allele('A', 0.1, {'A': 0.1, 'T': 0.9}, 0.1)
    'A'
    >>> get_database_strand_allele('T', 0.9, {'A': 0.1, 'T': 0.9}, 0.1)
    'T'
    >>> get_database_strand_allele('G', 0.1, {'G': 0.1, 'C': 0.9}, 0.1)
    'G'
    >>> get_database_strand_allele('C', 0.9, {'G': 0.1, 'C': 0.9}, 0.1)
    'C'

    Else if allele freq of reversed allele is exists in database_freq
    and the difference is within threshold, return reversed allele.

    >>> get_database_strand_allele('T', 0.1, {'A': 0.1, 'T': 0.9}, 0.1)
    'A'
    >>> get_database_strand_allele('A', 0.9, {'A': 0.1, 'T': 0.9}, 0.1)
    'T'
    >>> get_database_strand_allele('C', 0.1, {'G': 0.1, 'C': 0.9}, 0.1)
    'G'
    >>> get_database_strand_allele('G', 0.9, {'G': 0.1, 'C': 0.9}, 0.1)
    'C'

    Else return `?`

    >>> get_database_strand_allele('T', 0.5, {'A': 0.1, 'T': 0.9}, 0.1)
    '?'
    >>> get_database_strand_allele('A', 0.5, {'A': 0.1, 'T': 0.9}, 0.1)
    '?'
    >>> get_database_strand_allele('C', 0.5, {'G': 0.1, 'C': 0.9}, 0.1)
    '?'
    >>> get_database_strand_allele('C', 0.5, {'G': 0.1, 'C': 0.9}, 0.1)
    '?'

    - Case 2-2: reported_freq is not available, return `?`

    >>> get_database_strand_allele('A', None, {'A': 0.1, 'T': 0.9}, 0.1)
    '?'
    """

    reversed_allele = reverse_complement(allele)

    log_msg = ' allele: {}, reversed allele: {}, reported: {}, db: {}, freq_diff_thrs: {}'.format(allele, reversed_allele, reported_freq , database_freq, freq_diff_thrs)

    if not allele:
        log.info('Allele not given.' + log_msg)
        return AMBIGOUS

    if not PATTERN.match(allele):
        log.info('Given allele does not match A/T/G/C.' + log_msg)
        return AMBIGOUS

    if not database_freq:
        log.info('Database freq not given.' + log_msg)
        return AMBIGOUS

    # - Case 1: Alleles in database_freq is biallelic and A/G, T/C pattern.
    database_alleles = sorted(database_freq.keys())
    if database_alleles == ['A', 'G'] or database_alleles == ['C', 'T']:
        if allele in database_alleles:
            return allele
        elif reversed_allele in database_alleles:
            return reversed_allele
        else:
            raise GwasCatalogParseError('Unexpected pattern allele strand validation.' + log_msg)

    # - Case 2: Alleles in database_freq is biallelic and A/T, G/C pattern,
    # or database_freq is not biallelic, e.g., A/T/C, A/T/G/C.
    # In such cases, we need to check the consistency of allele
    # frequencies between database and reported.
    if reported_freq:
        # Check if |reported_freq - database_freq| <= freq_diff_thrs
        freq = database_freq.get(allele)
        if freq:
            if abs(Decimal(reported_freq) - Decimal(freq)) <= freq_diff_thrs:
                return allele

        # Check if |reported_freq - database_freq_rev| <= freq_diff_thrs
        freq = database_freq.get(reversed_allele)
        if freq:
            if abs(Decimal(reported_freq) - Decimal(freq)) <= freq_diff_thrs:
                return reversed_allele

        log.info('Reported freq and database freq are not consistent.' + log_msg)
        return AMBIGOUS
    else:
        log.info('Reported freq is not given.' + log_msg)
        return AMBIGOUS

    raise GwasCatalogParseError('Unexpected pattern allele strand validation, after validation process.' + log_msg)
