import re
import datetime
from xml.sax.saxutils import escape

from lib.utils import clogging
log = clogging.getColorLogger(__name__)


def _type(converter, text):
    if not text or text in ('NR', 'NS'):
        return None
    else:
        return converter(text)


def _date(text):
    return datetime.datetime.strptime(text, '%m/%d/%Y')


def _float(text):
    try:
        return float(text)
    except ValueError:
        match = re.match('\d*\.\d+', text)
        if match:
            return float(match.group())
        else:
            return None


def string_without_slash(text):
    text = escape(text)
    text = text.replace('/', '&#47;')  # FIXME
    return text


def snps(text):
    return [value.strip().replace('rs', '') for value in text.split(',')]


def ci_text(text):
    """Parse `95% CI (text)` in GWAS Catalog.

    Args:
    - `text`: value of `95% CI (text)`

    Returns:
    - {'CI': [float, float], 'text': ''}

    >>> res = _CI_text(''); res['CI'], res['text']
    ([], '')
    >>> res = _CI_text('NR'); res['CI'], res['text']
    ([], '')
    >>> res = _CI_text('NS'); res['CI'], res['text']
    ([], '')
    >>> res = _CI_text('[NR]'); res['CI'], res['text']
    ([], '')
    >>> res = _CI_text('[NR] unit increase]'); res['CI'], res['text']
    ([], 'unit increase]')
    >>> res = _CI_text('[0.091-0.169] unit decrease'); res['CI'], res['text']
    ([0.091, 0.169], 'unit decrease')
    >>> res = _CI_text(' hoge '); res['CI'], res['text']
    ([], 'hoge')
    """

    result = {'CI': [], 'text': ''}
    pattern_regular = re.compile('\[(-?\d+\.\d+)-(-?\d+\.\d+)\]\s*(.*)')
    pattern_ci_none_text = re.compile('\[(NR|NS)\]\s*(.*)')

    if not text or text in ('NR', 'NS', '[NR]', '[NS]'):
        return result

    match = pattern_regular.findall(text)
    if match:
        result['CI'] = [float(value) for value in match[0][0:2]]
        result['text'] = match[0][2].strip()
        return result

    match = pattern_ci_none_text.findall(text)
    if match:
        result['CI'] = []
        result['text'] = match[0][1].strip()
        return result

    result['text'] = text.strip()
    log.debug('CI and unit:')
    log.debug(result)

    return result


def platform(text):
    """
    >>> _platform('Illumina [2,272,849] (imputed)')
    ['Illumina']
    >>> _platform('Ilumina [475,157]')
    ['Illumina']
    >>> _platform('Affymetrix & Illumina [2,217,510] (imputed)')
    ['Affymetrix', 'Illumina']
    >>> _platform('Affymetrix[200,220]')
    ['Affymetrix']
    >>> _platform('Afymetrix [287,554]')
    ['Affymetrix']
    >>> _platform('Perlegen[438,784]')
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
