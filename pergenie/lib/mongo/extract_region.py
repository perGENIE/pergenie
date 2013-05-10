import sys, os
try:
    import cPickle as pickle
except ImportError:
    import pickle

def extract_region(region_file, records):
    """Extract record in region.

    * This function may require large memory...

    Example:
    # 1:14363-14829
    >>> region_path = "/Users/numa/Dropbox/py/pergenie_staging/pergenie/data/exome_region_file/TruSeq-Exome-Targeted-Regions-BED-file.1.interval_list"
    >>> records = [{'chr_pos':14362}, \
                   {'chr_pos':14363}, \
                   {'chr_pos':14364}, \
                   {'chr_pos':14829}, \
                   {'chr_pos':14830}]
    >>> extract_region(region_path, records)
    [{'chr_pos': 14363}, {'chr_pos': 14364}, {'chr_pos': 14829}]
    """

    region = set()

    if not os.path.exists(region_file + '.p'):
        with open(region_file, 'r') as fin:
            for line in fin:
                start, stop = line.split(':')[1].split('-')
                for pos in range(int(start), int(stop)+1):
                    region.update([pos])

        pickle.dump(region, open(region_file + '.p', 'w'), protocol=2)

    else:
        region = pickle.load(open(region_file + '.p'))

    # for r in records:
    #     print >>sys.stderr, r['chr_pos'], bool(r['chr_pos'] in region)

    return [r for r in records if r['chr_pos'] in region]


if __name__=='__main__':
    import doctest
    doctest.testmod()
