def _identfy_OR_or_beta(OR_or_beta, CI_95):
    if CI_95['text']:
        # TODO: convert beta to OR if can
        OR = 'beta:{0}'.format(OR_or_beta)

    else:
        if OR_or_beta:
            OR = float(OR_or_beta)

            #
            if OR < 1.0:  # somehow beta without text in 95% CI ?
                OR = 'beta:{0}?'.format(OR_or_beta)

        else:
            OR = None

    return OR


def _CI_text(text):
    """
    * 95% Confident interval

      * if is beta coeff., there is text. elif OR, no text.
    """
    result = {}

    if not text or text in ('NR', 'NS'):  # nothing or NR or NS
        result['CI'] = None
        result['text'] = None

    else:
        re_CI_text = re.compile('\[(.+)\](.*)')
        texts = re_CI_text.findall(text)

        if not len(texts) == 1:  # only text
            result['CI'] = None
            re_CInone_text = re.compile('(.*)')
            texts = re_CInone_text.findall(text)
            assert len(text[0]) == 1, '{0} {1}'.format(text, texts)
            result['text']  = texts[0][0]

        else:
            assert len(texts[0]) == 2, '{0} {1}'.format(text, texts)  # [] & text

            #
            if ']' in texts[0][0]:  # [] ] somehow there is ] at end... like [0.006-0.01] ml/min/1.73 m2 decrease]
                retry_re_CI_text = re.compile('\[(.+)\](.*)\]')
                texts = retry_re_CI_text.findall(text)

            if texts[0][0] in ('NR', 'NS'):
                result['CI'] = None
            else:
                CIs = re.split('(, | - |- | -| |-|)', str(texts[0][0]))

                try:
                    if not len(CIs) == 3:
                        log.warn('{0} {1} {2}'.format(text, texts[0][0], CIs))
                        if CIs[0] == '' and CIs[1] == '-' and CIs[3] == '-':  # [-2.13040-19.39040]
                            result['CI'] = [(-1) * float(CIs[2]), float(CIs[4])]
                        else:
                            log.warn('{0} {1}'.format(text, texts))
                            time.sleep(2)
                    else:
                        result['CI'] = [float(CIs[0]), float(CIs[2])]

                except ValueError:
                    #
                    if CIs[2] == '.5.00':
                        CIs[2] = float(5.00)
                        result['CI'] = [float(CIs[0]), float(CIs[2])]
                    #
                    elif texts[0][0] == 'mg/dl decrease':
                        result['CI'] = None
                        result['text'] = 'mg/dl decrease'
                        return result

            if texts[0][1]:  # beta coeff.
                result['text']  = texts[0][1].lstrip()
            else:  # OR
                result['text'] = None

    return result


def _OR_or_beta(text):
    """
    * parse odds-ratio or beta-coeff.

      * in GWAS Catalog, OR>1 is asserted.
      * OR and beta are mixed. (to identify, we need to check 95% CI text)
    """

    if not text or text in ('NR', 'NS'):
        return None
    else:
        try:
            value = float(text)
        except ValueError:
            match = re.match('\d*\.\d+', text)
            if match:
                value = float(match.group())
            else:
                log.warn('OR_or_beta? {0}'.format(text))
                return None

        return value
        # if value >= 1.0:
        #     return value

        # else:
        #     print >>sys.stderr, 'OR_or_beta? {0}'.format(text)
        #     return text+'?'
