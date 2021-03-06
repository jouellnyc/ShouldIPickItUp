#!/usr/bin/python3

import sys
sys.path.append("../lib/")

import mongodb

mg = mongodb.MongoCli()

def sa(how_to_sort):
    return sorted(
        [
            (x["craigs_url"], x["DateCrawled"])
                for x in
                    mg.dbh.find({ "DateCrawled": {"$exists": True} })
        ], key=how_to_sort,
    )

def by_date(stock):
    return stock[1]

try:
    for x in sa(how_to_sort=by_date):
        print(x)
except KeyError:
    pass

