# -*- coding: utf-8 -*-

import datetime

today = datetime.date.today()
today_date = datetime.datetime.strptime(str(today), '%Y-%m-%d')
today_str = str(today).replace('-', '_')

now_date = str(datetime.datetime.today()).split('.')[-2]
