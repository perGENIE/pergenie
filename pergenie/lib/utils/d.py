def join(d1, d2):
    '''Join two dict on d1.value = d2.key

    >>> d1 = {1:2}
    >>> d2 = {2:3}
    >>> join(d1, d2)
    {1: 3}
    '''
    d1 = dict(d1)
    d2 = dict(d2)

    return {k1:d2.get(v1) for k1,v1 in d1.items()}
