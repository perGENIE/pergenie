# def LD_block_clustering(risk_store, population_code):
#     """
#     LD block (r^2) clustering
#     -------------------------

#     * to avoid duplication of ORs

#       * use r^2 from HapMap by populaitons

#     """

#     risk_store_LD_clustered = {}

#     uniq_rs1_set = set()
#     with open('/Volumes/Macintosh HD 2/HapMap/LD_data/rs1_uniq/ld_CEU.rs1.uniq') as uniq_rs1s:
#         for uniq_rs1 in uniq_rs1s:
#             uniq_rs1_set.update([int(uniq_rs1.replace('rs', ''))])
#     print 'uniq_rs1_set', len(uniq_rs1_set)

#     with pymongo.Connection(port=HAPMAP_PORT) as connection:
#         db = connection['hapmap']
#         ld_data = db['ld_data']
#         ld_data_by_population_map = dict(zip(POPULATION_CODE, [ld_data[code] for code in POPULATION_CODE]))

#         for trait,rss in risk_store.items():
#             rs_LD_block_map = {}
#             risk_store_LD_clustered[trait] = {}
#             print trait

#             trait_rss = set(rss)
#             # print colors.red('# before trait_rss'), len(trait_rss)
#             print trait_rss

#             if rss:
#                 # print colors.yellow('# in ld_data (uniq_rs1)'), len(uniq_rs1_set.intersection(trait_rss))

#                 # fetch LD datas from mongo.hapmap.ld_data.POPULATION_CODE
#                 trait_ld_datas = ld_data_by_population_map[population_code].find( {'rs1': {'$in': list(trait_rss)} } )

#                 # LD block clustering
#                 if trait_ld_datas.count() > 0:
#                     for trait_ld_data in trait_ld_datas:

#                         # about rs1
#                         if not rs_LD_block_map:  # init
#                             rs_LD_block_map[trait_ld_data['rs1']] = 1

#                         elif not trait_ld_data['rs1'] in rs_LD_block_map:  # new block
#                             rs_LD_block_map[trait_ld_data['rs1']] = max(rs_LD_block_map.values()) + 1

#                         # about rs2
#                         if not trait_ld_data['rs2'] in rs_LD_block_map:
#                             if trait_ld_data['rs2'] in trait_rss:
#                                 rs_LD_block_map[trait_ld_data['rs2']] = rs_LD_block_map[trait_ld_data['rs1']]

# #                         print trait_ld_data['rs1'], trait_ld_data['rs2'], rs_LD_block_map

#                     # print colors.yellow('# in ld_data where r^2 > 0.8 & clusterd'), max(rs_LD_block_map.values())
#                     print rs_LD_block_map

#                     for rs in trait_rss:
#                         if not rs in rs_LD_block_map:
#                             rs_LD_block_map[rs] = max(rs_LD_block_map.values()) + 1

#                     # print colors.blue('# after trait_rss'), max(rs_LD_block_map.values())
#         #             for k,v in sorted(rs_LD_block_map.items(), key=lambda x:x[1]):
#         #                 print k,v

#                     # get one rs from each blocks
#                     one_rs_index = [rs_LD_block_map.values().index(i+1) for i in range(max(rs_LD_block_map.values()))]
#                     LD_blocked_rss = [rs_LD_block_map.items()[index][0] for index in one_rs_index]

#                     # save risk records of LD block clusterd rss
#                     for rs, catalog_record in rss.items():
# #                         print rss
#                         if rs in LD_blocked_rss:
#                             risk_store_LD_clustered[trait][rs] = catalog_record
# #                         else:
# #                             print 'filterd out record', catalog_record

#                 else:
#                     risk_store_LD_clustered[trait] = rss

#             else:
#                 risk_store_LD_clustered[trait] = rss

#             print


#     return risk_store_LD_clustered
