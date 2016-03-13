import os
import subprocess

from django.conf import settings

from utils import clogging
log = clogging.getColorLogger(__name__)


def project_new_person(src, genotype_bits, label):
    """Execute Rscript to project new person onto PCA coordinate
    """

    # TODO: try-catch

    cmd = ['Rscript', os.path.join(settings.BASE_DIR, 'lib', 'population', 'projection.r'), src] + genotype_bits + [label]
    print cmd
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].split()

    return [float(result[1]), float(result[2])]
