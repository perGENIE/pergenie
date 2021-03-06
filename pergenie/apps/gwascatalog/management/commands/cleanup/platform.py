import re


def get_platform(text):
    """
    >>> get_platform('Illumina [2,272,849] (imputed)')
    ['Illumina']
    >>> get_platform('Ilumina [475,157]')
    ['Illumina']
    >>> get_platform('Affymetrix & Illumina [2,217,510] (imputed)')
    ['Affymetrix', 'Illumina']
    >>> get_platform('Affymetrix[200,220]')
    ['Affymetrix']
    >>> get_platform('Afymetrix [287,554]')
    ['Affymetrix']
    >>> get_platform('Perlegen[438,784]')
    ['Perlegen']
    """
    if not text: return []

    result = set()
    regexps = [(re.compile('Il(|l)umina', re.I), 'Illumina'),
               (re.compile('Af(|f)ymetrix', re.I), 'Affymetrix'),
               (re.compile('Perlegen', re.I), 'Perlegen')]

    for regexp, vender in regexps:
        founds = regexp.findall(text)

        if founds: result.update([vender])

    return sorted(list(result))
