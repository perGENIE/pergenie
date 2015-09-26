def catalog_statistics():
    pass
    # TODO:

    # catalog_cover_rate = db['catalog_cover_rate']
    # if catalog_cover_rate.find_one(): db.drop_collection(catalog_cover_rate)
    # assert catalog_cover_rate.count() == 0

    # # Add region flags `is_in_*`
    # n_counter, n_counter_uniq = defaultdict(int), defaultdict(int)
    # for chrom in settings.INT_CHROMS:
    #     log.info('Addding flags... chrom: {0}'.format(chrom))

    #     records = list(catalog.find({'chr_id': chrom}).sort('chr_pos', pymongo.ASCENDING))
    #     ok_records = [rec for rec in records if rec['snp_id_current']]
    #     uniq_snps = set([rec['snp_id_current'] for rec in ok_records])
    #     n_counter['records'] += len(ok_records)
    #     n_counter_uniq['records'] += len(uniq_snps)

    #     chrom = {23: 'X', 24:'Y'}.get(chrom, chrom)

    # log.info('records: %s' % n_counter['records'])
    # log.info('records uniq: %s' % n_counter_uniq['records'])
    # for file_format in settings.FILEFORMATS:
    #     if file_format['name'] == 'vcf_whole_genome': continue
    #     log.info('`is_in_%s` extracted: %s' % (file_format['short_name'], n_counter[file_format['short_name']]))

    # # Cover rate for GWAS Catalog
    # for _counter,_name in [(n_counter, ''), (n_counter_uniq, '_uniq')]:
    #     _stats = {}
    #     for file_format in settings.FILEFORMATS:
    #         if file_format['name'] == 'vcf_whole_genome':
    #             _stats.update({'vcf_whole_genome': 100})
    #         else:
    #             _stats.update({file_format['name']: round(100 * _counter[file_format['short_name']] / float(_counter['records']))})
    #     catalog_cover_rate.insert({'stats': 'catalog_cover_rate' + _name, 'values': _stats})

    # # Cover rate for whole genome
    # len_regions = {
    #     'genome': 2861327131,  # number of bases (exclude `N`)
    #     'truseq': 62085286,  # FIXME: this region may contain N region, so it may not be fair
    #     'andme': 1022124,
    #     'iontargetseq': 47302058,
    #     'sureselect_v5_plus': 113687898,
    # }
    # catalog_cover_rate.insert({'stats': 'genome_cover_rate',
    #                            'values': {'vcf_whole_genome': 100,
    #                                       'vcf_exome_truseq': int(round(100 * len_regions['truseq'] / len_regions['genome'])),
    #                                       'andme': int(round(100 * len_regions['andme'] / len_regions['genome'])),
    #                                       'vcf_exome_iontargetseq': int(round(100 * len_regions['iontargetseq'] / len_regions['genome'])),
    #                                       'vcf_exome_sureselect_v5_plus': int(round(100 * len_regions['sureselect_v5_plus'] / len_regions['genome']))
    #                                       }
    #                            })

    # log.info(pformat(list(catalog_cover_rate.find())))
