import re
import string

def reverse_complement(text):
    nucleic_acid_codes = string.maketrans("ATGCRYKMBVDHatgcrykmbvdh", "TACGYRMKVBHDtacgyrmkvbhd")
    return text.translate(nucleic_acid_codes)

def get_forward_risk_allele(risk_allele, freq_reported, freq_db, thrs):
    """Returns risk alleles on the forward strand with respect to
    the human reference genome, by checking consistences of
    allele frequences against 1000 Genomes.

    >>> get_forward_risk_allele('A', 0.1, {'A': 0.1, 'T': 0.9}, 0.1)
    'A'
    >>> get_forward_risk_allele('A', 0.1, {'T': 0.1, 'A': 0.9}, 0.1)
    'T'
    """
    pattern = re.compile(r'[ATGC]+')

    if not pattern.match(risk_allele):
        log.warn('Allele does not match A/T/G/C: {}'.format(risk_allele))
        return ''

    if not freq_reported or not freq_db:
        log.warn('Freq not found')
        return ''

    # Check if |freq_reported - freq_db| <= thrs
    freq = freq_db.get(risk_allele)
    if freq:
        if abs(freq_reported - freq) <= thrs:
            log.debug('ok')
            return risk_allele

    # Check if |freq_reported - freq_db_rev| <= thrs
    risk_allele_reverse = reverse_complement(risk_allele))
    freq = freq_db.get(risk_allele_reverse)
    if freq:
        if abs(freq_reported - freq) <= thrs:
            log.debug('resolved')
            return risk_allele_reverse
        else:
            log.warn('Allele freq inconsistent: {}, reported: {}, db: {}, thrs: {}'.format(risk_allele, freq_reported, freq_db, thrs))
            return ''

    log.warn('Freq not found')
    return ''
