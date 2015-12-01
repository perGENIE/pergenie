import re


def get_population(text):
    """Parse `initial_sample_size` in GWAS Catalog,
    then return a list of combination of
    'European', 'EastAsian', 'African', 'Japanese', e.g.:

    >>> get_population('European and Asian and African')
    ['African', 'EastAsian', 'European']

    If uncategorized:

    >>> get_population('foo')
    []

    E.g.:

    >>> get_population('815 related Hispanic ancestry children from 263 families')
    ['European']
    >>> get_population('133,653 European ancestry individuals')
    ['European']
    >>> get_population('5,560 European ancestry women and 4,997 European ancestry men')
    ['European']
    >>> get_population('12,924 European ancestry cases, 21,442 European ancestry controls')
    ['European']
    >>> get_population('651 European American bipolar cases, 1,171 European American schizophrenia cases, 2,412 European American controls')
    ['European']
    >>> get_population('up to 398 European individuals')
    ['European']
    >>> get_population('1 American Indian ancestry individual, 18 African American/Afro-Caribbean ancestry individuals, 10 East Asian and South Asian ancestry individuals, 325 European ancestry individuals, 17 Latin American ancestry individuals, 6 other ancestry individuals, 4 individuals')
    ['African', 'EastAsian', 'European']
    >>> get_population('Up to 512 European ancestry individuals, up to 199 African American individuals')
    ['African', 'European']
    >>> get_population('9,772 European ancestry cases, 16,849 European ancestry controls')
    ['European']
    >>> get_population('9,617 individuals')
    []
    >>> get_population('Up to 813 European ancestry individuals, up to 167 East Asian ancestry individuals, up to 7 Hispanic/Latin American amncestry individuals, up to 74 South Asian ancestry individuals')
    ['EastAsian', 'European']
    >>> get_population('4,723 cases, 4,792 controls')
    []
    >>> get_population('7,943 African American children, 6,234 European ancestry children')
    ['African', 'European']
    >>> get_population('99,900 European descent individuals')
    ['European']
    >>> get_population('62,553 European ancestry individuals, 9,308 South Asian ancestry individuals')
    ['EastAsian', 'European']
    >>> get_population('Up to 52,350 European ancestry individuals, up to 8,739 Indian Asian individuals')
    ['EastAsian', 'European']
    >>> get_population('2,362 Caucasian cases')
    ['European']
    >>> get_population('4,533 European descent cases, 10,750 European descent controls')
    ['European']
    >>> get_population('12,545 Korean ancestry individuals')
    ['EastAsian']
    >>> get_population('217 African American ancestry individuals, 580 European ancestry individuals, 217 Hispanic ancestry individuals')
    ['African', 'European']
    >>> get_population('738 European American, African American, and other schizophrenia cases')
    ['African', 'European']
    >>> get_population('1,656 Han Chinese cases, 3,394 Han Chinese controls')
    ['EastAsian']
    >>> get_population('96 African American lymphoblastoid cell lines, 96 European ancestry lymphoblastoid cell lines, 96 Han Chinese lymphoblastoid cell lines')
    ['African', 'EastAsian', 'European']
    >>> get_population('1,792 Filipino women')
    ['EastAsian']
    >>> get_population('13,057 European ancestry individuals, 2,538 Indian ancestry individuals, 2,542 Malay ancestry individuals, 1,883 Chinese ancestry individuals')
    ['EastAsian', 'European']
    >>> get_population('19,633 Japanese individuals')
    ['EastAsian', 'Japanese']
    >>> get_population('1,141 individuals(Framingham))')
    ['European']
    >>> get_population('1,368 Australian twins, 848 UK individuals')
    ['European']
    >>> get_population('Up to 84 East Asian ancestry lymphoblastoid cell lines, up to 164 European ancestry lymphoblastoid cell lines, up to 173 African ancestry lymphoblastoid cell lines, up to 82 African American lymphoblastoid cell lines')
    ['African', 'EastAsian', 'European']
    >>> get_population('851 Old Order Amish individuals')
    ['European']
    >>> get_population('737 Ashkenazi Jewish cases, 2,257 Ashkenazi Jewish controls')
    ['European']
    >>> get_population('Up to 53,190 European ancestry individuals, 9,380 Japanese ancestry individuals')
    ['EastAsian', 'European', 'Japanese']
    >>> get_population('1,649 Australian siblings, 3,196 Australian twins, 16,140 European descent individuals')
    ['European']
    >>> get_population('39,717 Japanese, Korean, and Chinese ancestry individuals')
    ['EastAsian', 'Japanese']
    >>> get_population('430 Icelandic and Swedish cases, 1,090 Icelandic and Swedish controls')
    ['European']
    >>> get_population('Human lymphoblastoid cell lines from 93 African Americans, 89 Caucasian-Americans, and 95 Han Chinese Americans')
    ['African', 'EastAsian', 'European']
    >>> get_population('28,283 white individuals')
    ['European']
    >>> get_population('3,972 Italian individuals, 839 European ancestry individuals')
    ['European']
    >>> get_population('1,999 Chinese Han men')
    ['EastAsian']
    >>> get_population('1,694 British cases, 2,365 British controls, 1,145 European ancestry cases, 1,142 European ancestry controls')
    ['European']
    >>> get_population('1,822 Croatian individuals, 737 Scottish individuals')
    ['European']
    >>> get_population('1,354 Mexican-American family members')
    ['European']
    >>> get_population('1,583 Southern Chinese descent cases, 972 Southern Chinese descent controls, 922 Singapore Chinese controls')
    ['EastAsian']
    >>> get_population('15,757 Icelandic men')
    ['European']
    >>> get_population('374 non-Hispanic Caucasians')
    ['European']
    >>> get_population('7,739 Chinese ancestry individuals, 2,194 Japanese ancestry individuals, 8,838 Korean ancestry individuals, 2,522 Malay ancestry individuals, 1,999 Han Chinese individuals, 1,992 Singapore Chinese individuals, 2,431 Chinese, Malay and Asian Indian individuals')
    ['EastAsian', 'Japanese']
    >>> get_population('778 European ancestry cases, 4,414 European ancestry controls, 242 Ashkenazi Jewish cases, 354 Ashkenazi Jewish controls, 265 French Canadian cases, 196 French Canadian controls')
    ['European']
    >>> get_population('1,043 German cases, 1,703 German controls')
    ['European']
    >>> get_population('1,101 Indo-European ancestry cases, 1,027 Indo-European ancestry controls')
    ['European']
    >>> get_population('435 Turkish cases with uveitis, 780 Turkish cases without uveitis, 1,278 Turkish controls')
    ['European']
    >>> get_population('848 Malawian cases, 531 Malawian controls')
    ['African']
    >>> get_population('9,849 European ancestry individuals, 894 African ancestry individuals, 271 other ancestry individuals')
    ['African', 'European']
    >>> get_population('1,194 Chinese ancestry cases, 902 Chinese ancestry controls')
    ['EastAsian']
    >>> get_population('5,568 European ancestry cases, 7,187 European ancestry controls, 1,000 Taiwanese cases, 1,000 Taiwanese controls')
    ['EastAsian', 'European']
    >>> get_population('60 Caucasian American lymphoblastoid cell lines, 56 African- American lymphoblastoid cell lines, 60 Han Chinese-American lymphoblastoid cell lines')
    ['African', 'EastAsian', 'European']
    >>> get_population('984 Singaporean Chinese cases, 943 Singaporean Chinese controls, 297 Han Chinese cases, 1,044 Han Chinese controls, 573 South Asian ancestry cases, 3,065 Singaporean Malay controls, 2,538 Singaporean Asian Indian controls, 2,018 Vietnamese ancestry controls.')
    ['EastAsian']
    >>> get_population('2,008 Vietnamese ancestry cases, 2,018 Vietnamese ancestry controls')
    ['EastAsian']
    >>> get_population('2,684 Asian Indian men')
    ['EastAsian']
    >>> get_population('2,903 Icelandic CKD cases, 35,818 Icelandic controls, 22,256 Icelandic subjects with serum creatinine')
    ['European']
    >>> get_population('293 family members, 391 white non-Hispanic cases, 188 white non-Hispanic controls')
    ['European']
    >>> get_population('Romanian')
    ['European']
    >>> get_population('1,279 European ancestry cases, 5,139 European ancestry controls, 93 South African Afrikaner cases, 158 South African Afrikaner controls, 93 Ashkenazi Jewish cases, 260 Ashkenazi Jewish controls, 299 European ancestry trios, 101 trios')
    ['European']
    >>> get_population('1,399 EA cases,5,275 EA controls')
    ['European']
    >>> get_population('1,644 Dutch individuals, 978 European individuals')
    ['European']
    >>> get_population('1,683 Indonesian ancestry individuals')
    ['EastAsian']
    >>> get_population('235 mild Thai-Chinese cases, 383 severe Thai-Chinese cases')
    ['EastAsian']
    >>> get_population('315 Hong Kong Chinese individuals from 111 families')
    ['EastAsian']
    >>> get_population('431 European American cases, 340 European American controls, 209 African American cases, 84 African American controls')
    ['African', 'European']
    >>> get_population('62 American Indian or Alaska Native ancestry individuals, 158 Asian ancestry individuals, 3,272 African American ancestry individuals, 114 other ancestry individuals, 23,244 European ancestry individuals, 996 unknown ancestry individuals')
    ['African', 'EastAsian', 'European']
    >>> get_population('815 Hispanic/Latin American ancestry children')
    ['European']
    >>> get_population('1,138 French and German extremely obese children, 1,120 French and German normal or underweight children')
    ['European']
    >>> get_population('2,346 Micronesian individuals')
    ['EastAsian']
    >>> get_population('332 Scandinavian cases, 262 Scandinavian controls, 383 German cases, 2,700 German controls')
    ['European']
    >>> get_population('347 Finnish Saami individuals')
    ['European']
    >>> get_population('462 Hutterite individuals')
    []
    >>> get_population('810-1,010 individualsdepending on measure(Framingham)')
    ['European']
    >>> get_population('882 Sardinian cases, 872 Sardinian controls')
    ['European']
    >>> get_population('1,015 Swiss chronic HCV patients, 347 Swiss spontaneously cleared HCV patients')
    ['European']
    >>> get_population('379 Danish and Swedish cases, 791 Danish and Swedish controls')
    ['European']
    >>> get_population('4,270 UK twins')
    ['European']
    >>> get_population('667 European ancestry individuals with an event, 2,246 European ancestry individuals without an event, 18 African American individuals with an event, 60 African American individuals without an event, 20 Hispanic ancestry individuals with an event, 65 Hispanic ancestry individuals without an event, 6 Asian, Pacific or other ancestry individuals with an event, 27 Asian, Pacific or other ancestry individuals without an event')
    ['African', 'EastAsian', 'European']
    >>> get_population('785 Hong Kong Southern Chinese (HSKC) extreme BMD females)')
    ['EastAsian']
    >>> get_population('Sorbian')
    ['European']
    >>> get_population('837 Mexican-American cases, 781 Mexican-American controls')
    ['European']
    >>> get_population('857 Mexican Americans')
    ['European']
    >>> get_population('96 Southeast Asian cases,130 Southeast Asian controls')
    ['EastAsian']
    """
    result = set()

    # TODO: research about `human classification`

    # ? Hispanic
    # ? Mexican-American
    # ? Hispanic/Latin American

    # ? Native American
    # ? Indo-European  # Celts?

    # ? Hutterite
    # ? South African Afrikaner

    # ? Australian

    regexps = [(re.compile(' European ((|ancestry|descent)|(|individual(|s)))', re.I), 'European'),
               (re.compile('European American', re.I), 'European'),
               (re.compile('Caucasian', re.I), 'European'),
               (re.compile('white', re.I), 'European'),
               (re.compile(' EA '), 'European'),
               (re.compile('Australian', re.I), 'European'),
               (re.compile('UK', re.I), 'European'),
               (re.compile('British', re.I), 'European'),
               (re.compile('Framingham', re.I), 'European'),
               (re.compile('Amish', re.I), 'European'),
               (re.compile('Ashkenazi Jewish', re.I), 'European'),
               (re.compile('French', re.I), 'European'),
               (re.compile('Italian', re.I), 'European'),
               (re.compile('German', re.I), 'European'),
               (re.compile('Croatian', re.I), 'European'),
               (re.compile('Scottish', re.I), 'European'),
               (re.compile('Icelandic', re.I), 'European'),
               (re.compile('Romanian', re.I), 'European'),
               (re.compile('Dutch', re.I), 'European'),
               (re.compile('Danish', re.I), 'European'),
               (re.compile('Swedish', re.I), 'European'),
               (re.compile('Scandinavian', re.I), 'European'),
               (re.compile('Finnish', re.I), 'European'),
               (re.compile('Sardinian', re.I), 'European'),
               (re.compile('Swiss', re.I), 'European'),
               (re.compile('Sorbian', re.I), 'European'),

               (re.compile('Turkish', re.I), 'European'),
               (re.compile('Hispanic ancestry', re.I), 'European'),
               (re.compile('Hispanic\/', re.I), 'European'),
               (re.compile('Mexican( |-)American(|s)', re.I), 'European'),
               (re.compile('Indo-European', re.I), 'European'),

               (re.compile('[^South] African ((|ancestry|descent)|(|individual(|s)))', re.I), 'African'),
               (re.compile('[^South] African(|-) American', re.I), 'African'),
               (re.compile('Malawian', re.I), 'African'),

               (re.compile('(|East|South|Indian|Southeast) Asian', re.I), 'EastAsian'),
               (re.compile('Korean', re.I), 'EastAsian'),
               (re.compile('Taiwanese', re.I), 'EastAsian'),
               (re.compile('Indonesian', re.I), 'EastAsian'),
               (re.compile('Micronesian', re.I), 'EastAsian'),
               (re.compile('Han Chinese', re.I), 'EastAsian'),
               (re.compile('Chinese Han', re.I), 'EastAsian'),
               (re.compile('Southern Chinese', re.I), 'EastAsian'),
               (re.compile('Indian', re.I), 'EastAsian'),
               (re.compile('Malay', re.I), 'EastAsian'),
               (re.compile(' Chinese', re.I), 'EastAsian'),
               (re.compile('Thai-Chinese', re.I), 'EastAsian'),
               (re.compile('Filipino', re.I), 'EastAsian'),
               (re.compile('Vietnamese', re.I), 'EastAsian'),
               (re.compile('Japanese', re.I), 'EastAsian'),

               (re.compile('Japanese', re.I), 'Japanese'),
           ]

    for regexp, population in regexps:
        founds = regexp.findall(text)

        if founds:
            result.update([population])

    return sorted(list(result))
