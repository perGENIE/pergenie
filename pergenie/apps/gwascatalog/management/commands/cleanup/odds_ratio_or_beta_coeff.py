import re

from errors import GwasCatalogParseError
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


def get_odds_ratio_or_beta_coeff(odds_ratio_or_beta_coeff, unit):
    """Parse `odds_ratio_or_beta_coeff` in GWAS Catalog.

    >>> get_odds_ratio_or_beta_coeff('1.0', '')
    ('1.0', None)

    >>> get_odds_ratio_or_beta_coeff('-1.0', '')
    Traceback (most recent call last):
    ...
    GwasCatalogParseError: Strange odds_ratio: -1.0

    >>> get_odds_ratio_or_beta_coeff('1.0', 'mg/L')
    (None, '1.0')
    """

    if odds_ratio_or_beta_coeff == '':
        return None, None

    if unit:
        # OR and beta are mixed in the same row.
        # To identify them, we check if `confidence_interval_95_percent` has unit descriptor or not.
        # Beta coeff usually have a unit descriptor associated with them
        # e.g., 0.111 [0.08-0.14] unit decrease, and OR have no unit descriptors.
        odds_ratio = None
        beta_coeff = odds_ratio_or_beta_coeff

        try:
            value = float(beta_coeff)
        except (ValueError, AssertionError):
            raise GwasCatalogParseError('Strange beta_coeff: {}'.format(odds_ratio_or_beta_coeff))

    else:
        # In the GWAS Catalog, OR is asserted to be: OR > 1.
        # If OR are reported as OR < 1 in the articles, OR are inverted to 1/OR > 1
        # and the risk alleles are flipped to non risk alleles.
        odds_ratio = odds_ratio_or_beta_coeff
        beta_coeff = None

        try:
            value = float(odds_ratio)
            assert value > 0.0
        except (ValueError, AssertionError):
            raise GwasCatalogParseError('Strange odds_ratio: {}'.format(odds_ratio_or_beta_coeff))

    return odds_ratio, beta_coeff


def get_ci_and_unit(text):
    """
    >>> get_ci_and_unit('[NR] (kg/m2 per copy in adults)')
    ('', '(kg/m2 per copy in adults)')

    >>> get_ci_and_unit('% [NR] (of variance explained)')
    ('', '% (of variance explained)')

    >>> get_ci_and_unit('[NR] ((women))')
    ('', '((women))')

    >>> get_ci_and_unit('[NR] (SD lower (hip))')
    ('', '(SD lower (hip))')

    >>> get_ci_and_unit('[1.08-1.16]')
    ('1.08-1.16', '')

    >>> get_ci_and_unit('[1.28, 2.02]')
    ('1.28, 2.02', '')

    >>> get_ci_and_unit('[-2.13040-19.39040]')
    ('-2.13040-19.39040', '')

    >>> get_ci_and_unit('((U/L increase))')
    ('', 'U/L increase))')

    >>> get_ci_and_unit('NR (unit increase)')
    ('', 'NR (unit increase)')

    # typo?
    >>> get_ci_and_unit('[0.006-0.01] ml/min/1.73 m2 decrease]')
    ('0.006-0.01', 'ml/min/1.73 m2 decrease]')

    # ?
    >>> get_ci_and_unit('((0.04-0.09) mmol/L increase)')
    ('0.04-0.09', 'mmol/L increase)')

    >>> get_ci_and_unit('([0.03-0.07 u mol/L increase)')
    ('0.03-0.07', 'u mol/L increase)')

    # TODO:
    # '([1.2-1.61])'
    # '([1.32-3.26 cm increase)'
    # '1.19-1.48]'

    # ?
    >>> get_ci_and_unit('- 7.90 [NR] (msec difference between homozygotes)')
    Traceback (most recent call last):
    ...
    GwasCatalogParseError: Strange 95% CI: - 7.90 [NR] (msec difference between homozygotes)
    """

    if text == '':
        return '', ''

    # 1. Try to parse to CI and unit
    founds = re.findall(r'([^\[\(]*)[\s\[\(]*(NR|[-\d\.]*[\s\,-]+[-\d\.]*)[\s\]\)]*(.*)', text)

    if len(founds) > 0:
        unit_a, ci, unit_b = founds[0]
        ci = ci.strip()

        if ci in ('NR'):
            ci = ''

        unit = ' '.join([unit_a.strip(), unit_b.strip()]).strip()
    else:
        # 2. Try to parse to unit (without CI)
        founds = re.findall(r'[^\d\s\.\,-]+', text)

        if len(founds) > 0:
            ci = ''
            unit = founds[0].strip()
        else:
            raise GwasCatalogParseError('Strange 95% CI: {}'.format(text))

    # Validation
    if re.match(r'[\d\s\.\,-]+', unit):  # unit contains digits?
        raise GwasCatalogParseError('Strange 95% CI: {}'.format(text))

    return ci, unit
