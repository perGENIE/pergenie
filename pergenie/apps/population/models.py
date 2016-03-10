from lib.r.r import projection
from django.conf import settings
import pymongo


def project_new_person(scale, info):
    """Project new person onto PCA coordinate.

    args: str(scale)
          data_info: {'user_id': '', 'name': '', ...}
    retval: {'position': [x, y], 'label': '', 'map_label': ''}
    """

    # TODO: currently only for `global` scale
    if scale in ('global'):
        record = {'position': projection(scale, info),
                  'label': info['name'],
                  'map_label': ''}
    else:
        record = None

    return record


def get_people(scale):
    """Get points of people in PCA coordinate.

    args: str(scale)
    retval: list(list(), ...)
    """
    popcode2global = {'CHB': 'EastAsia', 'JPT': 'EastAsia', 'CHS': 'EastAsia',
                      'CEU': 'Europe', 'TSI': 'Europe', 'GBR': 'Europe', 'FIN': 'Europe', 'IBS': 'Europe',
                      'YRI': 'Africa', 'LWK': 'Africa', 'ASW': 'Africa',
                      'MXL': 'Americas', 'CLM': 'Americas', 'PUR': 'Americas'}

    with pymongo.MongoClient(host=settings.MONGO_URI) as c:
        db = c['pergenie']
        col = db['population_pca'][scale]

        if scale == 'global':
            records = [{'position': rec['position'],
                        'label': popcode2global[rec['popcode']],
                        'map_label': rec['popcode']} for rec in col.find()]
        else:
            records = [{'position': rec['position'],
                        'label': rec['popcode'],
                        'map_label': rec['popcode']} for rec in col.find()]

        return records
