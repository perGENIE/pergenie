# -*- coding: utf-8 -*-

import pymongo
from django.conf import settings


def get_traits_infos(as_dict=False):
    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        trait_info = connection['pergenie']['trait_info']

        founds = trait_info.find({})
        traits = set([found['eng'] for found in founds])
        traits_ja = [trait_info.find_one({'eng': trait})['ja'] for trait in traits]
        traits_category = [trait_info.find_one({'eng': trait})['category'] for trait in traits]

        #
        traits_wiki_url_en = list()
        for trait in traits:
            t = trait_info.find_one({'eng': trait})['wiki_url_en']
            if t:
                t = t['wiki_url_en']
            else:
                t = ''
            traits_wiki_url_en.append(t)

        if not as_dict:
            return traits, traits_ja, traits_category, traits_wiki_url_en

        elif as_dict:
            return traits, dict(zip(traits, traits_ja)), dict(zip(traits, traits_category)), dict(zip(traits, traits_wiki_url_en))
