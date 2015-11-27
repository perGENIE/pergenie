import operator


def cumulative_risk(estimated_snp_risks):
    return reduce(operator.mul, estimated_snp_risks, 1.0)


def relative_risk_to_general_population(risk_allele_freq, odds_ratio, zygosities):
    """
    >>> relative_risk_to_general_population(0.28, 1.37, 'NA')
    1.0
    >>> relative_risk_to_general_population(0.28, 1.37, 'RR')
    1.5
    >>> relative_risk_to_general_population(0.28, 1.37, 'R.')
    1.1
    >>> relative_risk_to_general_population(0.28, 1.37, '..')
    0.8

    #
    # >>> relative_risk_to_general_population(0.28, 1.37, '..')
    # (0.8, 1.22)
    """

    try:
        prob_hom = risk_allele_freq**2
        prob_het = 2*risk_allele_freq*(1-risk_allele_freq)
        prob_ref = (1-risk_allele_freq)**2

        odds_ratio_hom = odds_ratio**2
        odds_ratio_het = odds_ratio
        odds_ratio_ref = 1.0

        average_population_risk = prob_hom*odds_ratio_hom + prob_het*odds_ratio_het + prob_ref*odds_ratio_ref

        risk_hom = odds_ratio_hom/average_population_risk
        risk_het = odds_ratio_het/average_population_risk
        risk_ref = odds_ratio_ref/average_population_risk

    except TypeError:
        return 1.0# , 1.0  ###

    return round({'RR':risk_hom, 'R.':risk_het, '..':risk_ref, 'NA': 1.0}.get(zygosities, 1.0), 1)# , round(average_population_risk, 2)


def zyg(genotype, risk_allele):
    """Returns zygosities by counting risk alleles.

    >>> zyg('AA', 'A')
    'RR'
    >>> zyg('AT', 'A')
    'R.'
    >>> zyg('TT', 'A')
    '..'
    """

    return {0: '..', 1: 'R.', 2: 'RR'}[genotype.count(risk_allele)]


def to_signed_real(records, is_log=False):
    """
    >>> records = [{'RR': -1.0}, {'RR': 0.0}, {'RR': 0.1}, {'RR': 1.0}]
    >>> print _to_signed_real(records)
    [{'RR': -10.0}, {'RR': 1.0}, {'RR': 1.3}, {'RR': 10.0}]
    """
    results = []

    for record in records:
        tmp_record = record

        if is_log:
            # Convert to real
            tmp_record['RR'] = pow(10, record['RR'])

        # If RR is negative effects, i.e, 0.0 < RR < 1.0,
        # inverse it and minus sign
        if 0.0 < tmp_record['RR'] < 1.0:
            tmp_record['RR'] = -1.0 / record['RR']
        elif tmp_record['RR'] == 0.0:
            tmp_record['RR'] = 1.0
        else:
            tmp_record['RR'] = record['RR']

        tmp_record['RR'] = round(tmp_record['RR'], 1)

        results.append(tmp_record)

    return results
