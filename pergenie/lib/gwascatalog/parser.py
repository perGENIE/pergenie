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


def str_without_slash(text):
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

    >>> res = ci_text(''); res['CI'], res['text']
    ([], '')
    >>> res = ci_text('NR'); res['CI'], res['text']
    ([], '')
    >>> res = ci_text('NS'); res['CI'], res['text']
    ([], '')
    >>> res = ci_text('[NR]'); res['CI'], res['text']
    ([], '')
    >>> res = ci_text('[NR] unit increase]'); res['CI'], res['text']
    ([], 'unit increase]')
    >>> res = ci_text(' hoge '); res['CI'], res['text']
    ([], 'hoge')

    >>> res = ci_text('[0.091-0.169]'); res['CI'], res['text']
    ([0.091, 0.169], '')
    >>> res = ci_text('[0.091-0.169] unit decrease'); res['CI'], res['text']
    ([0.091, 0.169], 'unit decrease')
    >>> res = ci_text('0.091-0.169] unit decrease'); res['CI'], res['text']
    ([0.091, 0.169], 'unit decrease')
    >>> res = ci_text('[0.091-0.169 unit decrease'); res['CI'], res['text']
    ([0.091, 0.169], 'unit decrease')
    >>> res = ci_text('0.091-0.169 unit decrease'); res['CI'], res['text']
    ([0.091, 0.169], 'unit decrease')

    >>> res = ci_text('[.02931-.0585] unit decrease'); res['CI'], res['text']
    ([0.02931, 0.0585], 'unit decrease')
    >>> res = ci_text('[.009684-0.02406] unit increase'); res['CI'], res['text']
    ([0.009684, 0.02406], 'unit increase')
    >>> res = ci_text('[0.42-1] unit decrease'); res['CI'], res['text']
    ([0.42, 1.0], 'unit decrease')
    >>> res = ci_text('[1-2.37] unit increase'); res['CI'], res['text']
    ([1.0, 2.37], 'unit increase')
    >>> res = ci_text('[4.58-287]'); res['CI'], res['text']
    ([4.58, 287.0], '')
    >>> res = ci_text('[1.41 - 2.39]'); res['CI'], res['text']
    ([1.41, 2.39], '')
    >>> res = ci_text('[1.46,2.33]'); res['CI'], res['text']
    ([1.46, 2.33], '')
    >>> res = ci_text('[1.16 1.43]'); res['CI'], res['text']
    ([1.16, 1.43], '')
    >>> res = ci_text('1.19-1.48]'); res['CI'], res['text']
    ([1.19, 1.48], '')
    >>> res = ci_text('[NR] kg/m2 per copy in adults'); res['CI'], res['text']
    ([], 'kg/m2 per copy in adults')

    # malformed records...
    >>> res = ci_text('- 7.90 [NR] msec difference between homozygotes'); res['CI'], res['text']
    ([], '- 7.90 [NR] msec difference between homozygotes')
    """
    result = {'CI': [], 'text': ''}
    pattern_regular = re.compile('\[?(-?\d*\.\d+|\d+)\s*[-|,|\s+]\s*(-?\d*\.\d+|\d+)\]?\s*(.*)')
    pattern_without_ci = re.compile('(\[(NR|NS)\]\s*)?(.*)')

    if not text:
        return result

    text = text.strip()

    if text in ('NR', 'NS', '[NR]', '[NS]'):
        return result

    match = pattern_regular.findall(text)
    if match:
        result['CI'] = [float(value) for value in match[0][0:2]]
        result['text'] = match[0][2].strip()
        return result

    match = pattern_without_ci.findall(text)
    if match:
        result['CI'] = []
        result['text'] = match[0][2].strip()
        return result


def platform(text):
    """
    >>> platform('Illumina [2,272,849] (imputed)')
    ['Illumina']
    >>> platform('Ilumina [475,157]')
    ['Illumina']
    >>> platform('Affymetrix & Illumina [2,217,510] (imputed)')
    ['Affymetrix', 'Illumina']
    >>> platform('Affymetrix[200,220]')
    ['Affymetrix']
    >>> platform('Afymetrix [287,554]')
    ['Affymetrix']
    >>> platform('Perlegen[438,784]')
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
