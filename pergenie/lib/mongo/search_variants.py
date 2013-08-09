from pymongo import MongoClient
from search_catalog import search_catalog_by_query
from django.conf import settings


def search_variants(user_id, file_name, file_format, query, query_type=None, mongo_port=27017):
    with MongoClient(host=settings.MONGO_URI) as c:
        variants = c['pergenie']['variants'][user_id][file_name]
        catalog_records = search_catalog_by_query(query, query_type=query_type).sort('trait', 1)

        tmp_catalog_map = {}
        found_id = 0
        snps_all = set()
        for record in catalog_records:
            snps_all.update([record['snps']])

            # snps = ', '.join(map(str, record['snps']))
            reported_genes = ', '.join([gene['gene_symbol'] for gene in record['reported_genes']])
            mapped_genes = ', '.join([gene['gene_symbol'] for gene in record['mapped_genes']])

            found_id += 1
            tmp_catalog_map[found_id] = record
            tmp_catalog_map[found_id].update({'rs':record['snps'],
                                              'reported_genes':reported_genes,
                                              'mapped_genes':mapped_genes,

                                              'chr':record['chr_id'],
                                              'freq':record['risk_allele_frequency'],

                                              'added':record['added'].date(),
                                              'date':record['date'].date()
                                              })

        variants_records = variants.find({'rs': {'$in': list(snps_all)}})

        # in catalog & in variants
        tmp_variants_map = {}
        for record in variants_records:
            # print 'in catalog & in variants', record['rs']
            # tmp_variants_map[record['rs']] = {'genotype':record['genotype']}
            tmp_variants_map[record['rs']] = record['genotype']

        # in catalog, but not in variants. so genotype is homozygous of `ref` or `na`.
        na = 'na'
        for found_id, catalog_map in tmp_catalog_map.items():
            rs = catalog_map['rs']
            ref = catalog_map['ref']

            if rs and (not rs in tmp_variants_map):
                if file_format == 'andme':
                    tmp_variants_map[rs] = na
                elif file_format == 'vcf_whole_genome':
                    tmp_variants_map[rs] = ref * 2
                elif file_format == 'vcf_exome_truseq':
                    if catalog_map['is_in_truseq']:
                        tmp_variants_map[rs] = ref * 2
                    else:
                        tmp_variants_map[rs] = na
                elif file_format == 'vcf_exome_iontargetseq':
                    if catalog_map['is_in_iontargetseq']:
                        tmp_variants_map[rs] = ref * 2
                    else:
                        tmp_variants_map[rs] = na

    # print for debug
    for found_id, catalog_map in tmp_catalog_map.items():
        rs = catalog_map['rs']
        variant = tmp_variants_map.get(rs)

        if int(found_id) < 10:
            print found_id, rs, catalog_map.get('trait'), catalog_map.get('risk_allele'), catalog_map.get('freq'), catalog_map.get('OR_or_beta'),
            print variant
        elif int(found_id) == 10:
            print 'has more...'

    return tmp_catalog_map, tmp_variants_map

        # only for query_type == rs,
        # not in catalog, but in variants
        #
        # TODO
        #

        # return tmp_catalog_map, tmp_variants_map
