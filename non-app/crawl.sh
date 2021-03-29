#!/bin/bash

STOCKS=all.txt
while read stk; do echo == $stk ==;
	date
	OUT=$(../lib/crawler.py $stk | tee -a "${0}"_main_crawl.log)
done < $STOCKS
