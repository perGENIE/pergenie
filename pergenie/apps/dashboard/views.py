"""
.. module:: views
   :synopsis: A useful module indeed.

"""

import sys, os
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.conf import settings

from lib.api.user import User
user = User()
from lib.api.genomes import Genomes
genomes = Genomes()
from lib.api.gwascatalog import GWASCatalog
gwascatalog = GWASCatalog()
from utils.clogging import getColorLogger
log = getColorLogger(__name__)


@login_required
def index(request):
    """This function does something.

    Args:
       name (str):  The name to use.

    Kwargs:
       state (bool): Current state to be in.

    Returns:
       int.  The return code::

          0 -- Success!
          1 -- No good.
          2 -- Try again.

    Raises:
       AttributeError, KeyError

    A really great idea.  A way you might use me is

    >>> print public_fn_with_googley_docstring(name='foo', state=None)
    0

    BTW, this always returns 0.  **NEVER** use with :class:`MyPublicClass`.

    """

    user_id = request.user.username
    msg, err, = '', ''
    intro_type = ''

    while True:
        gwascatalog.check_gwascatalog_imported()
        catalog_latest_new_records_data = gwascatalog.get_latest_added_date()
        recent_catalog_records = gwascatalog.get_recent_catalog_records()

        infos = genomes.get_data_infos(user_id)

        if user_id.startswith(settings.DEMO_USER_ID):
            tmp_user_info = user.get_user_info(user_id)
            if not tmp_user_info.get('last_viewed_file'):
                intro_type = 'demo_welcome'
            else:
                intro_type = 'demo_invitation'

        else:
            if not infos:
                intro_type = 'welcome'
                break

            # for info in infos:
            #     if not info['status'] == 100:
            #         intro_type = ['wait_upload']

        break

    msgs = dict(msg=msg, err=err,
                demo_user_id=settings.DEMO_USER_ID,
                catalog_latest_new_records_data=catalog_latest_new_records_data,
                recent_catalog_records=recent_catalog_records,
                infos=infos,
                intro_type=intro_type,
                is_registerable=settings.IS_REGISTERABLE)

    return render(request, 'dashboard/index.html', msgs)
