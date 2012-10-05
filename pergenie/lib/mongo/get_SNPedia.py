#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import wikitools
import argparse

"""
ref: http://www.snpedia.com/index.php/Bulk
"""


class GetSNPedia(object):
    def __init__(self):
        self.site = wikitools.wiki.Wiki("http://bots.snpedia.com/api.php") # open snpedia
        self.snps = wikitools.category.Category(self.site, "Is_a_snp")
        self.snpedia = []
       
    def get_all_SNP_names(self):
        for article in self.snps.getAllMembersGen(namespaces=[0]): # get all snp-names as list and print them
            self.snpedia.append(article.title.lower())
            print article.title

    def grab_a_single_SNP_page_in_full_text(self, snp):
        pagehandle = wikitools.page.Page(self.site, snp)
        snp_page = pagehandle.getWikiText()
        print snp_page

def main():
    parser = argparse.ArgumentParser(description=('return SNPedia raw record.'))
    parser.add_argument('--rs')
    parser.add_argument('--all_rs', action='store_true')
    args = parser.parse_args()

    g = GetSNPedia()

    if args.all_rs:
        g.get_all_SNP_names()
        
    if args.rs:
        g.grab_a_single_SNP_page_in_full_text(args.rs)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    main()
