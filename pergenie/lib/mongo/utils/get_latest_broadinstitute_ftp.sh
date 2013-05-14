#!/bin/sh

# This script is from:
# http://gatkforums.broadinstitute.org/discussion/1215/how-can-i-access-the-gsa-public-ftp-server

RESOURCE="b37"

## Resource info: http://gatkforums.broadinstitute.org/discussion/1213/whats-in-the-resource-bundle-and-how-can-i-get-it


# Find latest version

list=$(curl -silent -l ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/)

highest=1

for e in $list
do
 if [ "$e" > "$highest" ]
 then highest=$e
fi
done

VERSION=$highest

echo "Downloading bundle version: "$VERSION
echo "Of the resource: "$RESOURCE

mkdir broad_bundle_${RESOURCE}_v${VERSION}
cd broad_bundle_${RESOURCE}_v${VERSION}

wget --no-directories --user=gsapubftp-anonymous -r ftp://ftp.broadinstitute.org/bundle/$VERSION/$RESOURCE/


for fn in *.gz
do
  md5ftp=$(cat $fn.md5 | awk '{print $1}')
  md5loc=$(md5sum $fn | awk '{print $1}')
  if [ $md5ftp == $md5loc ]
  then
    echo "md5 PASS"
  else
    echo "md5 FAIL"
    exit 1
  fi
  gzip -d $fn
  rm $fn.md5
  echo $fn" finished."
done
