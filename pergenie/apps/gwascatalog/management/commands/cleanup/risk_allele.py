def _risk_allele(data, thrs=None, snps=None):
    """Use strongest_snp_risk_allele in GWAS Catalog as risk allele, e.g., rs331615-T -> T

    Following checks will be done if available.

    * Consistency check based on allele frequency in SNPs database (dbSNP or 1000Genomes).

    """
    notes = ''
    gwascatalog_inconsistence_thrs = thrs or settings.GWASCATALOG_INCONSISTENCE_THRS

    # Parse `strongest_snp_risk_allele`
    if not data['strongest_snp_risk_allele']:
        return None, None, 'no strongest_snp_risk_allele'

    _risk_allele = re.compile('rs(\d+)\-(\S+)')
    try:
        rs, risk_allele = _risk_allele.findall(data['strongest_snp_risk_allele'])[0]
    except (ValueError, IndexError):
        log.warn('failed to parse "strongest_snp_risk_allele": {0}'.format(data))
        return None, None, 'failed to parse strongest_snp_risk_allele'

    if risk_allele == '?':
        return int(rs), risk_allele, 'risk_allele == ?'

    if not risk_allele in ('A', 'T', 'G', 'C'):
        log.warn('allele is not in (A,T,G,C): {0}'.format(data))
        return int(rs), None, 'not risk_allele in A, T, G, C'

    if not data['risk_allele_frequency']:
        log.warn('GWAS Catalog freq not found')
        return int(rs), risk_allele + '?', 'no risk_allele_frequency'

    # Strand checks (if database is available)
    snp_database = snps or snpdb or bq

    if not snp_database:
        return int(rs), risk_allele, 'no validation'

    else:
        RV = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
        population = data['population'][0] if data['population'] else 'European'  ## TODO: May be cause freq mismatch.
        rs = int(rs)
        # snp_summary = bq.get_snp_summary(rs)
        # ref = snp_summary['ancestral_alleles']
        allele_freqs, _ = snp_database.get_allele_freqs(rs, population=population)
        freqs = allele_freqs[population]

        # < Risk allele freq. X in Snpdb ? >
        freq = freqs.get(risk_allele)
        if freq:
            # < |freq_catalog(X) - freq_dbsnp(X))| <= thrs ? >
            diff = abs(freq['freq'] - data['risk_allele_frequency'])
            log.debug('diff: {diff}'.format(diff=diff))
            if diff <= gwascatalog_inconsistence_thrs:
                log.debug('ok')
                return int(rs), risk_allele, 'ok'
            else:
                log.warn('Inconsistence between GWAS Catalog and Snpdb')
                notes = 'Inconsistence between GWAS Catalog and Snpdb'
        else:
            log.warn('Snpdb freq for X not found')
            notes = 'Snpdb freq for X not found'

        # < Reversed risk allele freq. rev(X) in Snpdb ? >
        freq = freqs.get(RV[risk_allele])
        if not freq:
            log.warn(', but Snpdb freq for rev(X) not found')
            return int(rs), risk_allele + '?', notes + ', but Snpdb freq for rev(X) not found'

        # < |freq_catalog(rev(X)) - freq_dbsnp(rev(X)))| <= thrs ? >
        diff = abs(freq['freq'] - data['risk_allele_frequency'])
        log.debug('diff: {diff}'.format(diff=diff))
        if diff <= gwascatalog_inconsistence_thrs:
            log.info(', and solved with rev(X)')
            return int(rs), RV[risk_allele], notes + ', and solved with rev(X)'
        else:
            log.warn(', but not solved with rev(X)')
            return int(rs), risk_allele + '?', notes + ', but not solved with rev(X)'
