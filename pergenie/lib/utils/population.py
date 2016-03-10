from django.utils.translation import ugettext as _


POPULATION_UNKNOWN = 'UN'
POPULATION_GLOBAL = 'GL'
POPULATION_EAST_ASIAN = 'EAS'
POPULATION_EUROPEAN = 'EUR'
POPULATION_AFRICAN = 'AFR'
POPULATION_JAPANESE = 'JPN'
POPULATION_CHOICES = [
    (POPULATION_UNKNOWN,    _('Unknown')),
    # (POPULATION_GLOBAL,     _('Global')),
    (POPULATION_EAST_ASIAN, _('EastAsian')),
    (POPULATION_EUROPEAN,   _('European')),
    (POPULATION_AFRICAN,    _('African')),
    # (POPULATION_JAPANESE,   _('Japanese')),
]
POPULATION_MAP = {x[0]:x[1] for x in POPULATION_CHOICES}
POPULATION_MAP_REVERSE = {x[1]:x[0] for x in POPULATION_CHOICES}

POPCODE2GLOBAL = {'CHB': 'EastAsia', 'JPT': 'EastAsia', 'CHS': 'EastAsia',
                  'CEU': 'Europe', 'TSI': 'Europe', 'GBR': 'Europe', 'FIN': 'Europe', 'IBS': 'Europe',
                  'YRI': 'Africa', 'LWK': 'Africa', 'ASW': 'Africa',
                  'MXL': 'Americas', 'CLM': 'Americas', 'PUR': 'Americas'}
