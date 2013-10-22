#!/usr/bin/env bash

TO=numakura@sb.ecei.tohoku.ac.jp
URL=https://pergenie.org
LOG=/tmp/pergenie_http_response.html
STAT=/tmp/pergenie_http_response.stat

CURL=/usr/bin/curl
MAIL=/usr/bin/mail

# Check http response
current=`$CURL -s -w '%{http_code}\n' -o $LOG $URL`
echo [INFO] current: $current

# Load previous status
if [ ! -f $STAT ]; then echo "die" > $STAT; echo "[INFO] new"; fi
prev=`cat $STAT`

# Alert if status changes
echo [INFO] STAT: `cat $STAT`

if [ $current -eq 200 ]; then
    if [ $prev != "live" ]; then
        cat $LOG | mail -s "Alert: $URL is up" $TO
        echo "[INFO] is up. mail sent"
    fi
    echo "live" > $STAT
else
    if [ $prev != "die" ]; then
        cat $LOG | mail -s "Alert: $URL is down" $TO
        echo "[INFO] is down. mail sent"
    fi
    echo "die" > $STAT
fi

echo [INFO] STAT: `cat $STAT`
