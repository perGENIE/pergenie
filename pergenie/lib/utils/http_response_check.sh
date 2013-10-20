#!/usr/bin/env bash

MAIL_TO=numakura@sb.ecei.tohoku.ac.jp
URL=http://pergenie.org
WGET_LOG=/tmp/pergenie_http_response.log
STAT=/tmp/pergenie_http_response.txt

# Check http response
wget -nv --spider --no-check-certificate $URL 1>$WGET_LOG 2>&1
is_live=`awk '/200 OK/ {print 0}' $WGET_LOG`

# Load previous status
if [ ! -d $STAT ]; then touch $STAT; fi
prev=`cat $STAT`

# Alert if status changes
echo [DEBUG] STAT: `cat $STAT`

if [ $is_live -eq 0 ]; then
    if [ $prev != "live" ]; then
        echo isup
        echo $WGET_LOG | mail -s "Alert: $URL is up" $MAIL
    fi
    echo "live" > $STAT
else
    if [ $prev != "die" ]; then
        echo isdown
        echo $WGET_LOG | mail -s "Alert: $URL is down" $MAIL
    fi
    echo "die" > $STAT
fi

echo [DEBUG] STAT: `cat $STAT`
echo [DEBUG] WGET_LOG: `cat $WGET_LOG`
