#!/usr/bin/env bash
# http://d.hatena.ne.jp/akuwano/20120503/1335994486

URL=$1

cat << 'EOF' > /tmp/curl_env.txt
url_effective\t\t: %{url_effective}\n
http_code\t\t: %{http_code}\n
http_connect\t\t: %{http_connect}\n
time_total\t\t: %{time_total}\n
time_namelookup\t\t: %{time_namelookup}\n
time_connect\t\t: %{time_connect}\n
time_appconnect\t\t: %{time_appconnect}\n
time_pretransfer\t\t: %{time_pretransfer}\n
time_redirect\t\t: %{time_redirect}\n
time_starttransfer\t\t: %{time_starttransfer}\n
size_download\t\t: %{size_download}\n
size_upload\t\t: %{size_upload}\n
size_header\t\t: %{size_header}\n
size_request\t\t: %{size_request}\n
speed_download\t\t: %{speed_download}\n
speed_upload\t\t: %{speed_upload}
EOF
curl -o /dev/null $URL -w @/tmp/curl_env.txt -s
