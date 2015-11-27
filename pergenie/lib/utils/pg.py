def list2pg_array(l):
    """
    >>> list2pg_array([])
    {}
    >>> list2pg_array(['A', 'B'])
    {A,B}
    >>> list2pg_array(['A', 'B', 'C'])
    {A,B,C}
    """

    assert type(l) == list

    if len(l) == 0:
        return '{}'
    else:
        return '{' + ','.join(l)  +'}'

def text2pg_array(text):
    """
    >>> pg_array('')
    {}
    >>> pg_array('{A}')
    {A}
    >>> pg_array('A')
    {A}
    """

    assert type(text) == str

    if text == '':
        return '{}'
    elif text.startswith('{') and text.endswith('}'):
        return text
    else:
        return '{' + text + '}'
