#!/bin/bash

CITIES="../data/craigs_links.txt"

while read line; do

    URL=$(echo $line | cut -d "=" -f2)
    echo == $URL ==
    date
    SLEEP=$((1 + RANDOM % 30))
    echo "Sleep $SLEEP"
    ../lib/crawler.py $URL index; sleep $SLEEP;

done < $CITIES
