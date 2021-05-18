#!/usr/bin/env python3

""" crawler.py  - Web Crawler

-This script:
    - Takes in a Craigslist URL
    - Crawls the page
    - Prepares a MongoDB insert_one_document
    - Sends data to  MongoDB

-If no data matches or if MongoDB errors, S.F data will be returned
-This script requires the mongodb and websitepuller helper modules.
-This file is mean to be run outside of the Flask Appself.

"""

import os
import logging
import datetime

import mongodb
import websitepuller
from formatter import format_mongodocs

# "crawler.log"
logname = os.path.splitext(os.path.basename(__file__))[0] + ".log"

logging.basicConfig(
    filename=logname,
    level="INFO",
    format="%(levelname)s %(asctime)s %(module)s %(process)d  %(message)s",
)


def url_is_old_enough_to_crawl(old_enough):
    date_crawled = mongo_cli.lookup_crawled_date_given_craigs_url(one_craigs_url)
    difference = datetime.datetime.utcnow() - date_crawled
    if difference.days > old_enough:
        return True
    return False


if __name__ == "__main__":

    verbose = True
    howmany = 15
    timeout = 45
    old_enough = 3

    try:

        mongo_cli = mongodb.MongoCli()
        all_craigs_urls = mongo_cli.dump_all_craigs_urls_sorted_by_date()

        for one_craigs_url in all_craigs_urls:
            
            logging.info(f"...Checking Crawl Date for {one_craigs_url}")

            if url_is_old_enough_to_crawl(old_enough):
                logging.info(
                    f"Crawling and Indexing {one_craigs_url} - Crawl date more than {old_enough} days"
                )
            else:
                logging.info(
                    f"Passing on {one_craigs_url} - crawled within {old_enough} days"
                )
                continue

            logging.info(f"==== Connecting to {one_craigs_url} ====")
            craig_raw_posts = websitepuller.get_craigs_list_free_posts(one_craigs_url)
            logging.info(f"Picked up {len(craig_raw_posts)} items from Craigslist")

            for x in craig_raw_posts:
                logging.info(f"Picked up {x.get('href')} - {x.getText()}")

            logging.info(
                f"==== Connecting to Ebay - {timeout}s timeout, {howmany} items max to retrieve ===="
            )
            craig_posts_with_data, ebay_prices, ebay_links = websitepuller.get_ebay_data(
                craig_raw_posts, random="yes", howmany=howmany, timeout=timeout
            )
            logging.info(f"Ending Crawl of {one_craigs_url}")

            logging.info("==== Formatting Docs  ====")
            mongo_filter = {"craigs_url": one_craigs_url}
            
            mongo_doc = format_mongodocs(
                mongo_filter,
                craig_posts_with_data,
                ebay_prices,
                ebay_links,
                howmany=howmany,
            )

            logging.info("Sending to Mongo")
            mongo_cli.update_one_document(mongo_filter, mongo_doc)

    except (ValueError, NameError) as e:

        logging.exception(f"Data or other Issue: {e}")

    except Exception as e:
        logging.exception(f"Error: {e}")
