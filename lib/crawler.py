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
import sys
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


def print_and_log(msg):
    print(msg) 
    logging.info(msg)
    
def connect_to_mongo():
    try:
        mongo_cli = mongodb.MongoCli()
    except Exception:
        msg='Cannot connect to Mongo'
        logging.exception(msg)
        raise
    else:
        return mongo_cli
           
            
    
if __name__ == "__main__":

    verbose = True
    check_crawl_date = True
    howmany = 15
    timeout = 45
   
    try:

        mongo_cli = connect_to_mongo()
        one_craigs_urls = mongo_cli.dump_all_craigs_urls_sorted_by_date()
        
        for one_craigs_url in one_craigs_urls:
    
            if check_crawl_date:
                
                print_and_log(f"...Checking Crawl Date for {one_craigs_url}")
                old_enough = 3
                date_crawled = mongo_cli.lookup_crawled_date_given_craigs_url(one_craigs_url)
                difference = datetime.datetime.utcnow() - date_crawled
                
                if difference.days >  old_enough:
                    print_and_log(f"Crawling and Indexing {one_craigs_url} - Crawl date more than {old_enough} days")
                    pass
                else:
                    print_and_log(f"Passing on {one_craigs_url} - crawled within {old_enough} days")
                    continue
                
            msg = f"==== Connecting to {one_craigs_url} ===="
            print_and_log(msg)
            craig_raw_posts = websitepuller.get_craigs_list_free_posts(one_craigs_url)
            logging.info(f"Picked up {len(craig_raw_posts)} items from Craigslist")
      
            for x in craig_raw_posts:
                logging.info(f"Picked up {x.get('href')} - {x.getText()}")
                            
            msg = f"==== Connecting to Ebay - {timeout}s timeout, {howmany} items max to retrieve ===="
            print_and_log(msg)    
            craig_posts_with_data, ebay_prices, ebay_links = websitepuller.get_ebay_data(
                craig_raw_posts, random="yes", howmany=howmany, timeout=timeout
            )
            logging.info(f"Ending Crawl of {one_craigs_url}")
    
    
            msg="==== Formatting Docs  ===="
            print_and_log(msg)        
            mongo_filter = {"craigs_url": one_craigs_url}
            mongo_doc = format_mongodocs(
                mongo_filter, craig_posts_with_data, ebay_prices, ebay_links, howmany=howmany
            )
         
    except (ValueError, NameError) as e:
            logging.exception(f"Data or other Issue: {e}")
    
    except Exception as e:
            logging.exception(f"Unhandled Crawl error: {e}")
    
    else:
        msg="Sending to Mongo"
        print_and_log(msg)
        try:
            mongo_cli = connect_to_mongo()
            if mongo_cli.dbh:
                if verbose:
                    print(mongo_filter, mongo_doc)
                mongo_cli.update_one_document(mongo_filter, mongo_doc)
            else:
                msg='Cannot connect to Mongo'
                logging.exception(msg)
                print(msg)
                sys.exit(1)
        except Exception as e:
            logging.exception(f"Unhandled Database related error: {e}")
        else:
            msg = "Sent to Mongo Success"
            print_and_log(msg)        

