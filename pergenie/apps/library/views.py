import sys, os
from pprint import pprint
import pymongo
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils import translation
from django.utils.translation import ugettext as _
from django.conf import settings
from models import *

from lib.utils.io import pickle_load_obj
from lib.api.gwascatalog import GWASCatalog
gwascatalog = GWASCatalog()
from lib.utils.clogging import getColorLogger
log = getColorLogger(__name__)

TRAITS, TRAITS_JA, TRAITS_CATEGORY, TRAITS_WIKI_URL_EN = gwascatalog.get_traits_infos()


@login_required
def index(request):
    msg, err = '', ''

    latest_catalog_date = gwascatalog.get_latest_catalog_date()

    return direct_to_template(request, 'library/index.html',
                              dict(msg=msg, err=err,
                                   dbsnp_version=settings.DBSNP_VERSION, refgenome_version=settings.REFGENOME_VERSION,
                                   latest_catalog_date=latest_catalog_date))


@login_required
def summary_index(request):
    err = ''

    # TODO: error handling ?
    catalog_summary = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'catalog_summary.p'))
    field_names = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'field_names.p'))

    catalog_uniqs_counts = {}

    for field_name in field_names:
        uniqs = catalog_summary.get(field_name[0])

        if uniqs:
            catalog_uniqs_counts[field_name] = len(uniqs)

    log.debug('catalog_uniqs_counts', catalog_uniqs_counts)

    return direct_to_template(request, 'library/summary_index.html',
                              {'err': err,
                               'catalog_uniqs_counts': catalog_uniqs_counts})


@login_required
def summary(request, field_name):
    err = ''

    catalog_summary = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'catalog_summary.p'))
    uniqs_counts = catalog_summary.get(field_name)

    # TODO: 404?
    if not uniqs_counts:
        err = 'not found'
        uniqs_counts = {}

    return direct_to_template(request, 'library/summary.html',
                              {'err': err,
                               'uniqs_counts': uniqs_counts,
                               'field_name': field_name})


@login_required
def trait_index(request):
    msg, err = '', ''
    is_ja = bool(translation.get_language() == 'ja')

    return direct_to_template(request, 'library/trait_index.html',
                              dict(msg=msg, err=err,
                                   is_ja=is_ja,
                                   traits=TRAITS, traits_ja=TRAITS_JA, traits_category=TRAITS_CATEGORY,
                                   wiki_url_en=TRAITS_WIKI_URL_EN))


@login_required
def trait(request, trait):
    user_id = request.user.username
    msg, err = '', ''
    library_list, variants_maps = list(), dict()

    if not trait in TRAITS:
        err += 'trait not found'

    else:
        library_list = gwascatalog.search_catalog_by_query(trait, 'trait')

    log.error(err)

    return direct_to_template(request, 'library/trait.html',
                              dict(msg=msg, err=err,
                                   trait_name=trait,
                                   library_list=library_list,
                                   variants_maps=variants_maps))


@login_required
def snps_index(request):
    msg, err = '', ''
    uniq_snps_list = gwascatalog.get_uniq_snps_list()

    return direct_to_template(request,
                              'library/snps_index.html',
                              {'err': err,
                               'uniq_snps_list': uniq_snps_list
                               })


@login_required
def snps(request, rs):
    """
    /library/snps/rs(\d+)
    """
    try:
        rs = int(rs)
    except ValueError:
        # 404
        pass

    user_id = request.user.username
    msg, err = '', ''
    bq = Bioq(settings.DATABASES['bioq']['HOST'],
              settings.DATABASES['bioq']['USER'],
              settings.DATABASES['bioq']['PASSWORD'],
              settings.DATABASES['bioq']['NAME'])

    with pymongo.MongoClient(host=settings.MONGO_URI) as c:
        db = c['pergenie']
        data_info = db['data_info']
        uploadeds = list(data_info.find({'user_id': user_id}))
        file_names = [uploaded['name'] for uploaded in uploadeds]

        # data from uploaded files
        variants = {}
        for file_name in file_names:
            variant = db['variants'][user_id][file_name].find_one({'rs': rs})
            variants[file_name] = variant['genotype'] if variant else 'NA'

        # data from dbsnp
        dbsnp = c['dbsnp']['B132']
        dbsnp_record = dbsnp.find_one({'rs': rs})
        log.debug('dbsnp_record {0}'.format(dbsnp_record))

        # TODO: data from HapMap
        # * allele freq by polulation (with allele strand dbsnp oriented)
        # * LD data(r^2)

    # data from gwascatalog
    catalog_records = gwascatalog.get_catalog_records(rs)

    # TODO: replace bellow to info from dbSNP
    if len(catalog_records) > 0:
        catalog_record = catalog_records[0]
        if catalog_record['risk_allele_frequency']:
            catalog_record.update({'allele1': catalog_record['risk_allele'],
                                   'allele1_freq': catalog_record['risk_allele_frequency']*100,
                                   'allele2': 'other',
                                   'allele2_freq': (1 - catalog_record['risk_allele_frequency'])*100})
        else:
            err = 'allele frequency is not available...'
            catalog_record.update({'allele1': catalog_record['risk_allele'],
                                   'allele1_freq': None,
                                   'allele2': 'other',
                                   'allele2_freq': None})
    else:
        catalog_record = None

    omim_av_records = get_omim_av_records(rs)
    bq_allele_freqs, alleles = bq.get_allele_freqs(rs)

    pprint(bq_allele_freqs)

    bq_snp_summary = bq.get_snp_summary(rs)
    ref = bq_snp_summary['ancestral_alleles']

    # This may be buggy, when allele freq is not available...
    alleles.remove(ref)
    alts = list(alleles)
    seq = get_seq(bq_snp_summary['unique_chr'], bq_snp_summary['unique_pos_bp'])

    # Context
    # is in a gene
    if bq_snp_summary['rep_function']:
        context = bq_snp_summary['rep_function']
        gene_symbol = bq_snp_summary['rep_gene_symbol']
    # is in a intergenic region
    else:
        # TODO: create function/table which returns a context of each genomic positions.
        #       currently, using contexts in GWAS Catalog, for intergenic snps.
        if catalog_record:
            context = catalog_record['context']
            gene_symbol = catalog_record['mapped_genes']
        else:
            context = 'Intergenic'
            gene_symbol = ''

    return direct_to_template(request, 'library/snps.html',
                              dict(err=err, rs=rs, ref=ref, alts=alts,
                                   seq=seq, context=context, gene_symbol=gene_symbol,
                                   bq_allele_freqs=bq_allele_freqs,
                                   bq_snp_summary=bq_snp_summary,
                                   catalog_record=catalog_record,
                                   catalog_records=catalog_records,
                                   omim_av_records=omim_av_records,
                                   variants=variants,
                                   dbsnp_version=settings.DBSNP_VERSION,
                                   refgenome_version=settings.REFGENOME_VERSION))
