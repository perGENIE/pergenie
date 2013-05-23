import pymongo

with pymongo.MongoClient() as c:
    db = c['pergenie']
    andme_snps = db['andme_snps']

    print andme_snps.find_one({'index': 2000})
    print andme_snps.find_one({'rs': 2857290})
