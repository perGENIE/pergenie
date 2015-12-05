import operator
from pprint import pprint
from decimal import Decimal, getcontext

from lib.utils.deprecated_decorator import deprecated


def cumulative_risk(estimated_snp_risks):
    """Returns cumulative risk.

    >>> cumulative_risk([1.0, 2.0, None, 3.0])
    6.0
    >>> cumulative_risk([])
    1.0
    """
    getcontext().prec = 4

    assert type(estimated_snp_risks) == list

    if not estimated_snp_risks or set(estimated_snp_risks) == set([None]):
        return None

    return reduce(operator.mul, [val for val in estimated_snp_risks if val is not None], Decimal(1.0))


def estimated_risk(risks, zygosities):
    return risks.get(zygosities, Decimal(1.0))


def genotype_specific_risks_relative_to_population(risk_allele_freq, odds_ratio):
    """Returns genotype specific risks relative to the general population.

    >>> pprint(genotype_specific_risks_relative_to_population(0.2, 1.5))
    {'..': Decimal('0.8264'), 'R.': Decimal('1.240'), 'RR': Decimal('1.860')}

    >>> pprint(genotype_specific_risks_relative_to_population(0.3, 1.5))
    {'..': Decimal('0.7564'), 'R.': Decimal('1.135'), 'RR': Decimal('1.702')}

    >>> pprint(genotype_specific_risks_relative_to_population(0.4, 1.5))
    {'..': Decimal('0.6944'), 'R.': Decimal('1.042'), 'RR': Decimal('1.562')}
    """
    getcontext().prec = 4

    risk_allele_freq = Decimal(risk_allele_freq)
    odds_ratio = Decimal(odds_ratio)

    prob_hom = risk_allele_freq**2
    prob_het = 2 * risk_allele_freq * (1 - risk_allele_freq)
    prob_ref = (1 - risk_allele_freq)**2

    odds_ratio_hom = odds_ratio**2
    odds_ratio_het = odds_ratio**1
    odds_ratio_ref = odds_ratio**0

    average_population_risk = prob_hom * odds_ratio_hom + prob_het * odds_ratio_het + prob_ref * odds_ratio_ref

    risk_hom = odds_ratio_hom / average_population_risk
    risk_het = odds_ratio_het / average_population_risk
    risk_ref = odds_ratio_ref / average_population_risk

    return {'RR': risk_hom, 'R.': risk_het, '..': risk_ref}


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


@deprecated
def to_signed_real(records, is_log=False):
    """
    # >>> records = [{'RR': -1.0}, {'RR': 0.0}, {'RR': 0.1}, {'RR': 1.0}]
    # >>> print _to_signed_real(records)
    # [{'RR': -10.0}, {'RR': 1.0}, {'RR': 1.3}, {'RR': 10.0}]
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
