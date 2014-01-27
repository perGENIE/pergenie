import MySQLdb as mdb


class MySQLClient(object):
    def __init__(self, host, username, password, dbname):
        self.host = host
        self.username = username
        self.password = password
        self.dbname = dbname

    def _sql(self, sql, param):
        conf = dict(user=self.username, passwd=self.password, db=self.dbname)
        if self.host.endswith('sock'): conf['unix_socket'] = self.host
        else: conf['host'] = self.host
        con = mdb.connect(**conf)

        with con:
            cur = con.cursor(mdb.cursors.DictCursor)
            cur.execute(sql, param)
            rows = cur.fetchall()
            return rows
