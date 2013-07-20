# -*- coding: utf-8 -*-

import sys, os
import glob
import pymongo


def import_population_pca(settings, ):
    with pymongo.MongoClient(host=settings.MONGO_URI) as c:
        db = c['pergenie']
        population_pca = db['population_pca']

        # # Import original metrix data .csv
        # for src in glob.glob(os.path.join(settings.PATH_TO_POPULATION_PCA, '*.csv')):
        #     with open(src, 'r') as f:
        #         pass

        # Import genometric points of people in each PCA coordinate.
        for src in glob.glob(os.path.join(settings.PATH_TO_POPULATION_PCA, '*.geo')):
            col = population_pca[os.path.basename(src).replace('.geo', '').replace('.', '_')]
            if col.find_one(): db.drop_collection(col)

            with open(src, 'r') as f:
                for line in f:
                    num, pc1, pc2, popcode = line.rstrip().split(',')
                    if num == '': continue
                    col.insert({'popcode': popcode, 'loc': [float(pc1), float(pc2)]})

                col.ensure_index([('loc', pymongo.GEO2D), ('popcode', pymongo.ASCENDING)])
