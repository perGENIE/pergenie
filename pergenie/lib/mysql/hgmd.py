import MySQLdb as mdb
from django.conf import settings

from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class HGMD(object):
    """doc
    """

    def __init__(self, host, username, password, dbname, port):
        self.host = host
        self.username = username
        self.password = password
        self.dbname = dbname
        self.port = port


    def _sql(self, sql, param):
        conf = dict(user=self.username, passwd=self.password, db=self.dbname, port=self.port)
        if self.host.endswith('sock'): conf['unix_socket'] = self.host
        else: conf['host'] = self.host
        con = mdb.connect(**conf)

        with con:
            cur = con.cursor(mdb.cursors.DictCursor)
            cur.execute(sql, param)
            rows = cur.fetchall()
            return rows

    def _allmut(self):
        rows = self._sql("select * from allmut limit 3", None)
        return rows
